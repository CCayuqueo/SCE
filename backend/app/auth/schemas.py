import re
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_LOCAL = re.compile(
    r"[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*"
)
DOMAIN_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")
NewPassword = Annotated[str, Field(min_length=15, max_length=128)]
CurrentPassword = Annotated[str, Field(min_length=1, max_length=128)]


class LoginInput(BaseModel):
    email: str
    password: CurrentPassword

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        local, _, domain = value.partition("@")
        labels = domain.split(".")
        if (
            len(value) > 254
            or len(local) > 64
            or not EMAIL_LOCAL.fullmatch(local)
            or len(labels) < 2
            or not all(DOMAIN_LABEL.fullmatch(label) for label in labels)
        ):
            raise ValueError("Introduce un correo válido")
        return value


class RegistrationInput(LoginInput):
    name: Annotated[str, Field(min_length=2, max_length=100)]
    password: NewPassword

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class UserView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str


class SessionView(BaseModel):
    user: UserView
    csrf_token: str
