from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.auth.dependencies import CurrentUser, Db
from app.core.errors import ApiError
from app.models import Room, RoomMember
from app.rooms.schemas import Role


def room_not_found() -> ApiError:
    return ApiError(404, "ROOM_NOT_FOUND", "Sala no encontrada.")


def forbidden() -> ApiError:
    return ApiError(
        403, "ROOM_ACCESS_DENIED", "No tienes permisos para esta operación."
    )


def effective_role(room: Room, member: RoomMember) -> Role:
    if room.owner_user_id == member.user_id:
        return "owner"
    return "admin" if member.role == "admin" else "member"


def find_membership(db: DbSession, room_id: UUID, user_id: UUID) -> RoomMember | None:
    return db.scalar(
        select(RoomMember).where(
            RoomMember.room_id == room_id, RoomMember.user_id == user_id
        )
    )


@dataclass
class RoomAccess:
    room: Room
    membership: RoomMember
    role: Role


def require_room_member(
    room_id: UUID, request: Request, auth: CurrentUser, db: Db
) -> RoomAccess:
    user_id = auth.user.id
    # No se bloquean salas ajenas. Se revalida tras adquirir el bloqueo de escritura.
    membership = find_membership(db, room_id, user_id)
    if membership is None:
        raise room_not_found()
    if request.method in {"GET", "HEAD"}:
        room = db.get(Room, room_id)
    else:
        room = db.get(Room, room_id, with_for_update=True)
        membership = db.scalar(
            select(RoomMember)
            .where(RoomMember.room_id == room_id, RoomMember.user_id == user_id)
            .execution_options(populate_existing=True)
        )
    if room is None or membership is None:
        raise room_not_found()
    return RoomAccess(room, membership, effective_role(room, membership))


RoomMemberAccess = Annotated[RoomAccess, Depends(require_room_member)]


def require_room_admin(access: RoomMemberAccess) -> RoomAccess:
    if access.role == "member":
        raise forbidden()
    return access


RoomAdminAccess = Annotated[RoomAccess, Depends(require_room_admin)]


def require_room_owner(access: RoomMemberAccess) -> RoomAccess:
    if access.role != "owner":
        raise forbidden()
    return access


RoomOwnerAccess = Annotated[RoomAccess, Depends(require_room_owner)]
