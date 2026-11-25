from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session as DbSession

from app.auth.dependencies import SESSION_COOKIE
from app.core.config import Settings
from app.core.database import make_engine
from app.main import app
from app.models import Room, RoomMember, Schedule, ScheduleBlock, User

pytestmark = pytest.mark.integration
PREFIX = "/api/v1"
ORIGIN = {"Origin": "http://localhost:3000"}
PASSWORD = "contraseña temporal de pruebas"


def register(client):
    email = f"{uuid4()}@example.com"
    response = client.post(
        f"{PREFIX}/auth/register",
        headers=ORIGIN,
        json={"name": "Cuenta de prueba", "email": email, "password": PASSWORD},
    )
    assert response.status_code == 201
    return email


def session_headers(client):
    return {
        **ORIGIN,
        "X-CSRF-Token": client.get(f"{PREFIX}/auth/me").json()["csrf_token"],
    }


@pytest.fixture
def db():
    engine = make_engine(Settings())
    try:
        with DbSession(engine) as session:
            yield session
    finally:
        engine.dispose()


def test_profile_requires_password_for_email_and_password_change_revokes_other_sessions():
    with TestClient(app) as client:
        email = register(client)
        original = client.cookies[SESSION_COOKIE]
        client.cookies.clear()
        credentials = {"email": email, "password": PASSWORD}
        assert (
            client.post(
                f"{PREFIX}/auth/login", headers=ORIGIN, json=credentials
            ).status_code
            == 200
        )
        headers = session_headers(client)
        assert (
            client.patch(
                f"{PREFIX}/users/me", headers=ORIGIN, json={"name": "Otro nombre"}
            ).status_code
            == 403
        )
        new_email = f"{uuid4()}@example.com"
        assert (
            client.patch(
                f"{PREFIX}/users/me", headers=headers, json={"email": new_email}
            ).status_code
            == 403
        )
        profile = client.patch(
            f"{PREFIX}/users/me",
            headers=headers,
            json={
                "name": " Nuevo nombre ",
                "email": new_email.upper(),
                "current_password": PASSWORD,
            },
        )
        assert profile.status_code == 200
        assert profile.json()["name"] == "Nuevo nombre"
        assert client.get(f"{PREFIX}/users/me").json()["email"] == new_email

        new_password = "otra contraseña temporal"
        change = {"current_password": "incorrecta", "new_password": new_password}
        assert (
            client.put(
                f"{PREFIX}/users/me/password", headers=headers, json=change
            ).status_code
            == 403
        )
        assert (
            client.put(
                f"{PREFIX}/users/me/password",
                headers=headers,
                json={**change, "current_password": PASSWORD},
            ).status_code
            == 204
        )
        assert client.get(f"{PREFIX}/auth/me").status_code == 200
        assert (
            client.get(
                f"{PREFIX}/auth/me", headers={"Cookie": f"{SESSION_COOKIE}={original}"}
            ).status_code
            == 401
        )
        assert (
            client.post(
                f"{PREFIX}/auth/login",
                headers=ORIGIN,
                json={"email": new_email, "password": PASSWORD},
            ).status_code
            == 401
        )
        assert (
            client.post(
                f"{PREFIX}/auth/login",
                headers=ORIGIN,
                json={"email": new_email, "password": new_password},
            ).status_code
            == 200
        )


def make_room(db, owner, *others):
    room = Room(
        name="Sala de prueba", owner_user_id=owner, code=uuid4().hex[:12].upper()
    )
    db.add(room)
    db.flush()
    members = [
        RoomMember(room_id=room.id, user_id=user_id, role=role)
        for user_id, role in [(owner, "admin"), *others]
    ]
    db.add_all(members)
    db.flush()
    return room.id, members


def add_schedule(db, member):
    schedule = Schedule(member_id=member.id)
    db.add(schedule)
    db.flush()
    db.add(ScheduleBlock(schedule_id=schedule.id, day=1, block=1, is_occupied=True))
    return schedule.id


