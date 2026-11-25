import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_liveness_independent_from_postgres(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://127.0.0.1:1/src")
    with TestClient(app) as client:
        assert client.get("/api/v1/health/live").json() == {"status": "ok"}
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "DATABASE_UNAVAILABLE"


@pytest.mark.integration
def test_readiness_with_postgres():
    with TestClient(app) as client:
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
