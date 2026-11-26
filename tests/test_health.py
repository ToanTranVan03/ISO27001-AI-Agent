import pytest
from fastapi.testclient import TestClient

from compliance_ai.api import create_app
from compliance_ai.config import auth_secret


def test_health(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXECUTION_MODE", "SIMULATION")
    monkeypatch.setenv("LAB_ENABLED", "false")
    with TestClient(create_app()) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "execution_mode": "SIMULATION"}
        assert "/health" in client.get("/openapi.json").json()["paths"]


@pytest.mark.parametrize(
    ("key", "value"),
    [("EXECUTION_MODE", "LAB"), ("LAB_ENABLED", "true")],
)
def test_unsupported_execution_configuration(
    monkeypatch: pytest.MonkeyPatch, key: str, value: str
) -> None:
    monkeypatch.setenv(key, value)
    with pytest.raises(ValueError, match=key):
        create_app()


def test_auth_secret_has_no_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_SECRET_KEY", raising=False)
    with pytest.raises(ValueError, match="APP_SECRET_KEY"):
        auth_secret()


def test_ready_without_configured_database(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "")
    with TestClient(create_app()) as client:
        assert client.get("/ready").status_code == 503
