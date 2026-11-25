from typing import Annotated, Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: SecretStr
    app_env: Literal["development", "test", "staging", "production"] = "development"
    app_origin: str = "http://localhost:3000"
    session_ttl_hours: Annotated[int, Field(gt=0)] = 24
    session_idle_minutes: Annotated[int, Field(gt=0)] = 60
    max_room_members: Annotated[int, Field(gt=0)] = 100
