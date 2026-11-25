from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.auth.schemas import CurrentPassword, Email, Name, NewPassword


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Name | None = None
    email: Email | None = None
    current_password: CurrentPassword | None = None

    @model_validator(mode="after")
    def require_change(self):
        if self.name is None and self.email is None:
            raise ValueError("Indica un nombre o correo")
        return self


class PasswordUpdate(BaseModel):
    current_password: CurrentPassword
    new_password: NewPassword


class Candidate(BaseModel):
    id: UUID
    name: str
    role: Literal["admin", "member"]


class OwnedRoom(BaseModel):
    room_id: UUID
    name: str
    members_count: int
    suggested_new_owner_id: UUID | None
    requires_decision: bool
    candidates: list[Candidate]


class DeletionPreview(BaseModel):
    memberships_count: int
    schedules_count: int
    owned_rooms: list[OwnedRoom]


class TransferRoom(BaseModel):
    room_id: UUID
    action: Literal["transfer"]
    new_owner_id: UUID


class CloseRoom(BaseModel):
    room_id: UUID
    action: Literal["close"]
    new_owner_id: None = None


class DeletionInput(BaseModel):
    current_password: CurrentPassword
    confirmation: Literal["ELIMINAR"]
    room_actions: list[
        Annotated[TransferRoom | CloseRoom, Field(discriminator="action")]
    ]
