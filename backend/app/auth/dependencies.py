from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hmac import compare_digest
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.auth.security import hash_token
from app.auth.supabase import SupabaseAuth, identity_email
from app.core.config import Settings
from app.core.errors import ApiError
from app.models import Session, User

SESSION_COOKIE = "src_session"


def get_db(request: Request) -> Iterator[DbSession]:
    with DbSession(request.app.state.db, expire_on_commit=False) as db:
        yield db


Db = Annotated[DbSession, Depends(get_db)]


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


AppSettings = Annotated[Settings, Depends(get_settings)]


def get_provider(request: Request) -> SupabaseAuth | None:
    return request.app.state.supabase_auth


AuthProvider = Annotated[SupabaseAuth | None, Depends(get_provider)]


def require_origin(request: Request, settings: AppSettings) -> None:
    if request.headers.get("origin") != settings.app_origin.rstrip("/"):
        raise ApiError(403, "INVALID_ORIGIN", "Origen de solicitud no permitido.")


def require_json(request: Request) -> None:
    content_type = (
        request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    )
    if content_type != "application/json":
        raise ApiError(415, "UNSUPPORTED_MEDIA_TYPE", "Usa application/json.")


@dataclass
class AuthContext:
    user: User
    session: Session
    token: str
    email: str


def get_current_user(request: Request, db: Db, settings: AppSettings) -> AuthContext:
    token = request.cookies.get(SESSION_COOKIE)
    unauthorized = ApiError(401, "AUTH_REQUIRED", "Inicia sesión para continuar.")
    if not token or len(token) != 43 or not token.isascii():
        raise unauthorized

    token_hash = hash_token(token)
    user_id = db.scalar(select(Session.user_id).where(Session.token_hash == token_hash))
    user = (
        db.get(User, user_id, with_for_update={"key_share": True}) if user_id else None
    )
    if user is None or (user.password_hash is None) != bool(settings.supabase_url):
        raise unauthorized
    session = db.scalar(select(Session).where(Session.token_hash == token_hash))
    now = datetime.now(UTC)
    if (
        session is None
        or session.expires_at <= now
        or session.last_activity_at
        <= now - timedelta(minutes=settings.session_idle_minutes)
    ):
        raise unauthorized
    email = identity_email(db, user.id) if settings.supabase_url else user.email
    if email is None:
        raise unauthorized
    session.last_activity_at = now
    return AuthContext(user, session, token, email)


CurrentUser = Annotated[AuthContext, Depends(get_current_user)]


def require_csrf(
    request: Request, auth: CurrentUser, _: Annotated[None, Depends(require_origin)]
) -> AuthContext:
    token = request.headers.get("x-csrf-token", "")
    if len(token) != 64 or not compare_digest(
        hash_token(token), auth.session.csrf_token_hash
    ):
        raise ApiError(403, "INVALID_CSRF", "Validación de seguridad fallida.")
    return auth


CsrfUser = Annotated[AuthContext, Depends(require_csrf)]


def limit(request: Request, operation: str, email: str) -> None:
    ip = request.client.host if request.client else "unknown"
    request.app.state.auth_rate_limit.check(operation, email, ip)
