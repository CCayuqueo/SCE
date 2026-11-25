from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, model_validator
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

    @model_validator(mode="after")
    def secure_origin(self):
        if self.app_env == "production":
            origin = urlsplit(self.app_origin)
            if (
                origin.scheme != "https"
                or origin.hostname is None
                or origin.username is not None
                or origin.path not in {"", "/"}
                or origin.query
                or origin.fragment
            ):
                raise ValueError(
                    "APP_ORIGIN debe ser un origen HTTPS válido en producción"
                )
        return self
