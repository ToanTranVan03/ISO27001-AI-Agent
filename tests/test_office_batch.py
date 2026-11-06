from uuid import uuid4
from backend import employee_commands as commands


def test_batch_continues_after_guard_failure_and_reuses_ids(monkeypatch):
    machines = [{"employee_id": actor, "state": {"shift": "off"}} for actor in ["EMP-001", "EMP-003"]]
    monkeypatch.setattr(commands, "workspace_state", lambda _: machines)
    monkeypatch.setattr(commands, "command_history", lambda _: [])
    calls = []
    def execute(aid, actor, command, key, user):
        calls.append((actor, command, key))
        if actor == "EMP-001":
            raise ValueError("busy")
        return {"event_id": str(key)}
    monkeypatch.setattr(commands, "execute_command", execute)
    key = uuid4()
    result = commands.execute_office_command("assessment", "start_shift", key, "user")
    assert [r["ok"] for r in result["results"]] == [False, True]
    assert result["results"][0]["reason"] == "busy"
    assert [c[1] for c in calls] == ["/vao-ca", "/vao-ca", "/lam-viec"]
    first = calls.copy()
    commands.execute_office_command("assessment", "start_shift", key, "user")
    assert calls[3:] == first


def test_end_shift_does_not_bypass_cleanup(monkeypatch):
    monkeypatch.setattr(commands, "workspace_state", lambda _: [{"employee_id": "EMP-001", "state": {"shift": "on"}}])
    monkeypatch.setattr(commands, "command_history", lambda _: [])
    def execute(aid, actor, command, key, user):
        assert command == "/tan-ca"
        raise ValueError("USB must be removed")
    monkeypatch.setattr(commands, "execute_command", execute)
    result = commands.execute_office_command("assessment", "end_shift", uuid4(), "user")
    assert not result["results"][0]["ok"]
