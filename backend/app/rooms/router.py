from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.exc import DBAPIError

from app.auth.dependencies import (
    AppSettings,
    CsrfUser,
    CurrentUser,
    Db,
    limit,
    require_csrf,
    require_json,
)
from app.core.errors import ApiError
from app.rooms.dependencies import (
    RoomAdminAccess,
    RoomMemberAccess,
    RoomOwnerAccess,
    forbidden,
)
from app.rooms.schemas import (
    MembersView,
    OwnershipTransfer,
    RoleUpdate,
    RoomCreate,
    RoomJoin,
    RoomUpdate,
    RoomView,
)
from app.rooms.service import (
    create_room,
    get_target,
    join_room,
    list_members,
    list_rooms,
    protect_owner,
    room_view,
)


def no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


router = APIRouter(
    prefix="/api/v1/rooms", tags=["rooms"], dependencies=[Depends(no_store)]
)
write = [Depends(require_csrf)]
json_write = [*write, Depends(require_json)]


def commit(db: Db) -> None:
    try:
        db.commit()
    except DBAPIError as error:
        if getattr(error.orig, "sqlstate", None) in {"23503", "40001", "40P01"}:
            raise ApiError(
                409, "ROOM_CONFLICT", "La sala cambió. Vuelve a cargarla."
            ) from error
        raise


@router.get("")
def read_rooms(db: Db, auth: CurrentUser) -> list[RoomView]:
    rooms = list_rooms(db, auth.user.id)
    db.commit()
    return rooms


@router.post("", status_code=201, dependencies=[Depends(require_json)])
def add_room(data: RoomCreate, db: Db, auth: CsrfUser) -> RoomView:
    room, member = create_room(db, auth.user.id, data)
    commit(db)
    return room_view(db, room, member)


@router.post(
    "/join",
    status_code=201,
    responses={200: {"model": RoomView}},
    dependencies=[Depends(require_json)],
)
def enter_room(
    data: RoomJoin,
    request: Request,
    response: Response,
    db: Db,
    auth: CsrfUser,
    settings: AppSettings,
) -> RoomView:
    limit(request, "join-room", auth.email)
    room, member, created = join_room(
        db, auth.user.id, data.code, settings.max_room_members
    )
    result = room_view(db, room, member)
    commit(db)
    if not created:
        response.status_code = 200
    return result


@router.get("/{room_id}")
def read_room(db: Db, access: RoomMemberAccess) -> RoomView:
    result = room_view(db, access.room, access.membership)
    db.commit()
    return result


@router.patch("/{room_id}", dependencies=json_write)
def edit_room(data: RoomUpdate, db: Db, access: RoomAdminAccess) -> RoomView:
    if data.name is not None:
        access.room.name = data.name
    if "description" in data.model_fields_set:
        access.room.description = data.description
    result = room_view(db, access.room, access.membership)
    commit(db)
    return result


@router.get("/{room_id}/members")
def read_members(db: Db, access: RoomAdminAccess) -> MembersView:
    out = MembersView(members=list_members(db, access.room))
    db.commit()
    return out


@router.patch(
    "/{room_id}/members/{member_id}/role", status_code=204, dependencies=json_write
)
def change_role(
    member_id: UUID, data: RoleUpdate, db: Db, access: RoomAdminAccess
) -> None:
    target = get_target(db, access.room.id, member_id=member_id)
    protect_owner(access.room, target)
    if data.role == "member" and access.role != "owner":
        raise forbidden()
    target.role = data.role
    commit(db)


@router.post("/{room_id}/transfer-ownership", dependencies=json_write)
def transfer_room(data: OwnershipTransfer, db: Db, access: RoomOwnerAccess) -> RoomView:
    target = get_target(db, access.room.id, user_id=data.new_owner_id)
    protect_owner(access.room, target)
    target.role = "admin"
    access.room.owner_user_id = target.user_id
    commit(db)
    return room_view(db, access.room, access.membership)


@router.delete("/{room_id}/members/{member_id}", status_code=204, dependencies=write)
def remove_member(member_id: UUID, db: Db, access: RoomOwnerAccess) -> None:
    target = get_target(db, access.room.id, member_id=member_id)
    protect_owner(access.room, target)
    db.delete(target)
    commit(db)


@router.delete("/{room_id}/membership/me", status_code=204, dependencies=write)
def leave_room(db: Db, access: RoomMemberAccess) -> None:
    protect_owner(access.room, access.membership)
    db.delete(access.membership)
    commit(db)


@router.delete("/{room_id}", status_code=204, dependencies=write)
def close_room(db: Db, access: RoomOwnerAccess) -> None:
    db.delete(access.room)
    commit(db)
