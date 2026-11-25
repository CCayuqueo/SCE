from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session as DbSession

from app.core.errors import ApiError
from app.models import Schedule, ScheduleBlock
from app.schedules.schemas import ScheduleCell, ScheduleView


def lookup(db: DbSession, member_id: UUID) -> Schedule | None:
    return db.scalar(select(Schedule).where(Schedule.member_id == member_id))


def version_conflict() -> ApiError:
    return ApiError(
        409,
        "SCHEDULE_VERSION_CONFLICT",
        "El horario cambió. Vuelve a cargarlo antes de continuar.",
    )


def check_version(schedule: Schedule | None, expected: int) -> None:
    if (schedule.version if schedule else 0) != expected:
        raise version_conflict()


def check_identity(schedule: Schedule | None, tag: str | None) -> None:
    if tag is not None and (
        schedule is None or tag != f'"{schedule.id}:{schedule.version}"'
    ):
        raise version_conflict()


def read_schedule(
    db: DbSession, member_id: UUID, *, confirmed_only: bool = False
) -> ScheduleView:
    rows = db.execute(
        select(Schedule, ScheduleBlock)
        .outerjoin(ScheduleBlock)
        .where(Schedule.member_id == member_id)
        .order_by(ScheduleBlock.day, ScheduleBlock.block)
    ).all()
    if not rows:
        return ScheduleView(status="missing", version=0)
    schedule = rows[0][0]
    if confirmed_only and schedule.status != "confirmed":
        return ScheduleView(status="draft", version=0)
    return ScheduleView(
        schedule_id=schedule.id,
        status=schedule.status,
        version=schedule.version,
        blocks=[
            ScheduleCell(
                day=block.day, block=block.block, is_occupied=block.is_occupied
            )
            for _, block in rows
            if block is not None
        ],
    )


def replace_blocks(
    db: DbSession,
    schedule: Schedule | None,
    member_id: UUID,
    cells: list[ScheduleCell],
    *,
    confirm: bool = False,
) -> ScheduleView:
    if schedule is None:
        schedule = Schedule(member_id=member_id, version=1)
        db.add(schedule)
    else:
        db.execute(
            delete(ScheduleBlock).where(ScheduleBlock.schedule_id == schedule.id)
        )
        schedule.version += 1
    schedule.status = "confirmed" if confirm else "draft"
    schedule.confirmed_at = datetime.now(UTC) if confirm else None
    db.flush()
    db.add_all(
        ScheduleBlock(schedule_id=schedule.id, **cell.model_dump()) for cell in cells
    )
    return ScheduleView(
        schedule_id=schedule.id,
        status=schedule.status,
        version=schedule.version,
        blocks=cells,
    )
