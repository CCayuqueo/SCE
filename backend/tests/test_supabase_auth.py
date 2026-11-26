import json
import os
from contextlib import closing
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.auth.supabase import SupabaseAuth
from app.main import app

pytestmark = pytest.mark.integration
ROOT = "/api/v1"
ORIGIN = {"Origin": "https://src.example.com"}
EMAIL = "persona@example.com"
PASSWORD = "contraseña inicial de prueba"


@pytest.fixture
def managed_db(monkeypatch):
    url = make_url(os.environ["DATABASE_URL"])
    server = create_engine(url, isolation_level="AUTOCOMMIT")
    database = f"src_auth_test_{uuid4().hex}"
    with server.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{database}"'))
    temporary_url = url.set(database=database)
    monkeypatch.setenv(
        "DATABASE_URL", temporary_url.render_as_string(hide_password=False)
    )
    monkeypatch.setenv("APP_ORIGIN", ORIGIN["Origin"])
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("SUPABASE_URL", "https://staging-example.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "testing-publishable-key")
    engine = create_engine(temporary_url)
    try:
        command.upgrade(Config("alembic.ini"), "head")
        with engine.begin() as connection:
            for role in ("anon", "authenticated", "service_role"):
                connection.execute(
                    text(
                        f"DO $$ BEGIN CREATE ROLE {role}; EXCEPTION WHEN duplicate_object THEN NULL; END $$"
                    )
                )
            connection.execute(text("CREATE SCHEMA auth"))
            connection.execute(
                text("""
                CREATE TABLE auth.users (
                    id uuid PRIMARY KEY, email text UNIQUE, email_confirmed_at timestamptz,
                    deleted_at timestamptz, banned_until timestamptz
                )
            """)
            )
            connection.execute(
                text(
                    "CREATE TABLE auth.sessions (user_id uuid REFERENCES auth.users ON DELETE CASCADE)"
                )
            )
        script = Path("../infrastructure/supabase/permissions.sql").read_text()
        with engine.connect() as connection:
            connection.connection.driver_connection.execute(script, prepare=False)
        runtime_url = temporary_url.update_query_dict({"options": "-c role=src_app"})
        monkeypatch.setenv(
            "DATABASE_URL", runtime_url.render_as_string(hide_password=False)
        )
        yield engine
    finally:
        engine.dispose()
        with server.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{database}" WITH (FORCE)'))
        server.dispose()


def test_managed_confirmation_sessions_and_atomic_deletion(monkeypatch, managed_db):
    identity = uuid4()
    successor = uuid4()
    password = PASSWORD
    confirmed = False
    email_change_requested = False

    def auth_server(request: httpx.Request) -> httpx.Response:
        nonlocal email_change_requested, password
        body = json.loads(request.content) if request.content else {}
        assert request.headers["apikey"] == "testing-publishable-key"
        if request.url.path.endswith("/signup"):
            assert request.url.params["redirect_to"] == "https://src.example.com/login"
            assert body["data"] == {"name": "Persona"}
            assert len(body["code_challenge"]) == 43
            return httpx.Response(200, json={"user": {"id": str(identity)}})
        if request.url.path.endswith("/token"):
            if not confirmed or body["password"] != password:
                return httpx.Response(400, json={"error_code": "invalid_credentials"})
            return httpx.Response(
                200,
                json={
                    "access_token": "ephemeral",
                    "user": {
                        "id": str(identity),
                        "user_metadata": {"name": "Persona", "role": "admin"},
                    },
                },
            )
        assert request.headers["Authorization"] == "Bearer ephemeral"
        if request.url.path.endswith("/user"):
            if "email" in body:
                assert body["email"] == "nuevo@example.com"
                assert len(body["code_challenge"]) == 43
                email_change_requested = True
                return httpx.Response(200, json={})
            assert body["current_password"] == password
            password = body["password"]
            return httpx.Response(200, json={})
        assert (
            request.url.path.endswith("/logout")
            and request.url.params["scope"] == "local"
        )
        return httpx.Response(204)

    original_init = SupabaseAuth.__init__

    def setup_provider(self, settings):
        original_init(self, settings)
        previous = self.client
        self.client = httpx.Client(
            base_url=previous.base_url,
            headers=previous.headers,
            transport=httpx.MockTransport(auth_server),
        )
        previous.close()

    monkeypatch.setattr(SupabaseAuth, "__init__", setup_provider)
    credentials = {"email": EMAIL, "password": PASSWORD}
    with (
        TestClient(app, base_url=ORIGIN["Origin"]) as client,
        closing(TestClient(app, base_url=ORIGIN["Origin"])) as other,
    ):
        pending = client.post(
            f"{ROOT}/auth/register",
            json={**credentials, "name": "Persona"},
            headers=ORIGIN,
        )
        assert pending.status_code == 202 and "Set-Cookie" not in pending.headers
        invalid = client.post(
            f"{ROOT}/auth/register",
            json={**credentials, "name": "Persona", "password": "ñ" * 37},
            headers=ORIGIN,
        )
        assert invalid.status_code == 422
        assert (
            client.post(
                f"{ROOT}/auth/login", json=credentials, headers=ORIGIN
            ).status_code
            == 401
        )
        with managed_db.begin() as connection:
            connection.execute(
                text("INSERT INTO auth.users VALUES (:id, :email, now(), NULL, NULL)"),
                {"id": identity, "email": EMAIL},
            )
            connection.execute(
                text("INSERT INTO auth.sessions VALUES (:id)"), {"id": identity}
            )
            assert not connection.scalar(
                text("SELECT has_table_privilege('src_app', 'auth.users', 'DELETE')")
            )
            connection.execute(text("SET LOCAL ROLE src_app"))
            assert (
                connection.scalar(
                    text("SELECT src_auth.identity_id(:email)"), {"email": EMAIL}
                )
                == identity
            )
            assert not connection.scalar(
                text("SELECT has_table_privilege('anon', 'public.users', 'SELECT')")
            )
        confirmed = True
        login = client.post(f"{ROOT}/auth/login", json=credentials, headers=ORIGIN)
        assert login.status_code == 200, login.text
        assert login.json()["user"] == {
            "id": str(identity),
            "name": "Persona",
            "email": EMAIL,
        }
        headers = {**ORIGIN, "X-CSRF-Token": login.json()["csrf_token"]}
        assert (
            other.post(
                f"{ROOT}/auth/login", json=credentials, headers=ORIGIN
            ).status_code
            == 200
        )
        with managed_db.connect() as connection:
            assert connection.execute(
                text("SELECT email, password_hash FROM users")
            ).one() == (None, None)
        changed = client.put(
            f"{ROOT}/users/me/password",
            json={
                "current_password": PASSWORD,
                "new_password": "nueva contraseña de prueba",
            },
            headers=headers,
        )
        assert changed.status_code == 204, changed.text
        assert other.get(f"{ROOT}/auth/me").status_code == 401
        response = client.patch(
            f"{ROOT}/users/me",
            json={"email": "nuevo@example.com", "current_password": password},
            headers=headers,
        )
        assert response.status_code == 200 and response.json()["email"] == EMAIL
        assert email_change_requested
        with managed_db.begin() as connection:
            connection.execute(
                text("UPDATE auth.users SET email = 'nuevo@example.com'")
            )
        assert (
            client.get(f"{ROOT}/auth/me").json()["user"]["email"] == "nuevo@example.com"
        )
        room = client.post(
            f"{ROOT}/rooms", json={"name": "Sala de prueba"}, headers=headers
        )
        assert room.status_code == 201
        room_id = room.json()["id"]
        with managed_db.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO auth.users VALUES (:id, 'otra@example.com', now(), NULL, NULL)"
                ),
                {"id": successor},
            )
            connection.execute(
                text("INSERT INTO users (id, name) VALUES (:id, 'Sucesor')"),
                {"id": successor},
            )
            connection.execute(
                text(
                    "INSERT INTO room_members (id, room_id, user_id, role) VALUES (:id, :room, :user, 'member')"
                ),
                {"id": uuid4(), "room": room_id, "user": successor},
            )
        preview = client.get(f"{ROOT}/users/me/deletion-preview")
        body = {
            "current_password": password,
            "confirmation": "ELIMINAR",
            "room_actions": [
                {
                    "room_id": room_id,
                    "action": "transfer",
                    "new_owner_id": str(successor),
                }
            ],
        }
        with managed_db.begin() as connection:
            connection.execute(
                text("CREATE TABLE auth.block_delete (id uuid REFERENCES auth.users)")
            )
            connection.execute(
                text("INSERT INTO auth.block_delete VALUES (:id)"), {"id": identity}
            )
        response = client.post(
            f"{ROOT}/users/me/deletion",
            json=body,
            headers={**headers, "If-Match": preview.headers["ETag"]},
        )
        assert response.status_code == 409
        assert client.get(f"{ROOT}/auth/me").status_code == 200
        with managed_db.begin() as connection:
            assert (
                connection.scalar(text("SELECT owner_user_id FROM rooms")) == identity
            )
            connection.execute(text("DELETE FROM auth.block_delete"))
        response = client.post(
            f"{ROOT}/users/me/deletion",
            json=body,
            headers={**headers, "If-Match": preview.headers["ETag"]},
        )
        assert response.status_code == 204, response.text
        assert client.get(f"{ROOT}/auth/me").status_code == 401
        with managed_db.connect() as connection:
            for name in ("users", "auth.users"):
                assert connection.scalars(text(f"SELECT id FROM {name}")).all() == [
                    successor
                ]
            for name in ("sessions", "auth.sessions"):
                assert connection.scalar(text(f"SELECT count(*) FROM {name}")) == 0
            assert (
                connection.scalar(text("SELECT owner_user_id FROM rooms")) == successor
            )
            assert connection.execute(
                text("SELECT user_id, role FROM room_members")
            ).all() == [(successor, "admin")]
