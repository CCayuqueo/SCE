from secrets import choice
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from app.core.errors import ApiError
from app.models import Room, RoomMember, Schedule, User
from app.rooms.dependencies import effective_role, find_membership, room_not_found
from app.rooms.schemas import (
    CODE_ALPHABET,
    CODE_LENGTH,
    MemberView,
    RoomCreate,
    RoomView,
)


def generate_code() -> str:
    return "".join(choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def create_room(
    db: DbSession, user_id: UUID, data: RoomCreate
) -> tuple[Room, RoomMember]:
    for _ in range(5):
        try:
            with db.begin_nested():
                room = Room(
                    owner_user_id=user_id,
                    code=generate_code(),
                    name=data.name,
                    description=data.description,
                )
                db.add(room)
                db.flush()
                member = RoomMember(room_id=room.id, user_id=user_id, role="admin")
                db.add(member)
                db.flush()
            return room, member
        except IntegrityError as error:
            if (
                getattr(getattr(error.orig, "diag", None), "constraint_name", None)
                != "uq_rooms_code"
            ):
                raise
    raise ApiError(
        503,
        "ROOM_CODE_UNAVAILABLE",
        "No se pudo generar un código. Vuelve a intentarlo.",
    )


def member_count(room_id):
    return (
        select(func.count())
        .select_from(RoomMember)
        .where(RoomMember.room_id == room_id)
    )


def join_room(
    db: DbSession, user_id: UUID, code: str, capacity: int
) -> tuple[Room, RoomMember, bool]:
    room = db.scalar(select(Room).where(Room.code == code).with_for_update())
    if room is None:
        raise room_not_found()
    existing = find_membership(db, room.id, user_id)
    if existing is not None:
        return room, existing, False
    if (db.scalar(member_count(room.id)) or 0) >= capacity:
        raise ApiError(409, "ROOM_FULL", "La sala alcanzó su límite de integrantes.")
    member = RoomMember(room_id=room.id, user_id=user_id, role="member")
    db.add(member)
    db.flush()
    return room, member, True


def to_room_view(room: Room, member: RoomMember, count: int, status) -> RoomView:
    role = effective_role(room, member)
    return RoomView(
        id=room.id,
        name=room.name,
        description=room.description,
        code=room.code if role != "member" else None,
        current_user_role=role,
        members_count=count,
        schedule_status=status or "missing",
    )


def room_view(db: DbSession, room: Room, member: RoomMember) -> RoomView:
    status = db.scalar(select(Schedule.status).where(Schedule.member_id == member.id))
    return to_room_view(room, member, db.scalar(member_count(room.id)) or 0, status)


def list_rooms(db: DbSession, user_id: UUID) -> list[RoomView]:
    count = member_count(Room.id).correlate(Room).scalar_subquery()
    result = db.execute(
        select(Room, RoomMember, count, Schedule.status)
        .join(RoomMember, RoomMember.room_id == Room.id)
        .outerjoin(Schedule, Schedule.member_id == RoomMember.id)
        .where(RoomMember.user_id == user_id)
        .order_by(Room.name, Room.id)
    )
    return [
        to_room_view(room, member, total, schedule)
        for room, member, total, schedule in result
    ]


def to_member_view(room: Room, member: RoomMember, name: str, status) -> MemberView:
    return MemberView(
        id=member.id,
        user_id=member.user_id,
        name=name,
        role=effective_role(room, member),
        schedule_status=status or "missing",
    )


def list_members(db: DbSession, room: Room) -> list[MemberView]:
    rows = db.execute(
        select(RoomMember, User.name, Schedule.status)
        .join(User, User.id == RoomMember.user_id)
        .outerjoin(Schedule, Schedule.member_id == RoomMember.id)
        .where(RoomMember.room_id == room.id)
        .order_by(User.name, RoomMember.id)
    )
    return [to_member_view(room, member, name, status) for member, name, status in rows]


def get_target(
    db: DbSession,
    room_id: UUID,
    *,
    member_id: UUID | None = None,
    user_id: UUID | None = None,
) -> RoomMember:
    if member_id is not None:
        target_filter = RoomMember.id == member_id
    else:
        target_filter = RoomMember.user_id == user_id
    member = db.scalar(
        select(RoomMember)
        .where(RoomMember.room_id == room_id, target_filter)
        .with_for_update()
    )
    if member is None:
        raise ApiError(
            404, "ROOM_MEMBER_NOT_FOUND", "Integrante no encontrado en la sala."
        )
    return member


def protect_owner(room: Room, member: RoomMember) -> None:
    if room.owner_user_id == member.user_id:
        raise ApiError(
            409,
            "OWNER_MEMBERSHIP_REQUIRED",
            "Primero debes transferir la propiedad o cerrar la sala.",
        )
