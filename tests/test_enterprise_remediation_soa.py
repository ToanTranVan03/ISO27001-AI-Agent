import uuid
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.team_api import require_user
import backend.enterprise_api as api
from backend.soa_report import build_soa_matrix, render_soa_html
from evidence_collectors import enterprise_container_collector as ecc


def test_soa_matrix_structure(monkeypatch):
    test_id = str(uuid.uuid4())
    monkeypatch.setattr("backend.database.list_controls", lambda: [
        {"control_id": "A.5.1", "name": "Policies for information security", "objective": "Obj A.5.1", "group": "A.5"},
        {"control_id": "A.8.5", "name": "Secure authentication", "objective": "Obj A.8.5", "group": "A.8"},
    ])
    monkeypatch.setattr("backend.teamwork.progress_board", lambda aid: [
        {"control_id": "A.5.1", "compliance_status": "Compliant", "workflow_status": "COMPLETED"},
        {"control_id": "A.8.5", "compliance_status": "Non-Compliant", "workflow_status": "COMPLETED", "latest_evaluation_id": 10},
    ])
    monkeypatch.setattr("backend.teamwork.list_history", lambda aid, cid: [
        {"rationale": "Vi pham mat khau va tai khoan chua khoa"}
    ])

    soa = build_soa_matrix(test_id)
    assert soa["standard"] == "ISO/IEC 27001:2022 & ISO/IEC 27002:2022 Annex A"
    assert soa["stats"]["total"] == 2
    assert soa["stats"]["compliant"] == 1
    assert soa["stats"]["non_compliant"] == 1
    assert len(soa["risk_treatment_plan"]) == 1
    assert soa["risk_treatment_plan"][0]["control_id"] == "A.8.5"

    html = render_soa_html(soa)
    assert "BẢN TUYÊN BỐ VỀ KHẢ NĂNG ÁP DỤNG" in html
    assert "A.8.5" in html
    assert "Secure authentication" in html
    assert "KẾ HOẠCH XỬ LÝ RỦI RO" in html


def test_remediation_actions_dispatch(monkeypatch):
    monkeypatch.setattr(ecc, "_run_docker_exec", lambda c, cmd: (0, "success"))
    res_iam = ecc.execute_remediation("iam", "lock_terminated_user")
    assert res_iam["success"] is True
    assert res_iam["container"] == "corp-iam-auth-node"

    res_net = ecc.execute_remediation("network", "harden_security_headers")
    assert res_net["success"] is True
    assert res_net["container"] == "corp-network-fw-node"

    res_sec = ecc.execute_remediation("secops", "trigger_emergency_backup")
    assert res_sec["success"] is True
    assert res_sec["container"] == "corp-secops-log-node"

    monkeypatch.setattr(ecc, "_run_docker_exec", lambda c, cmd: (0, '[{"emp_id":"E1","nda_signed":false}]' if "cat" in cmd else "ok"))
    res_hr = ecc.execute_remediation("hr", "sign_pending_ndas")
    assert res_hr["success"] is True
    assert res_hr["container"] == "corp-hr-directory"

    monkeypatch.setattr(ecc, "_run_docker_exec", lambda c, cmd: (0, "ok"))
    res_siem = ecc.execute_remediation("siem", "enforce_tamper_proof")
    assert res_siem["success"] is True
    assert res_siem["container"] == "corp-siem-audit-node"

    with pytest.raises(ValueError):
        ecc.execute_remediation("unknown_node", "action")


def test_enterprise_remediation_api_permissions(monkeypatch):
    app.dependency_overrides[require_user] = lambda: {"user_id": "u1", "role": "member", "username": "mem"}
    monkeypatch.setattr(api, "require_campaign", lambda *args: None)
    test_id = str(uuid.uuid4())

    try:
        with TestClient(app) as client:
            # Member is rejected from remediation (admin only)
            resp = client.post(f"/api/assessments/{test_id}/enterprise/remediate", json={
                "node_key": "iam",
                "action": "lock_terminated_user"
            })
            assert resp.status_code == 403

            # Override as admin
            app.dependency_overrides[require_user] = lambda: {"user_id": "u1", "role": "admin", "username": "adm"}
            monkeypatch.setattr(ecc, "execute_remediation", lambda k, a: {"success": True, "message": "done"})
            monkeypatch.setattr("backend.database.get_connection", lambda: _mock_con())

            resp_admin = client.post(f"/api/assessments/{test_id}/enterprise/remediate", json={
                "node_key": "iam",
                "action": "lock_terminated_user"
            })
            assert resp_admin.status_code == 200
            assert resp_admin.json()["success"] is True
    finally:
        app.dependency_overrides.pop(require_user, None)


class _mock_cur:
    def execute(self, *args, **kwargs):
        pass
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass

class _mock_con:
    def cursor(self):
        return _mock_cur()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass

