from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from backend import main, incident_api, employee_commands
from backend.team_api import require_user


@pytest.mark.parametrize("text,actor,expected", [
    ("đi làm", "EMP-006", "/di-lam"),
    ("@EMP-025 tham gia", "EMP-025", "/di-lam"),
    ("  Cắm USB lạ  ", "EMP-006", "/usb-la"),
    ("/cai-app-la", "EMP-025", "/cai-app-la"),
    ("CÀI PHẦN MỀM CHƯA DUYỆT", "EMP-025", "/cai-app-la"),
    ("làm việc bình thường", "EMP-006", "/lam-viec"),
    ("/lam-viec", "EMP-025", "/lam-viec"),
    ("@EMP-006 rời máy không khóa", "EMP-006", "/roi-may"),
    ("@EMP-025 /cai-app-la", "EMP-025", "/cai-app-la"),
    ("vào ca", "EMP-044", "/vao-ca"),
    ("nghỉ giải lao", "EMP-003", "/nghi"),
    ("khóa màn hình", "EMP-001", "/khoa-may"),
    ("/usb-la", "EMP-044", "/usb-la"),
    ("/roi-may", "EMP-025", "/roi-may"),
])
def test_supported_commands(text, actor, expected):
    assert employee_commands.parse_command(text, actor)[0] == expected


@pytest.mark.parametrize("text,actor", [
    ("không cắm USB lạ", "EMP-006"),
    ("/usb-la; rm -rf /", "EMP-006"),
    ("/usb-la /lam-viec", "EMP-006"),
    ("/lam-viec", "EMP-999"),
    ("", "EMP-006"),
    ("@EMP-025 /usb-la", "EMP-006"),
    ("không rời máy", "EMP-006"),
])
def test_unknown_negated_compound_or_wrong_actor_commands_rejected(text, actor):
    with pytest.raises(ValueError):
        employee_commands.parse_command(text, actor)


def test_command_routes_require_auth():
    url = f"/api/assessments/{uuid4()}/enterprise/employee-commands"
    with TestClient(main.app) as client:
        assert client.get(url).status_code == 401
        assert client.get(url + '/catalog').status_code == 401
        assert client.post(url, json={"employee_id": "EMP-006", "text": "/usb-la", "request_id": str(uuid4())}).status_code == 401


def test_membership_denial_prevents_activity(monkeypatch):
    from fastapi import HTTPException
    main.app.dependency_overrides[require_user] = lambda: {"user_id": str(uuid4())}
    def forbidden(*args):
        raise HTTPException(403)
    monkeypatch.setattr(incident_api, "require_campaign", forbidden)
    monkeypatch.setattr(employee_commands, "execute_command", lambda *args: pytest.fail("Must not execute"))
    try:
        with TestClient(main.app) as client:
            response = client.post(f"/api/assessments/{uuid4()}/enterprise/employee-commands",
                json={"employee_id": "EMP-006", "text": "/usb-la", "request_id": str(uuid4())})
            assert response.status_code == 403
    finally:
        main.app.dependency_overrides.clear()


def test_command_starts_independent_monitor(monkeypatch):
    actor = {"user_id": str(uuid4())}
    main.app.dependency_overrides[require_user] = lambda: actor
    monkeypatch.setattr(incident_api, "require_campaign", lambda *args: None)
    calls = []
    monkeypatch.setattr(employee_commands, "execute_command", lambda *args: {"event_id": "CMD-test"})
    def start(*args):
        calls.append(args)
        return {"active": True}
    monkeypatch.setattr(incident_api, "start_automatic_monitor", start)
    try:
        with TestClient(main.app) as client:
            response = client.post(f"/api/assessments/{uuid4()}/enterprise/employee-commands",
                json={"employee_id": "EMP-006", "text": "/usb-la", "request_id": str(uuid4())})
            assert response.status_code == 200
            assert response.json() == {"event_id": "CMD-test", "monitor_active": True}
            assert len(calls) == 1
    finally:
        main.app.dependency_overrides.clear()
