from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.auth.dependencies import SESSION_COOKIE
from app.core.config import Settings
from app.core.database import make_engine
from app.main import app
from app.models import RoomMember, Schedule, ScheduleBlock
from app.rooms import service

pytestmark = pytest.mark.integration
ROOT = "/api/v1"
ROOMS = f"{ROOT}/rooms"
ORIGIN = {"Origin": "http://localhost:3000"}
PASSWORD = "contraseña para probar salas"


@pytest.fixture
def db():
    engine = make_engine(Settings())
    try:
        with DbSession(engine) as session:
            yield session
    finally:
        engine.dispose()


def account(client):
    response = client.post(
        f"{ROOT}/auth/register",
        headers=ORIGIN,
        json={
            "name": "Persona de prueba",
            "email": f"{uuid4()}@example.com",
            "password": PASSWORD,
        },
    )
    assert response.status_code == 201
    return_auth = {
        **ORIGIN,
        "Cookie": f"{SESSION_COOKIE}={client.cookies[SESSION_COOKIE]}",
        "X-CSRF-Token": client.get(f"{ROOT}/auth/me").json()["csrf_token"],
    }
    client.cookies.clear()
    return response.json()["id"], return_auth


def create(client, auth, name):
    response = client.post(ROOMS, headers=auth, json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()


def join(client, auth, code):
    return client.post(f"{ROOMS}/join", headers=auth, json={"code": code})


def members(client, auth, room_id):
    response = client.get(f"{ROOMS}/{room_id}/members", headers=auth)
    assert response.status_code == 200, response.text
    return {member["user_id"]: member for member in response.json()["members"]}


def change_role(client, auth, room_id, member, role):
    return client.patch(
        f"{ROOMS}/{room_id}/members/{member}/role", headers=auth, json={"role": role}
    )


def test_role_isolation_local_administration_and_transfer(monkeypatch):
    collision = service.generate_code()
    codes = iter([collision, collision, service.generate_code()])
    monkeypatch.setattr(service, "generate_code", lambda: next(codes))
    with TestClient(app) as client:
        first_id, first = account(client)
        second_id, second = account(client)
        third_id, third = account(client)
        assert client.get(ROOMS).status_code == 401
        without_csrf = {
            key: value for key, value in first.items() if key != "X-CSRF-Token"
        }
        assert (
            client.post(
                ROOMS, headers=without_csrf, json={"name": "Sin CSRF"}
            ).status_code
            == 403
        )
        a = create(client, first, "Sala A")
        b = create(client, third, "Sala B")
        aid, bid = a["id"], b["id"]
        assert a["code"] != b["code"]
        assert a["current_user_role"] == "owner" and a["members_count"] == 1
        assert client.get(f"{ROOMS}/{aid}", headers=third).status_code == 404
        assert join(client, second, "ZZZZZZZZZZZZ").status_code == 404
        assert client.get(ROOMS, headers=second).json() == []
        assert join(client, second, f" {a['code'].lower()} ").status_code == 201
        repeat = join(client, second, a["code"])
        assert repeat.status_code == 200 and repeat.json()["members_count"] == 2
        assert repeat.json()["code"] is None
        assert join(client, third, a["code"]).status_code == 201
        assert join(client, second, b["code"]).status_code == 201
        roster = members(client, first, aid)
        assert "email" not in roster[second_id]
        second_member = roster[second_id]["id"]
        third_member = roster[third_id]["id"]
        assert roster[first_id]["role"] == "owner"
        assert (
            client.delete(f"{ROOMS}/{aid}/membership/me", headers=first).status_code
            == 409
        )
        assert (
            change_role(client, second, aid, third_member, "admin").status_code == 403
        )
        assert (
            change_role(client, first, aid, second_member, "admin").status_code == 204
        )
        assert (
            change_role(client, second, aid, third_member, "admin").status_code == 204
        )
        assert (
            change_role(client, second, aid, third_member, "member").status_code == 403
        )
        assert (
            change_role(client, first, aid, third_member, "member").status_code == 204
        )
        assert client.get(f"{ROOMS}/{bid}/members", headers=second).status_code == 403
        wrong_member = members(client, third, bid)[second_id]["id"]
        assert change_role(client, first, aid, wrong_member, "admin").status_code == 404
        listed = {room["id"]: room for room in client.get(ROOMS, headers=second).json()}
        assert listed[aid]["current_user_role"] == "admin"
        assert (
            listed[bid]["current_user_role"] == "member" and listed[bid]["code"] is None
        )
        response = client.patch(
            f"{ROOMS}/{aid}", headers=second, json={"description": "Editada"}
        )
        assert (
            response.status_code == 200 and response.json()["description"] == "Editada"
        )
        assert (
            client.post(
                f"{ROOMS}/{aid}/transfer-ownership",
                headers=first,
                json={"new_owner_id": third_id},
            ).json()["current_user_role"]
            == "admin"
        )
        assert members(client, third, aid)[third_id]["role"] == "owner"
        assert client.delete(f"{ROOMS}/{aid}", headers=first).status_code == 403


def test_concurrent_joins_respect_capacity_and_idempotency(monkeypatch):
    monkeypatch.setenv("MAX_ROOM_MEMBERS", "2")
    with TestClient(app) as client:
        _, owner = account(client)
        _, member_a = account(client)
        _, member_b = account(client)
        room = create(client, owner, "Sala de capacidad")
        barrier = Barrier(3)

        def try_join(auth):
            barrier.wait(timeout=5)
            return join(client, auth, room["code"]).status_code

        with ThreadPoolExecutor(max_workers=3) as pool:
            statuses = list(pool.map(try_join, [member_a, member_a, member_b]))
        assert sorted(statuses) in ([200, 201, 409], [201, 409, 409])
        assert len(members(client, owner, room["id"])) == 2


def add_block(db, membership_id):
    schedule = Schedule(member_id=UUID(membership_id))
    db.add(schedule)
    db.flush()
    db.add(ScheduleBlock(schedule_id=schedule.id, day=1, block=1, is_occupied=True))
    db.commit()
    return schedule.id


def test_leave_expel_and_delete_cascade_with_real_room_endpoints(db):
    with TestClient(app) as client:
        owner_id, owner = account(client)
        regular_id, regular = account(client)
        expelled_id, expelled = account(client)
        room = create(client, owner, "Salas y cascadas")
        rid = room["id"]
        for auth in (regular, expelled):
            assert join(client, auth, room["code"]).status_code == 201
        roster = members(client, owner, rid)
        ids = [
            add_block(db, roster[user]["id"])
            for user in (owner_id, regular_id, expelled_id)
        ]
        assert (
            client.delete(f"{ROOMS}/{rid}/membership/me", headers=regular).status_code
            == 204
        )
        assert (
            client.delete(
                f"{ROOMS}/{rid}/members/{roster[expelled_id]['id']}", headers=owner
            ).status_code
            == 204
        )
        assert client.delete(f"{ROOMS}/{rid}", headers=owner).status_code == 204
        for schedule_id in ids:
            assert db.get(Schedule, schedule_id) is None
            assert db.get(ScheduleBlock, (schedule_id, 1, 1)) is None


def test_delete_account_transfers_room_created_through_api(db):
    with TestClient(app) as client:
        _, owner = account(client)
        successor_id, successor = account(client)
        room = create(client, owner, "Sala a conservar")
        rid = room["id"]
        assert join(client, successor, room["code"]).status_code == 201
        preview = client.get(f"{ROOT}/users/me/deletion-preview", headers=owner)
        response = client.post(
            f"{ROOT}/users/me/deletion",
            headers={**owner, "If-Match": preview.headers["ETag"]},
            json={
                "current_password": PASSWORD,
                "confirmation": "ELIMINAR",
                "room_actions": [
                    {"room_id": rid, "action": "transfer", "new_owner_id": successor_id}
                ],
            },
        )
        assert response.status_code == 204
        assert [item["role"] for item in members(client, successor, rid).values()] == [
            "owner"
        ]
        assert (
            db.scalar(select(RoomMember.role).where(RoomMember.room_id == UUID(rid)))
            == "admin"
        )
