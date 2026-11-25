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
    max_upload_mb: Annotated[int, Field(gt=0, le=10)] = 5
    max_image_pixels: Annotated[int, Field(gt=0, le=12_000_000)] = 12_000_000
    image_processing_timeout_seconds: Annotated[int, Field(gt=0)] = 15
    image_processing_concurrency: Annotated[int, Field(gt=0)] = 2
