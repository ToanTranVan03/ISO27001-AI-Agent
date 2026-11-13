"""CLI regressions use fake inputs; never create real human-review records."""
from contextlib import nullcontext
from copy import deepcopy
from unittest.mock import Mock

import pytest

from scripts import run_human_review as cli
from scripts import seed_team_accounts as accounts


@pytest.fixture
def blind_pack():
    return dict(state="finished", blind=True, can_review=True,
                report_sha256="a" * 64, submitted_controls=[], evidence_pack=[dict(
                    control_id="A.8.13", name="Backup", criteria_checks=["restore_test_passed"],
                    criteria_details=[dict(pass_condition="Restored bytes equal backup")],
                    evidence=dict(artifacts=[dict(artifact="restored.dat", content="raw observation")]))])


def enter(monkeypatch, answers):
    values = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _: next(values))


def test_explicit_answers_and_assistance_are_preserved(monkeypatch, capsys, blind_pack):
    request = Mock(return_value=blind_pack)
    enter(monkeypatch, ["", "4", "short", "Human saw that restore evidence is missing.", "2", "2", "NOP"])
    cli.review(request, "/study", "run")
    output = capsys.readouterr().out
    assert "raw observation" in output and "Restored bytes equal backup" in output
    payload = request.call_args.args[2]
    assert payload == dict(control_id="A.8.13", expected="Insufficient Evidence",
                           rationale="Human saw that restore evidence is missing.",
                           report_sha256="a" * 64, assistance="ai_assisted", prior_exposure="yes")
    assert request.call_count == 2


@pytest.mark.parametrize("answers", [
    ["q"], ["1", "q"], ["1", "Human's own evidence reasoning.", "q"],
])
def test_interrupt_does_not_submit(monkeypatch, blind_pack, answers):
    request = Mock(return_value=blind_pack)
    enter(monkeypatch, answers)
    with pytest.raises(KeyboardInterrupt):
        cli.review(request, "/study", "run")
    request.assert_called_once_with("GET", "/study/runs/run")


def test_no_submission_without_explicit_confirmation(monkeypatch, blind_pack):
    request = Mock(return_value=blind_pack)
    enter(monkeypatch, ["2", "Human's own evidence reasoning.", "1", "1", ""])
    cli.review(request, "/study", "run")
    assert request.call_count == 1


def test_resume_skips_locked_controls(monkeypatch, blind_pack):
    second = deepcopy(blind_pack["evidence_pack"][0])
    second["control_id"] = "A.8.15"
    blind_pack["evidence_pack"].append(second)
    blind_pack["submitted_controls"] = ["A.8.13"]
    request = Mock(return_value=blind_pack)
    enter(monkeypatch, ["3", "Human inspected the audit evidence.", "1", "3", "NOP"])
    cli.review(request, "/study", "run")
    assert request.call_count == 2
    assert request.call_args.args[2]["control_id"] == "A.8.15"
    assert request.call_args.args[2]["prior_exposure"] == "unknown"


@pytest.mark.parametrize("state", [dict(state="running"), dict(can_review=False)])
def test_unfinished_or_old_protocol_cannot_submit(blind_pack, state):
    blind_pack.update(state)
    request = Mock(return_value=blind_pack)
    with pytest.raises(ValueError):
        cli.review(request, "/study", "run")
    assert request.call_count == 1


def test_unblinded_pack_is_not_submitted(blind_pack):
    blind_pack["blind"] = False
    request = Mock(return_value=blind_pack)
    cli.review(request, "/study", "run")
    assert request.call_count == 1


@pytest.mark.parametrize("args", [["--auto"], ["--action", "review-all"], []])
def test_auto_modes_and_implicit_run_are_rejected(monkeypatch, args):
    monkeypatch.setattr("sys.argv", ["run_human_review.py", *args])
    monkeypatch.setattr(cli, "getpass", lambda _: pytest.fail("Must reject before login"))
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2


@pytest.mark.parametrize("existing", [None, ("existing-tu-id", "assessor")])
def test_seed_tu_preserves_other_accounts_and_existing_password(monkeypatch, existing):
    cursor = Mock()
    cursor.fetchone.return_value = existing
    connection = Mock()
    connection.cursor.return_value = nullcontext(cursor)
    monkeypatch.setattr(accounts, "get_connection", lambda: nullcontext(connection))
    if existing:
        monkeypatch.setattr(accounts, "getpass", lambda _: pytest.fail("Must preserve existing password"))
    else:
        monkeypatch.setattr(accounts, "getpass", lambda _: "Test-only-password-123")
        monkeypatch.setattr(accounts, "hash_password", lambda _: "test-hash")
    accounts.seed("tu")
    calls = cursor.execute.call_args_list
    assert calls[0].args[1] == ("vantu",)
    assert all(not c.args[0].lstrip().upper().startswith(("DELETE", "UPDATE")) for c in calls)
    assert not any("team_sessions" in c.args[0] or "login_attempts" in c.args[0] for c in calls)
    inserts = [c for c in calls if "INSERT INTO team_users" in c.args[0]]
    assert len(inserts) == (0 if existing else 1)
    if inserts:
        assert inserts[0].args[1][1] == "vantu"
    assert "INSERT INTO assessment_members" in calls[-1].args[0]


def test_seed_refuses_wrong_existing_role(monkeypatch):
    cursor = Mock()
    cursor.fetchone.return_value = ("existing-id", "admin")
    connection = Mock()
    connection.cursor.return_value = nullcontext(cursor)
    monkeypatch.setattr(accounts, "get_connection", lambda: nullcontext(connection))
    with pytest.raises(ValueError):
        accounts.seed("tu")
    assert cursor.execute.call_count == 1
