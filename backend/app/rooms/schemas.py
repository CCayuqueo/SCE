from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 12
Role = Literal["owner", "admin", "member"]
ScheduleStatus = Literal["missing", "draft", "confirmed"]
RoomName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]
Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]


class RoomCreate(BaseModel):
    name: RoomName
    description: Description | None = None


class RoomUpdate(BaseModel):
    name: RoomName | None = None
    description: Description | None = None

    @model_validator(mode="after")
    def check_changes(self):
        if not self.model_fields_set or (
            "name" in self.model_fields_set and self.name is None
        ):
            raise ValueError("Indica un nombre o una descripción para actualizar")
        return self


class RoomJoin(BaseModel):
    code: Annotated[str, Field(min_length=CODE_LENGTH, max_length=CODE_LENGTH)]

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip().upper()
            if any(char not in CODE_ALPHABET for char in value):
                raise ValueError("El código contiene caracteres no válidos")
        return value


class RoomView(BaseModel):
    id: UUID
    name: str
    description: str | None
    code: str | None = None
    current_user_role: Role
    members_count: int
    schedule_status: ScheduleStatus


class MemberView(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    role: Role
    schedule_status: ScheduleStatus


class MembersView(BaseModel):
    members: list[MemberView]


class RoleUpdate(BaseModel):
    role: Literal["admin", "member"]


class OwnershipTransfer(BaseModel):
    new_owner_id: UUID
