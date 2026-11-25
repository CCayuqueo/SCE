from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

Day = Annotated[int, Field(strict=True, ge=1, le=7)]
Block = Annotated[int, Field(strict=True, ge=1, le=10)]


class ScheduleCell(BaseModel):
    model_config = ConfigDict(extra="forbid")

    day: Day
    block: Block
    is_occupied: StrictBool


class ScheduleView(BaseModel):
    schedule_id: UUID | None = None
    status: Literal["missing", "draft", "confirmed"]
    version: int
    blocks: list[ScheduleCell] = Field(default_factory=list)


class ScheduleUpdate(BaseModel):
    expected_version: Annotated[int, Field(strict=True, ge=1)]
    blocks: Annotated[list[ScheduleCell], Field(min_length=70, max_length=70)]

    @model_validator(mode="after")
    def distinct_coordinates(self):
        if len({(cell.day, cell.block) for cell in self.blocks}) != 70:
            raise ValueError("Las 70 celdas deben tener coordenadas distintas")
        return self
