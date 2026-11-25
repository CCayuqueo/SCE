from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from app.auth.schemas import LoginInput, RegistrationInput
from app.auth.security import (
    csrf_token,
    dummy_hash,
    hash_password,
    hash_token,
    verify_password,
)
from app.core.config import Settings
from app.core.errors import ApiError
from app.models import Session, User


def start_session(
    db: DbSession, user: User, settings: Settings, previous_token: str | None
) -> str:
    if previous_token:
        db.execute(
            delete(Session).where(Session.token_hash == hash_token(previous_token))
        )
    token = token_urlsafe(32)
    db.add(
        Session(
            user_id=user.id,
            token_hash=hash_token(token),
            csrf_token_hash=hash_token(csrf_token(token)),
            expires_at=datetime.now(UTC) + timedelta(hours=settings.session_ttl_hours),
        )
    )
    return token


def register(
    db: DbSession,
    data: RegistrationInput,
    settings: Settings,
    previous_token: str | None,
) -> tuple[User, str]:
    user = User(
        name=data.name, email=data.email, password_hash=hash_password(data.password)
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError as error:
        if (
            getattr(getattr(error.orig, "diag", None), "constraint_name", None)
            == "uq_users_email"
        ):
            raise ApiError(
                409, "EMAIL_ALREADY_REGISTERED", "El correo ya está registrado."
            ) from error
        raise
    return user, start_session(db, user, settings, previous_token)


def login(
    db: DbSession, data: LoginInput, settings: Settings, previous_token: str | None
) -> tuple[User, str]:
    user = db.scalar(select(User).where(User.email == data.email))
    observed_hash = user.password_hash if user else dummy_hash
    valid = verify_password(data.password, observed_hash)
    if user is None or not valid:
        raise invalid_credentials()

    # Si cambió la contraseña durante la verificación, no se emite una sesión.
    user = db.get(User, user.id, populate_existing=True, with_for_update=True)
    if user is None or observed_hash != user.password_hash:
        raise invalid_credentials()
    return user, start_session(db, user, settings, previous_token)


def invalid_credentials() -> ApiError:
    return ApiError(401, "INVALID_CREDENTIALS", "Correo o contraseña incorrectos.")