def test_deletion_conflicts_then_transfers_closes_and_cascades(db):
    with TestClient(app) as client:
        email = register(client)
        register_token = client.cookies[SESSION_COOKIE]
        client.cookies.clear()
        client.post(
            f"{PREFIX}/auth/login",
            headers=ORIGIN,
            json={"email": email, "password": PASSWORD},
        )
        owner = db.scalar(select(User.id).where(User.email == email))
        member = User(
            name="Integrante", email=f"{uuid4()}@example.com", password_hash="test"
        )
        admin = User(
            name="Administradora", email=f"{uuid4()}@example.com", password_hash="test"
        )
        db.add_all([member, admin])
        db.flush()
        member_id, admin_id = member.id, admin.id

        retained_id, memberships = make_room(
            db, owner, (member_id, "member"), (admin_id, "admin")
        )
        closed_id, closed = make_room(db, owner, (member_id, "member"))
        solo_id, _ = make_room(db, owner)
        foreign_id, foreign = make_room(db, admin_id, (owner, "member"))
        owner_schedule, other_schedule = [add_schedule(db, m) for m in memberships[:2]]
        closed_schedule = add_schedule(db, closed[1])
        foreign_schedule = add_schedule(db, foreign[1])
        db.commit()

        path = f"{PREFIX}/users/me"
        headers = session_headers(client)
        preview = client.get(f"{path}/deletion-preview")
        data = preview.json()
        assert data["memberships_count"] == 4 and data["schedules_count"] == 2
        records = {r["room_id"]: r for r in data["owned_rooms"]}
        assert records[str(retained_id)]["suggested_new_owner_id"] == str(admin_id)
        assert records[str(closed_id)]["suggested_new_owner_id"] == str(member_id)
        assert not records[str(solo_id)]["requires_decision"]
        actions = [
            {
                "room_id": str(retained_id),
                "action": "transfer",
                "new_owner_id": str(member_id),
            },
            {"room_id": str(closed_id), "action": "close"},
        ]
        body = {
            "current_password": PASSWORD,
            "confirmation": "ELIMINAR",
            "room_actions": actions,
        }
        guarded = {**headers, "If-Match": preview.headers["ETag"]}
        assert (
            client.post(f"{path}/deletion", headers=headers, json=body).status_code
            == 409
        )
        assert (
            client.post(
                f"{path}/deletion",
                headers=guarded,
                json={**body, "current_password": "incorrecta"},
            ).status_code
            == 403
        )
        assert (
            client.post(
                f"{path}/deletion",
                headers=guarded,
                json={**body, "room_actions": actions + actions[:1]},
            ).status_code
            == 409
        )
        assert (
            client.post(
                f"{path}/deletion",
                headers=guarded,
                json={**body, "room_actions": actions[:1]},
            ).status_code
            == 409
        )
        wrong_target = [{**actions[0], "new_owner_id": str(uuid4())}, actions[1]]
        assert (
            client.post(
                f"{path}/deletion",
                headers=guarded,
                json={**body, "room_actions": wrong_target},
            ).status_code
            == 409
        )

        room = db.get(Room, retained_id)
        room.name = "Sala modificada"
        db.commit()
        assert (
            client.post(f"{path}/deletion", headers=guarded, json=body).status_code
            == 409
        )
        assert db.get(User, owner) is not None
        assert db.get(Room, closed_id) is not None
        current = client.get(f"{path}/deletion-preview")
        assert (
            client.post(
                f"{path}/deletion",
                headers={**headers, "If-Match": current.headers["ETag"]},
                json=body,
            ).status_code
            == 204
        )
        assert client.get(f"{PREFIX}/auth/me").status_code == 401
        assert (
            client.get(
                f"{PREFIX}/auth/me",
                headers={"Cookie": f"{SESSION_COOKIE}={register_token}"},
            ).status_code
            == 401
        )

        db.expire_all()
        assert db.get(User, owner) is None
        assert db.get(Room, retained_id).owner_user_id == member_id
        assert (
            db.scalar(
                select(RoomMember.role).where(
                    RoomMember.room_id == retained_id, RoomMember.user_id == member_id
                )
            )
            == "admin"
        )
        assert db.get(Room, closed_id) is None and db.get(Room, solo_id) is None
        assert db.get(Room, foreign_id).owner_user_id == admin_id
        for schedule_id in (owner_schedule, closed_schedule, foreign_schedule):
            assert db.get(Schedule, schedule_id) is None
            assert db.get(ScheduleBlock, (schedule_id, 1, 1)) is None
        assert db.get(ScheduleBlock, (other_schedule, 1, 1)) is not None

        db.execute(delete(Room).where(Room.id.in_([retained_id, foreign_id])))
        db.execute(delete(User).where(User.id.in_([member_id, admin_id])))
        db.commit()
