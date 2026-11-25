from concurrent.futures import ThreadPoolExecutor
from math import ceil
from threading import Event
from time import perf_counter
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import insert, update
from sqlalchemy.orm import Session as DbSession
from test_rooms import ROOMS, account, create, join, members

from app.core.config import Settings
from app.core.database import make_engine
from app.main import app
from app.models import RoomMember, Schedule, ScheduleBlock, User

pytestmark = pytest.mark.integration

COORDINATES = ((1, 1), (1, 2), (2, 3), (3, 4), (5, 6))


@pytest.fixture
def db():
    engine = make_engine(Settings())
    try:
        with DbSession(engine) as session:
            yield session
    finally:
        engine.dispose()


def seed_schedule(db, member_id, status, occupied):
    schedule = Schedule(member_id=UUID(member_id), status=status)
    db.add(schedule)
    db.flush()
    db.execute(
        insert(ScheduleBlock),
        [
            {
                "schedule_id": schedule.id,
                "day": day,
                "block": block,
                "is_occupied": (day, block) in occupied,
            }
            for day in range(1, 8)
            for block in range(1, 11)
        ],
    )
    db.commit()
    return schedule.id


def expect_matrix(client, auth, path, weights, confirmed, pending):
    response = client.get(path, headers=auth)
    assert response.status_code == 200
    result = response.json()
    cells = {(entry["day"], entry["block"]): entry for entry in result["cells"]}
    total = confirmed + pending
    assert result["total_members"] == total
    assert result["confirmed_members"] == confirmed
    assert result["pending_members"] == pending
    assert result["coverage"] == confirmed / total
    assert len(cells) == 70
    assert [cells[coordinate]["weight"] for coordinate in COORDINATES] == weights
    assert result["min_weight"] == min(cell["weight"] for cell in cells.values())
    assert result["max_weight"] == max(cell["weight"] for cell in cells.values())
    for cell in cells.values():
        assert 0 <= cell["weight"] <= confirmed <= total
        assert cell["weight"] + cell["available_count"] + cell["pending_count"] == total
        assert cell["intensity"] == cell["weight"] / total
        assert cell["everyone_available"] == (cell["weight"] == 0 and pending == 0)


def test_overlap_math_changes_roles_and_cell_details(db):
    with TestClient(app) as client:
        a_id, a = account(client)
        b_id, b = account(client)
        c_id, c = account(client)
        d_id, d = account(client)
        room = create(client, a, "Superposición matemática")
        rid = room["id"]
        path = f"{ROOMS}/{rid}/overlap"
        assert join(client, b, room["code"]).status_code == 201
        assert join(client, c, room["code"]).status_code == 201
        assert client.get(path, headers=b).status_code == 403
        assert client.get(f"{path}/cells/1/1", headers=b).status_code == 403
        assert client.get(path, headers=d).status_code == 404
        assert client.get(f"{path}/cells/8/1", headers=a).status_code == 422
        roster = members(client, a, rid)
        expect_matrix(client, a, path, [0, 0, 0, 0, 0], 0, 3)
        a_sid = seed_schedule(
            db, roster[a_id]["id"], "confirmed", {COORDINATES[i] for i in (0, 1, 4)}
        )
        seed_schedule(
            db, roster[b_id]["id"], "confirmed", {COORDINATES[i] for i in (1, 3, 4)}
        )
        c_sid = seed_schedule(
            db, roster[c_id]["id"], "confirmed", {COORDINATES[i] for i in (0, 1)}
        )
        expect_matrix(client, a, path, [2, 3, 0, 1, 2], 3, 0)
        cell = client.get(f"{path}/cells/1/1", headers=a).json()
        assert cell["weight"] == 2
        assert {item["id"] for item in cell["occupied_members"]} == {
            roster[a_id]["id"],
            roster[c_id]["id"],
        }
        assert [item["id"] for item in cell["available_members"]] == [
            roster[b_id]["id"]
        ]
        assert cell["pending_members"] == []
        assert set(cell["occupied_members"][0]) == {"id", "name"}

        edit = client.get(f"{ROOMS}/{rid}/schedules/me", headers=a).json()
        assert edit["schedule_id"] == str(a_sid)
        edit["blocks"][0]["is_occupied"] = False
        assert (
            client.put(
                f"{ROOMS}/{rid}/schedules/me",
                headers=a,
                json={
                    "expected_version": edit["version"],
                    "blocks": edit["blocks"],
                },
            ).status_code
            == 200
        )
        expect_matrix(client, a, path, [1, 3, 0, 1, 2], 3, 0)

        assert (
            client.delete(
                f"{ROOMS}/{rid}/members/{roster[b_id]['id']}", headers=a
            ).status_code
            == 204
        )
        assert join(client, d, room["code"]).status_code == 201
        roster = members(client, a, rid)
        seed_schedule(db, roster[d_id]["id"], "draft", set(COORDINATES))
        expect_matrix(client, a, path, [1, 2, 0, 0, 1], 2, 1)
        cell = client.get(f"{path}/cells/1/1", headers=a).json()
        assert [item["id"] for item in cell["pending_members"]] == [roster[d_id]["id"]]
        assert (
            client.patch(
                f"{ROOMS}/{rid}/members/{roster[d_id]['id']}/role",
                headers=a,
                json={"role": "admin"},
            ).status_code
            == 204
        )
        individual_path = f"{ROOMS}/{rid}/members/{roster[c_id]['id']}/schedule"
        individual = client.get(individual_path, headers=d).json()
        assert (
            individual["schedule_id"] == str(c_sid) and len(individual["blocks"]) == 70
        )
        expect_matrix(client, d, path, [1, 2, 0, 0, 1], 2, 1)


