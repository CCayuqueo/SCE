from uuid import UUID

from pydantic import BaseModel

from app.schedules.schemas import Block, Day


class CellCount(BaseModel):
    day: Day
    block: Block
    weight: int
    available_count: int
    pending_count: int


class OverlapCell(CellCount):
    intensity: float
    everyone_available: bool


class OverlapView(BaseModel):
    room_id: UUID
    total_members: int
    confirmed_members: int
    pending_members: int
    min_weight: int
    max_weight: int
    coverage: float
    cells: list[OverlapCell]


class MemberSummary(BaseModel):
    id: UUID
    name: str


class CellDetails(CellCount):
    total_members: int
    occupied_members: list[MemberSummary]
    available_members: list[MemberSummary]
    pending_members: list[MemberSummary]
