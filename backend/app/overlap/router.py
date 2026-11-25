from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.auth.dependencies import Db
from app.overlap.schemas import CellDetails, OverlapView
from app.overlap.service import calculate_cell, calculate_overlap, room_snapshot
from app.rooms.dependencies import RoomAdminAccess
from app.rooms.router import no_store

router = APIRouter(
    prefix="/api/v1/rooms/{room_id}/overlap",
    tags=["overlap"],
    dependencies=[Depends(no_store)],
)


@router.get("")
def overlap(db: Db, access: RoomAdminAccess) -> OverlapView:
    members = room_snapshot(db, access.room.id, access.membership.user_id)
    db.commit()
    return calculate_overlap(access.room.id, members)


@router.get("/cells/{day}/{block}")
def cell_details(
    day: Annotated[int, Path(ge=1, le=7)],
    block: Annotated[int, Path(ge=1, le=10)],
    db: Db,
    access: RoomAdminAccess,
) -> CellDetails:
    members = room_snapshot(db, access.room.id, access.membership.user_id)
    db.commit()
    return calculate_cell(day, block, members)
