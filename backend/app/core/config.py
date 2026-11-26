from typing import Annotated, Literal
from urllib.parse import parse_qs, urlsplit

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(hide_input_in_errors=True)

    database_url: SecretStr
    supabase_url: str | None = None
    supabase_publishable_key: SecretStr | None = None
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
        if bool(self.supabase_url) != bool(self.supabase_publishable_key):
            raise ValueError("Configura SUPABASE_URL y SUPABASE_PUBLISHABLE_KEY juntas")
        if self.supabase_url:
            provider = urlsplit(self.supabase_url)
            local = provider.hostname in {"localhost", "127.0.0.1"}
            if (
                not provider.hostname
                or provider.username is not None
                or provider.path not in {"", "/"}
                or provider.query
                or provider.fragment
                or not (
                    provider.scheme == "https"
                    or (
                        provider.scheme == "http"
                        and local
                        and self.app_env in {"development", "test"}
                    )
                )
            ):
                raise ValueError("SUPABASE_URL debe ser el origen HTTPS del proyecto")
        if self.app_env in {"staging", "production"}:
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
                    "APP_ORIGIN debe ser un origen HTTPS válido en staging o producción"
                )
            if self.supabase_url:
                query = parse_qs(urlsplit(self.database_url.get_secret_value()).query)
                if query.get("sslmode") != ["verify-full"]:
                    raise ValueError(
                        "DATABASE_URL para Supabase debe usar sslmode=verify-full"
                    )
        return self
