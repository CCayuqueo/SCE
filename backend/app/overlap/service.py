from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import aliased

from app.models import RoomMember, Schedule, ScheduleBlock, User
from app.overlap.schemas import CellDetails, MemberSummary, OverlapCell, OverlapView
from app.rooms.dependencies import forbidden

WEEK = tuple((day, block) for day in range(1, 8) for block in range(1, 11))
Coordinate = tuple[int, int]


@dataclass
class MemberSchedule:
    id: UUID
    name: str
    grid: dict[Coordinate, bool] = field(default_factory=dict)

    @property
    def confirmed(self) -> bool:
        return len(self.grid) == len(WEEK)


def room_snapshot(db: DbSession, room_id: UUID, actor_id: UUID) -> list[MemberSchedule]:
    administrator = aliased(RoomMember)
    permitted = (
        select(administrator.id)
        .where(
            administrator.room_id == room_id,
            administrator.user_id == actor_id,
            administrator.role == "admin",
        )
        .exists()
    )
    rows = db.execute(
        select(
            RoomMember.id,
            User.name,
            ScheduleBlock.day,
            ScheduleBlock.block,
            ScheduleBlock.is_occupied,
        )
        .join(User, User.id == RoomMember.user_id)
        .outerjoin(
            Schedule,
            and_(Schedule.member_id == RoomMember.id, Schedule.status == "confirmed"),
        )
        .outerjoin(ScheduleBlock, ScheduleBlock.schedule_id == Schedule.id)
        .where(RoomMember.room_id == room_id, permitted)
        .order_by(User.name, RoomMember.id)
    )
    members: dict[UUID, MemberSchedule] = {}
    for member_id, name, day, block, occupied in rows:
        member = members.get(member_id)
        if member is None:
            member = members[member_id] = MemberSchedule(member_id, name)
        if day is not None:
            member.grid[day, block] = occupied
    if not members:
        raise forbidden()
    return list(members.values())


def calculate_overlap(room_id: UUID, members: list[MemberSchedule]) -> OverlapView:
    total = len(members)
    confirmed = [member for member in members if member.confirmed]
    pending = total - len(confirmed)
    weights = dict.fromkeys(WEEK, 0)
    for member in confirmed:
        for coordinate, occupied in member.grid.items():
            if occupied:
                weights[coordinate] += 1

    return OverlapView(
        room_id=room_id,
        total_members=total,
        confirmed_members=len(confirmed),
        pending_members=pending,
        min_weight=min(weights.values()),
        max_weight=max(weights.values()),
        coverage=len(confirmed) / total if total else 0,
        cells=[
            OverlapCell(
                day=day,
                block=block,
                weight=weight,
                available_count=len(confirmed) - weight,
                pending_count=pending,
                intensity=weight / total if total else 0,
                everyone_available=bool(total and not pending and not weight),
            )
            for (day, block), weight in weights.items()
        ],
    )


def calculate_cell(day: int, block: int, members: list[MemberSchedule]) -> CellDetails:
    occupied, available, pending = [], [], []
    for member in members:
        summary = MemberSummary(id=member.id, name=member.name)
        if not member.confirmed:
            pending.append(summary)
        elif member.grid[day, block]:
            occupied.append(summary)
        else:
            available.append(summary)
    return CellDetails(
        day=day,
        block=block,
        weight=len(occupied),
        total_members=len(members),
        available_count=len(available),
        pending_count=len(pending),
        occupied_members=occupied,
        available_members=available,
        pending_members=pending,
    )
