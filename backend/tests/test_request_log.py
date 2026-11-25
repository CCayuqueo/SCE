import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.request_log import log_request, logger


def test_http_logs_do_not_record_request_secrets_or_exception_text(monkeypatch):
    sample = FastAPI()
    sample.middleware("http")(log_request)

    @sample.post("/operation/{value}")
    def operation(value: str) -> None:
        raise ValueError(value)

    lines = []
    monkeypatch.setattr(logger, "info", lines.append)
    request_id = "a" * 32
    with TestClient(sample) as client:
        response = client.post(
            "/operation/private-path?value=private-query",
            headers={
                "X-Request-ID": request_id,
                "Cookie": "src_session=private-cookie",
            },
            json={"password": "private-body"},
        )
    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == request_id
    assert "private-" not in response.text and "private-" not in lines[0]
    event = json.loads(lines[0])
    assert event["request_id"] == request_id and event["error"] == "ValueError"
    assert event["duration_ms"] >= 0
