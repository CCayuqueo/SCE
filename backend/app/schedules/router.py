from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, Response, UploadFile
from sqlalchemy import select

from app.auth.dependencies import (
    AppSettings,
    CsrfUser,
    Db,
    get_current_user,
    limit,
    require_csrf,
    require_json,
)
from app.core.errors import ApiError
from app.models import RoomMember
from app.rooms.dependencies import (
    RoomAdminAccess,
    RoomMemberAccess,
    require_room_member,
)
from app.rooms.router import commit, no_store
from app.schedules.schemas import ScheduleUpdate, ScheduleView
from app.schedules.service import (
    check_identity,
    check_version,
    lookup,
    read_schedule,
    replace_blocks,
    version_conflict,
)

router = APIRouter(
    prefix="/api/v1/rooms/{room_id}",
    tags=["schedules"],
    dependencies=[Depends(no_store)],
)
own = "/schedules/me"


@router.get(own)
def get_own(
    response: Response, db: Db, access: RoomMemberAccess, settings: AppSettings
) -> ScheduleView:
    result = read_schedule(db, access.membership.id)
    db.commit()
    response.headers["X-Max-Upload-Bytes"] = str(settings.max_upload_mb * 1024**2)
    return result


@router.post(
    own + "/upload",
    responses={201: {"model": ScheduleView}},
    form_limits={"max_files": 1, "max_fields": 1, "max_part_size": 1024},
    dependencies=[Depends(require_csrf)],
)
def upload(
    request: Request,
    response: Response,
    db: Db,
    access: RoomMemberAccess,
    auth: CsrfUser,
    settings: AppSettings,
    file: Annotated[UploadFile, File()],
    expected_version: Annotated[int, Form(ge=0)],
) -> ScheduleView:
    limit(request, "schedule-upload", auth.user.email)
    member_id = access.membership.id
    room_id = access.room.id
    previous = lookup(db, member_id)
    check_version(previous, expected_version)
    check_identity(previous, request.headers.get("if-match"))
    previous_id = previous.id if previous else None
    # La extracción es externa y puede tardar. No debe mantener bloqueos ni transacciones.
    db.commit()

    max_size = settings.max_upload_mb * 1024 * 1024
    data = file.file.read(max_size + 1)
    if len(data) > max_size:
        raise ApiError(413, "IMAGE_TOO_LARGE", "La captura excede el límite de tamaño.")
    cells = request.app.state.image_processor.process(data)

    db.expire_all()
    actor = get_current_user(request, db, settings)
    refreshed = require_room_member(room_id, request, actor, db)
    if refreshed.membership.id != member_id:
        raise version_conflict()
    current = lookup(db, member_id)
    check_version(current, expected_version)
    if (current.id if current else None) != previous_id:
        raise version_conflict()

    result = replace_blocks(db, current, member_id, cells)
    commit(db)
    if previous_id is None:
        response.status_code = 201
    return result


@router.put(own, dependencies=[Depends(require_csrf), Depends(require_json)])
def confirm(
    data: ScheduleUpdate, request: Request, db: Db, access: RoomMemberAccess
) -> ScheduleView:
    schedule = lookup(db, access.membership.id)
    check_version(schedule, data.expected_version)
    check_identity(schedule, request.headers.get("if-match"))
    result = replace_blocks(
        db,
        schedule,
        access.membership.id,
        sorted(data.blocks, key=lambda cell: (cell.day, cell.block)),
        confirm=True,
    )
    commit(db)
    return result


@router.delete(own, status_code=204, dependencies=[Depends(require_csrf)])
def delete_own(request: Request, db: Db, access: RoomMemberAccess) -> None:
    schedule = lookup(db, access.membership.id)
    check_identity(schedule, request.headers.get("if-match"))
    if schedule is not None:
        db.delete(schedule)
    commit(db)


@router.get("/members/{member_id}/schedule")
def get_confirmed(member_id: UUID, db: Db, access: RoomAdminAccess) -> ScheduleView:
    target = db.scalar(
        select(RoomMember.id).where(
            RoomMember.id == member_id, RoomMember.room_id == access.room.id
        )
    )
    if target is None:
        raise ApiError(
            404, "ROOM_MEMBER_NOT_FOUND", "Integrante no encontrado en la sala."
        )
    result = read_schedule(db, target, confirmed_only=True)
    db.commit()
    return result
