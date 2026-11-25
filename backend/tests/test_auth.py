from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session as DbSession

from app.auth.dependencies import SESSION_COOKIE
from app.auth.security import hash_token
from app.core.config import Settings
from app.core.database import make_engine
from app.main import app
from app.models import Session, User

API = "/api/v1/auth"
ORIGIN = {"Origin": "http://localhost:3000"}
PASSWORD = "una contraseña de ejemplo"
pytestmark = pytest.mark.integration


@pytest.fixture
def db():
    engine = make_engine(Settings())
    try:
        with DbSession(engine) as session:
            yield session
    finally:
        engine.dispose()


@pytest.fixture
def account(db):
    email = f"{uuid4()}@example.com"
    yield {"name": "Usuario de prueba", "email": email, "password": PASSWORD}
    db.rollback()
    db.execute(delete(User).where(User.email == email))
    db.commit()


def signup(client, account):
    response = client.post(f"{API}/register", json=account, headers=ORIGIN)
    assert response.status_code == 201
    return response


def test_signup_normalizes_email_hashes_credentials_and_rejects_duplicates(account, db):
    with TestClient(app) as client:
        response = signup(client, {**account, "email": f" {account['email'].upper()} "})
        assert response.json()["email"] == account["email"]
        assert "password" not in response.json()
        assert "HttpOnly" in response.headers["Set-Cookie"]
        assert "SameSite=lax" in response.headers["Set-Cookie"]
        assert response.headers["Cache-Control"] == "no-store"

        duplicate = client.post(f"{API}/register", json=account, headers=ORIGIN)
        assert duplicate.status_code == 409

        user = db.scalar(select(User).where(User.email == account["email"]))
        assert user.password_hash.startswith("$argon2id$")
        session = db.scalar(select(Session).where(Session.user_id == user.id))
        assert session.token_hash == hash_token(client.cookies[SESSION_COOKIE])
        assert session.csrf_token_hash == hash_token(
            client.get(f"{API}/me").json()["csrf_token"]
        )


def test_login_restores_session_and_logout_rejects_missing_or_cross_origin_csrf(
    account, db
):
    credentials = {"email": account["email"], "password": account["password"]}
    with TestClient(app) as client:
        assert client.get(f"{API}/me").status_code == 401
        signup(client, account)
        original_token = client.cookies[SESSION_COOKIE]
        client.cookies.clear()
        failed = client.post(
            f"{API}/login",
            json={**credentials, "password": "incorrecta"},
            headers=ORIGIN,
        )
        assert failed.status_code == 401
        assert "Set-Cookie" not in failed.headers
        user = db.scalar(select(User).where(User.email == account["email"]))
        assert (
            len(db.scalars(select(Session).where(Session.user_id == user.id)).all())
            == 1
        )

        login = client.post(
            f"{API}/login",
            json=credentials,
            headers={**ORIGIN, "Cookie": f"{SESSION_COOKIE}={original_token}"},
        )
        assert login.status_code == 200
        fresh_token = client.cookies[SESSION_COOKIE]
        assert fresh_token != original_token

    with TestClient(app) as reopened:
        session_header = {"Cookie": f"{SESSION_COOKIE}={fresh_token}"}
        state = reopened.get(f"{API}/me", headers=session_header)
        assert state.json() == login.json()
        csrf = {"X-CSRF-Token": state.json()["csrf_token"], **session_header}
        assert (
            reopened.post(
                f"{API}/logout", headers={**session_header, **ORIGIN}
            ).status_code
            == 403
        )
        assert (
            reopened.post(
                f"{API}/logout", headers={**csrf, "Origin": "http://other.test"}
            ).status_code
            == 403
        )
        assert (
            reopened.post(f"{API}/logout", headers={**csrf, **ORIGIN}).status_code
            == 204
        )

        for revoked_token in (fresh_token, original_token):
            headers = {"Cookie": f"{SESSION_COOKIE}={revoked_token}"}
            assert reopened.get(f"{API}/me", headers=headers).status_code == 401


@pytest.mark.parametrize("expired_field", ["expires_at", "last_activity_at"])
def test_expired_or_idle_session_is_rejected(expired_field, account, db):
    with TestClient(app) as client:
        signup(client, account)
        token = client.cookies[SESSION_COOKIE]
        session = db.scalar(
            select(Session).where(Session.token_hash == hash_token(token))
        )
        setattr(session, expired_field, datetime.now(UTC) - timedelta(days=2))
        db.commit()
        assert client.get(f"{API}/me").status_code == 401


def test_registration_rejects_untrusted_origins_non_json_and_invalid_input(account):
    with TestClient(app) as client:
        assert client.post(f"{API}/register", json=account).status_code == 403
        assert (
            client.post(f"{API}/register", data=account, headers=ORIGIN).status_code
            == 415
        )
        response = client.post(
            f"{API}/register", json={**account, "password": "secreto"}, headers=ORIGIN
        )
        assert response.status_code == 422
        assert "secreto" not in response.text


def test_cookie_secure_flag_in_production(account, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_ORIGIN", "https://src.example.com")
    with TestClient(app, base_url="https://src.example.com") as client:
        response = client.post(
            f"{API}/register",
            json=account,
            headers={"Origin": "https://src.example.com"},
        )
        assert response.status_code == 201
        assert "; Secure" in response.headers["Set-Cookie"]
        assert client.get(f"{API}/me").status_code == 200


def test_login_returns_429_on_repeated_attempts(monkeypatch):
    with TestClient(app) as client:
        monkeypatch.setattr(app.state.auth_rate_limit, "account_limit", 2)
        for attempt in range(3):
            response = client.post(
                f"{API}/login",
                json={"email": "missing@example.com", "password": "wrong"},
                headers=ORIGIN,
            )
            assert response.status_code == (401 if attempt < 2 else 429)
        assert response.headers["Retry-After"] == "300"