def test_overlap_snapshot_during_atomic_schedule_changes(db):
    with TestClient(app) as client:
        _, owner = account(client)
        rid = create(client, owner, "Sala concurrente")["id"]
        member_id = next(iter(members(client, owner, rid).values()))["id"]
        sid = seed_schedule(db, member_id, "confirmed", {(1, 1)})
        started = Event()
        release = Event()

        def change_schedule():
            with DbSession(db.bind) as writer, writer.begin():
                writer.execute(
                    update(Schedule).where(Schedule.id == sid).values(status="draft")
                )
                started.set()
                assert release.wait(10)
                writer.execute(
                    update(ScheduleBlock)
                    .where(ScheduleBlock.schedule_id == sid)
                    .values(is_occupied=False)
                )

        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(change_schedule)
            try:
                assert started.wait(5)
                expect_matrix(
                    client, owner, f"{ROOMS}/{rid}/overlap", [1, 0, 0, 0, 0], 1, 0
                )
            finally:
                release.set()
            pending.result(timeout=10)
        expect_matrix(client, owner, f"{ROOMS}/{rid}/overlap", [0, 0, 0, 0, 0], 0, 1)


def test_overlap_at_room_capacity(db):
    with TestClient(app) as client:
        _, owner = account(client)
        rid = create(client, owner, "Sala de cien")["id"]
        roster = members(client, owner, rid)
        owner_member = UUID(next(iter(roster.values()))["id"])
        users = [uuid4() for _ in range(99)]
        member_ids = [uuid4() for _ in users]
        schedule_ids = [uuid4() for _ in range(100)]
        db.execute(
            insert(User),
            [
                {
                    "id": uid,
                    "name": f"Integrante {i}",
                    "email": f"{uid}@example.com",
                    "password_hash": "fixture",
                }
                for i, uid in enumerate(users)
            ],
        )
        db.execute(
            insert(RoomMember),
            [
                {"id": mid, "room_id": UUID(rid), "user_id": uid, "role": "member"}
                for mid, uid in zip(member_ids, users, strict=True)
            ],
        )
        db.execute(
            insert(Schedule),
            [
                {"id": sid, "member_id": mid, "status": "confirmed"}
                for sid, mid in zip(
                    schedule_ids, [owner_member, *member_ids], strict=True
                )
            ],
        )
        db.execute(
            insert(ScheduleBlock),
            [
                {
                    "schedule_id": sid,
                    "day": day,
                    "block": block,
                    "is_occupied": index % 2 == 0,
                }
                for index, sid in enumerate(schedule_ids)
                for day in range(1, 8)
                for block in range(1, 11)
            ],
        )
        db.commit()
        path = f"{ROOMS}/{rid}/overlap"
        expect_matrix(client, owner, path, [50] * 5, 100, 0)
        timings = []
        for _ in range(20):
            start = perf_counter()
            response = client.get(path, headers=owner)
            timings.append(perf_counter() - start)
            assert response.status_code == 200
        p95 = sorted(timings)[ceil(len(timings) * 0.95) - 1]
        print(
            f"Superposición con 100 integrantes y 7000 celdas persistidas: p95 {p95 * 1000:.1f} ms."
        )
