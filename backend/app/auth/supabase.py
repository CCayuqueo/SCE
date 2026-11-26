from base64 import urlsafe_b64encode
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID

import httpx
from pydantic import BaseModel, SecretStr, ValidationError
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.schemas import RegistrationInput
from app.core.config import Settings
from app.core.errors import ApiError


class Identity(BaseModel):
    id: UUID
    user_metadata: dict[str, object] | None = None

    def profile_name(self) -> str:
        value = (self.user_metadata or {}).get("name")
        name = value.replace("\x00", "").strip() if isinstance(value, str) else ""
        return name[:100] if len(name) >= 2 else "Usuario SRC"


class PasswordGrant(BaseModel):
    access_token: SecretStr
    user: Identity

    def authorization(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token.get_secret_value()}"}


def verification_challenge() -> dict[str, str]:
    # La verificación de correo termina en /login. SRC emite su cookie al iniciar sesión.
    verifier = token_urlsafe(48)
    challenge = (
        urlsafe_b64encode(sha256(verifier.encode()).digest()).decode().rstrip("=")
    )
    return {"code_challenge": challenge, "code_challenge_method": "s256"}


def unavailable() -> ApiError:
    return ApiError(
        503, "AUTH_UNAVAILABLE", "El servicio de autenticación no está disponible."
    )


def validate_password_length(password: str) -> None:
    if len(password.encode()) > 72:
        raise ApiError(
            422, "INVALID_AUTH_INPUT", "La contraseña supera el máximo de 72 bytes."
        )


class SupabaseAuth:
    def __init__(self, settings: Settings) -> None:
        assert settings.supabase_url and settings.supabase_publishable_key
        self.client = httpx.Client(
            base_url=settings.supabase_url.rstrip("/") + "/auth/v1/",
            headers={"apikey": settings.supabase_publishable_key.get_secret_value()},
            timeout=5,
        )
        self.redirect = settings.app_origin.rstrip("/") + "/login"

    def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        try:
            response = self.client.request(method, path, **kwargs)
        except httpx.RequestError as error:
            raise unavailable() from error
        if response.status_code == 429:
            raise ApiError(
                429, "RATE_LIMITED", "Demasiados intentos. Prueba más tarde."
            )
        if response.status_code >= 500 or response.is_redirect:
            raise unavailable()
        return response

    def register(self, data: RegistrationInput) -> None:
        validate_password_length(data.password)
        response = self.request(
            "POST",
            "signup",
            params={"redirect_to": self.redirect},
            json={
                "email": data.email,
                "password": data.password,
                "data": {"name": data.name},
                **verification_challenge(),
            },
        )
        if response.is_success or provider_code(response) in {
            "email_exists",
            "user_already_exists",
        }:
            return
        raise self.update_error(response)

    def authenticate(self, email: str, password: str) -> PasswordGrant | None:
        if len(password.encode()) > 72:
            return None
        response = self.request(
            "POST",
            "token",
            params={"grant_type": "password"},
            json={"email": email, "password": password},
        )
        if not response.is_success:
            if provider_code(response) in {
                "invalid_credentials",
                "email_not_confirmed",
                "user_banned",
            }:
                return None
            raise unavailable()
        try:
            return PasswordGrant.model_validate_json(response.content)
        except ValidationError:
            raise unavailable() from None

    def update_email(self, grant: PasswordGrant, email: str) -> None:
        self.update(grant, {"email": email, **verification_challenge()})

    def update_password(self, grant: PasswordGrant, current: str, new: str) -> None:
        validate_password_length(new)
        self.update(grant, {"password": new, "current_password": current})

    def update(self, grant: PasswordGrant, payload: dict) -> None:
        response = self.request(
            "PUT",
            "user",
            params={"redirect_to": self.redirect},
            headers=grant.authorization(),
            json=payload,
        )
        if not response.is_success:
            raise self.update_error(response)

    def end_grant(self, grant: PasswordGrant) -> None:
        # El token del proveedor vive solo durante la solicitud. Su revocación es adicional.
        try:
            self.request(
                "POST",
                "logout",
                params={"scope": "local"},
                headers=grant.authorization(),
            )
        except ApiError:
            pass

    @staticmethod
    def update_error(response: httpx.Response) -> ApiError:
        code = provider_code(response)
        if code in {"email_exists", "user_already_exists"}:
            return ApiError(
                409, "EMAIL_ALREADY_REGISTERED", "El correo ya está registrado."
            )
        if code in {"weak_password", "same_password", "email_address_invalid"}:
            return ApiError(
                422,
                "INVALID_AUTH_INPUT",
                "Revisa el correo o elige una contraseña diferente.",
            )
        if code in {
            "invalid_credentials",
            "reauthentication_needed",
            "reauthentication_not_valid",
            "current_password_required",
            "current_password_mismatch",
        }:
            return ApiError(
                403, "REAUTHENTICATION_REQUIRED", "Verifica tu contraseña actual."
            )
        return unavailable()


def provider_code(response: httpx.Response) -> str | None:
    try:
        result = response.json()
    except ValueError:
        return None
    code = result.get("error_code") if isinstance(result, dict) else None
    return code if isinstance(code, str) else None


def identity_id(db: Session, email: str) -> UUID | None:
    return db.scalar(text("SELECT src_auth.identity_id(:email)"), {"email": email})


def identity_email(db: Session, user_id: UUID) -> str | None:
    return db.scalar(text("SELECT src_auth.identity_email(:id)"), {"id": user_id})


def delete_identity(db: Session, user_id: UUID) -> None:
    deleted = db.scalar(text("SELECT src_auth.delete_identity(:id)"), {"id": user_id})
    if not deleted:
        raise ApiError(
            409,
            "DELETION_CONFLICT",
            "La identidad de la cuenta cambió. Vuelve a iniciar sesión.",
        )
