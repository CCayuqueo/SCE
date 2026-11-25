from hashlib import sha256
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from app.auth.dependencies import AuthContext
from app.auth.security import hash_password, verify_password
from app.core.errors import ApiError
from app.models import Room, RoomMember, Schedule, Session, User
from app.users.schemas import (
    Candidate,
    DeletionInput,
    DeletionPreview,
    OwnedRoom,
    ProfileUpdate,
)


def reauthenticate(user: User, password: str | None) -> None:
    if password is None or not verify_password(password, user.password_hash):
        raise ApiError(
            403,
            "REAUTHENTICATION_REQUIRED",
            "La contraseña actual es obligatoria y debe ser correcta.",
        )


def update_profile(db: DbSession, user: User, data: ProfileUpdate) -> None:
    if data.email is not None and data.email != user.email:
        reauthenticate(user, data.current_password)
        user.email = data.email
    if data.name is not None:
        user.name = data.name
    try:
        db.flush()
    except IntegrityError as error:
        if (
            getattr(getattr(error.orig, "diag", None), "constraint_name", None)
            == "uq_users_email"
        ):
            raise ApiError(
                409, "EMAIL_ALREADY_REGISTERED", "El correo ya está registrado."
            ) from error
        raise


def change_password(db: DbSession, auth: AuthContext, current: str, new: str) -> None:
    reauthenticate(auth.user, current)
    auth.user.password_hash = hash_password(new)
    db.execute(
        delete(Session).where(
            Session.user_id == auth.user.id, Session.id != auth.session.id
        )
    )


def owned_rooms(db: DbSession, user: User, *, lock: bool = False) -> list[Room]:
    query = select(Room).where(Room.owner_user_id == user.id).order_by(Room.id)
    return list(db.scalars(query.with_for_update() if lock else query))


def describe_deletion(
    db: DbSession, user: User, rooms: list[Room], *, lock: bool = False
) -> tuple[DeletionPreview, dict[UUID, dict[UUID, RoomMember]]]:
    eligible: dict[UUID, dict[UUID, RoomMember]] = {room.id: {} for room in rooms}
    candidates: dict[UUID, list[Candidate]] = {room.id: [] for room in rooms}
    if rooms:
        query = (
            select(RoomMember, User.name)
            .join(User, RoomMember.user_id == User.id)
            .where(RoomMember.room_id.in_(eligible), RoomMember.user_id != user.id)
            .order_by(
                RoomMember.room_id,
                (RoomMember.role == "admin").desc(),
                RoomMember.joined_at,
                RoomMember.id,
            )
        )
        if lock:
            query = query.with_for_update(of=RoomMember)
        for membership, name in db.execute(query):
            eligible[membership.room_id][membership.user_id] = membership
            candidates[membership.room_id].append(
                Candidate(id=membership.user_id, name=name, role=membership.role)
            )

    memberships = db.scalar(
        select(func.count())
        .select_from(RoomMember)
        .where(RoomMember.user_id == user.id)
    )
    schedules = db.scalar(
        select(func.count())
        .select_from(Schedule)
        .join(RoomMember)
        .where(RoomMember.user_id == user.id)
    )
    return DeletionPreview(
        memberships_count=memberships,
        schedules_count=schedules,
        owned_rooms=[
            OwnedRoom(
                room_id=room.id,
                name=room.name,
                members_count=len(candidates[room.id]) + 1,
                suggested_new_owner_id=candidates[room.id][0].id
                if candidates[room.id]
                else None,
                requires_decision=bool(candidates[room.id]),
                candidates=candidates[room.id],
            )
            for room in rooms
        ],
    ), eligible


def preview_version(preview: DeletionPreview) -> str:
    return '"' + sha256(preview.model_dump_json().encode()).hexdigest() + '"'


def deletion_conflict() -> ApiError:
    return ApiError(
        409,
        "DELETION_CONFLICT",
        "Revisa nuevamente las salas y confirma las decisiones antes de eliminar la cuenta.",
    )


def delete_account(
    db: DbSession, user: User, data: DeletionInput, expected_version: str | None
) -> None:
    reauthenticate(user, data.current_password)
    rooms = owned_rooms(db, user, lock=True)
    preview, eligible = describe_deletion(db, user, rooms, lock=True)
    if expected_version != preview_version(preview):
        raise deletion_conflict()

    actions = {action.room_id: action for action in data.room_actions}
    needed = {room.room_id for room in preview.owned_rooms if room.requires_decision}
    if (
        len(actions) != len(data.room_actions)
        or not needed <= actions.keys() <= eligible.keys()
    ):
        raise deletion_conflict()

    for room in rooms:
        action = actions.get(room.id)
        if action is None or action.action == "close":
            db.delete(room)
        else:
            replacement = eligible[room.id].get(action.new_owner_id)
            if replacement is None:
                raise deletion_conflict()
            replacement.role = "admin"
            room.owner_user_id = replacement.user_id
    db.flush()
    db.delete(user)
