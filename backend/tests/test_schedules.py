from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from fastapi.testclient import TestClient
from test_image_processing import SAMPLE
from test_rooms import ROOMS, ROOT, account, create, join, members

from app.main import app

pytestmark = pytest.mark.integration


def upload(client, auth, path, version=0, data=None, filename="horario.png"):
    return client.post(
        f"{path}/upload",
        headers=auth,
        files={
            "file": (
                filename,
                SAMPLE.read_bytes() if data is None else data,
                "image/png",
            )
        },
        data={"expected_version": str(version)},
    )


def test_upload_draft_confirm_replace_and_fail_without_losing_schedule(monkeypatch):
    monkeypatch.setenv("MAX_UPLOAD_MB", "1")
    with TestClient(app) as client:
        _, owner = account(client)
        student_id, student = account(client)
        _, outsider = account(client)
        room = create(client, owner, "Horarios semanales")
        rid = room["id"]
        own = f"{ROOMS}/{rid}/schedules/me"
        assert client.get(own, headers=outsider).status_code == 404
        assert client.get(own, headers=student).status_code == 404
        assert join(client, student, room["code"]).status_code == 201
        assert client.get(own, headers=student).json() == {
            "schedule_id": None,
            "status": "missing",
            "version": 0,
            "blocks": [],
        }
        result = upload(client, student, own)
        assert result.status_code == 201, result.text
        draft = result.json()
        assert (
            draft["status"] == "draft"
            and draft["version"] == 1
            and len(draft["blocks"]) == 70
        )
        student_member = members(client, owner, rid)[student_id]["id"]
        shared = f"{ROOMS}/{rid}/members/{student_member}/schedule"
        assert client.get(shared, headers=student).status_code == 403
        assert client.get(shared, headers=owner).json()["blocks"] == []
        assert client.put(shared, headers=owner, json={}).status_code == 405

        changed = draft["blocks"]
        changed[-1]["is_occupied"] = not changed[-1]["is_occupied"]
        payload = {"expected_version": 1, "blocks": changed}
        duplicated = {**payload, "blocks": [changed[0], *changed[:-1]]}
        assert client.put(own, headers=student, json=duplicated).status_code == 422
        confirmed = client.put(own, headers=student, json=payload)
        assert confirmed.status_code == 200, confirmed.text
        assert (
            confirmed.json()["version"] == 2
            and confirmed.json()["status"] == "confirmed"
        )
        assert confirmed.json()["blocks"] == changed
        assert client.put(own, headers=student, json=payload).status_code == 409
        assert client.get(shared, headers=owner).json() == confirmed.json()

        assert upload(client, student, own, 2, b"%PDF-1.4").status_code == 415
        assert (
            upload(client, student, own, 2, SAMPLE.read_bytes()[:50]).status_code == 422
        )
        assert upload(client, student, own, 2, b"x" * (1024**2 + 1)).status_code == 413
        oversized = upload(client, student, own, 2, b"x" * (2 * 1024**2))
        assert (
            oversized.status_code == 413
            and oversized.json()["error"]["code"] == "IMAGE_TOO_LARGE"
        )
        assert client.get(own, headers=student).json() == confirmed.json()

        replaced = upload(client, student, own, 2)
        assert replaced.status_code == 200
        assert replaced.json()["status"] == "draft" and replaced.json()["version"] == 3
        assert client.get(shared, headers=owner).json()["blocks"] == []
        assert client.delete(own, headers=student).status_code == 204
        assert client.get(own, headers=student).json()["status"] == "missing"
        recreated = upload(client, student, own)
        assert recreated.status_code == 201
        old_tag = f'"{draft["schedule_id"]}:1"'
        assert (
            client.put(
                own, headers={**student, "If-Match": old_tag}, json=payload
            ).status_code
            == 409
        )


@pytest.mark.parametrize("change", ["confirm", "leave", "logout"])
def test_upload_revalidates_after_processing_without_holding_locks(change, monkeypatch):
    with TestClient(app) as client:
        _, owner = account(client)
        _, student = account(client)
        room = create(client, owner, "Procesamiento concurrente")
        rid = room["id"]
        own = f"{ROOMS}/{rid}/schedules/me"
        assert join(client, student, room["code"]).status_code == 201
        draft = upload(client, student, own).json()
        started, resume = Event(), Event()
        process = app.state.image_processor.process

        def delayed(data):
            started.set()
            assert resume.wait(10)
            return process(data)

        monkeypatch.setattr(app.state.image_processor, "process", delayed)
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(upload, client, student, own, draft["version"])
            try:
                assert started.wait(5)
                if change == "confirm":
                    assert (
                        client.put(
                            own,
                            headers=student,
                            json={
                                "expected_version": draft["version"],
                                "blocks": draft["blocks"],
                            },
                        ).status_code
                        == 200
                    )
                elif change == "leave":
                    assert (
                        client.delete(
                            f"{ROOMS}/{rid}/membership/me", headers=student
                        ).status_code
                        == 204
                    )
                else:
                    assert (
                        client.post(f"{ROOT}/auth/logout", headers=student).status_code
                        == 204
                    )
            finally:
                resume.set()
            assert (
                pending.result(timeout=10).status_code
                == {"confirm": 409, "leave": 404, "logout": 401}[change]
            )
