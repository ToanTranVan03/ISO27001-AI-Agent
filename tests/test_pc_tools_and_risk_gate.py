"""Unit tests for Phase 2: 3-tier risk-gated Parameterized Tools, RBAC, Snapshot/Rollback & Lab Adapter."""
import pytest
from pydantic import ValidationError

from backend.pc_storage import InMemoryPCStore
from lab_adapters.lab_adapter import LabHostConfig, RealLabExecutionAdapter
from lab_adapters.sim_adapter import SimulationExecutionAdapter
from simulation.scenarios import seed_canonical_company
from tools.playbooks import build_default_tool_registry
from tools.registry import ToolSecurityError


def _setup():
    store = InMemoryPCStore()
    seed_canonical_company(store, "COMP-CANONICAL-01")
    seed_canonical_company(store, "COMP-OTHER-02")
    adapter = SimulationExecutionAdapter(store)
    registry = build_default_tool_registry(store, adapter)
    return store, adapter, registry


def test_blocks_raw_shell_and_injection_and_cross_tenant_rbac():
    store, _, registry = _setup()

    # 1. Raw shell / unregistered tool must be blocked and audited
    with pytest.raises(ToolSecurityError):
        registry.invoke(
            company_id="COMP-CANONICAL-01",
            tool_name="run_raw_powershell",
            params={"cmd": "Remove-Item -Recurse C:\\"},
        )
    logs = store.list_audit_logs("COMP-CANONICAL-01")
    assert logs[-1]["status"] == "BLOCKED_SECURITY"

    # 2. Shell metacharacter injection inside parameters must fail Pydantic validation
    with pytest.raises(ValidationError):
        registry.invoke(
            company_id="COMP-CANONICAL-01",
            tool_name="disable_ad_and_revoke_access",
            params={
                "employee_id": "NV015; rm -rf /",
                "systems": ["active_directory"],
                "reason_ticket": "TKT-001",
            },
        )

    # 3. Cross-tenant RBAC violation blocked
    with pytest.raises(ToolSecurityError):
        registry.invoke(
            company_id="COMP-OTHER-02",
            tool_name="inspect_human_records",
            params={},
            allowed_companies={"COMP-CANONICAL-01"},
        )
    assert store.list_audit_logs("COMP-OTHER-02")[-1]["status"] == "BLOCKED_RBAC"


def test_low_risk_tools_auto_execute_and_support_dry_run():
    store, _, registry = _setup()

    dry = registry.invoke(
        company_id="COMP-CANONICAL-01",
        tool_name="send_nda_reminder",
        params={"employee_ids": ["NV046", "NV047"], "deadline_days": 5},
        control_id="A.6.6",
        dry_run=True,
    )
    assert dry["status"] == "DRY_RUN_PREVIEW"
    assert store.list_notifications("COMP-CANONICAL-01") == []

    real = registry.invoke(
        company_id="COMP-CANONICAL-01",
        tool_name="send_nda_reminder",
        params={"employee_ids": ["NV046", "NV047"], "deadline_days": 5},
        control_id="A.6.6",
    )
    assert real["status"] == "EXECUTED"
    assert real["risk_level"] == "LOW"
    assert real["result"]["sent_count"] == 2
    assert len(store.list_notifications("COMP-CANONICAL-01")) == 2


def test_medium_risk_scenario_1_patch_and_scenario_2_pc02_with_snapshot_and_rollback():
    store, _, registry = _setup()

    # Scenario 1 (A.8.8): Patch PC-03, PC-06, PC-09
    patch_res = registry.invoke(
        company_id="COMP-CANONICAL-01",
        tool_name="deploy_security_patches",
        params={
            "device_ids": ["PC-03", "PC-06", "PC-09"],
            "patch_ids": ["KB5044285", "KB5043076", "CVE-2026-1102-FIX"],
            "maintenance_window": "2026-11-28T02:00Z",
        },
        control_id="A.8.8",
    )
    assert patch_res["status"] == "EXECUTED"
    assert patch_res["compatibility"]["compatible"] is True
    assert patch_res["snapshot_before"]["snapshot_kind"] == "devices"
    pcs = [d for d in store.list_devices("COMP-CANONICAL-01") if d["device_id"].startswith("PC-")]
    assert all(d["patch_compliant"] for d in pcs)

    # Scenario 2 (A.8.9): Sync PC-02 baseline 4/6 -> 6/6, then test rollback
    sync_res = registry.invoke(
        company_id="COMP-CANONICAL-01",
        tool_name="sync_device_baseline_gpo",
        params={"device_id": "PC-02", "baseline_profile_id": "ISO27001-BASELINE-V1"},
        control_id="A.8.9",
    )
    assert sync_res["status"] == "EXECUTED"
    pc02_after = store.list_devices("COMP-CANONICAL-01", device_ids=["PC-02"])[0]
    assert pc02_after["firewall_enabled"] is True
    assert pc02_after["screen_lock_minutes"] == 5
    assert pc02_after["disk_encrypted"] is True
    assert pc02_after["password_policy_ok"] is True

    # Rollback PC-02 must restore exact pre-change snapshot
    rb = registry.rollback_action("COMP-CANONICAL-01", sync_res["action_id"], actor="admin:secops")
    assert rb["status"] == "ROLLED_BACK"
    pc02_restored = store.list_devices("COMP-CANONICAL-01", device_ids=["PC-02"])[0]
    assert pc02_restored["firewall_enabled"] is False
    assert pc02_restored["screen_lock_minutes"] == 30
    assert pc02_restored["disk_encrypted"] is False


def test_high_risk_scenario_4_nv015_requires_admin_approval_before_execution():
    store, _, registry = _setup()

    # Agent invokes HIGH RISK tool -> MUST pause at PENDING_APPROVAL
    queued = registry.invoke(
        company_id="COMP-CANONICAL-01",
        tool_name="disable_ad_and_revoke_access",
        params={
            "employee_id": "NV015",
            "systems": ["active_directory", "vpn", "email", "accounting_app"],
            "reason_ticket": "TKT-OFFBOARD-NV015",
        },
        control_id="A.6.5",
    )
    assert queued["status"] == "PENDING_APPROVAL"
    assert queued["compliance_status_hint"] == "Pending Remediation"
    # Accounts must still be active until Admin approves!
    assert len([a for a in store.list_accounts("COMP-CANONICAL-01", employee_id="NV015") if a["is_active"]]) == 4

    # Admin approves on Dashboard -> now executes & disables all 4 accounts
    approved = registry.approve_and_execute("COMP-CANONICAL-01", queued["action_id"], admin_actor="admin_khoa")
    assert approved["status"] == "EXECUTED"
    assert len([a for a in store.list_accounts("COMP-CANONICAL-01", employee_id="NV015") if a["is_active"]]) == 0

    # Audit log contains both PENDING_APPROVAL and APPROVED_AND_EXECUTED with SHA-256 hashes
    logs = store.list_audit_logs("COMP-CANONICAL-01")
    statuses = [l["status"] for l in logs]
    assert "PENDING_APPROVAL" in statuses
    assert "APPROVED_AND_EXECUTED" in statuses
    assert all(len(l["params_sha256"]) == 64 and len(l["result_sha256"]) == 64 for l in logs)


def test_real_lab_adapter_renders_safe_winrm_playbooks_for_pc02_and_nv015(monkeypatch):
    store = InMemoryPCStore()
    seed_canonical_company(store, "COMP-CANONICAL-01")
    cfg = LabHostConfig(
        ad_server_host="192.168.56.10",
        ad_username="Administrator",
        workstation_hosts={"PC-02": "192.168.56.22"},
    )
    adapter = RealLabExecutionAdapter(store, cfg)

    executed_calls = []

    def fake_winrm(host, script):
        executed_calls.append((host, script))
        return {"host": host, "status_code": 0, "stdout": '{"ok":true}', "stderr": ""}

    monkeypatch.setattr(adapter, "_run_winrm_ps", fake_winrm)

    # Dry-run never calls WinRM
    dry = adapter.sync_device_baseline_gpo("COMP-CANONICAL-01", "PC-02", "ISO27001-BASELINE-V1", dry_run=True)
    assert dry["dry_run"] is True
    assert len(executed_calls) == 0

    # Real run executes fixed PowerShell templates on PC-02 and AD server for NV015
    res_pc02 = adapter.sync_device_baseline_gpo("COMP-CANONICAL-01", "PC-02", "ISO27001-BASELINE-V1", dry_run=False)
    assert res_pc02["transport"] == "winrm"
    assert "Set-NetFirewallProfile" in executed_calls[0][1]
    assert "ScreenSaveTimeOut" in executed_calls[0][1]

    res_nv015 = adapter.disable_ad_and_revoke_access(
        "COMP-CANONICAL-01", "NV015", ["active_directory", "vpn", "email", "accounting_app"], "TKT-NV015", dry_run=False
    )
    assert res_nv015["transport"] == "winrm_ad"
    assert "Disable-ADAccount -Identity 'NV015'" in executed_calls[1][1]

    # Rejects unsafe token in script renderer
    with pytest.raises(ValueError):
        RealLabExecutionAdapter.render_ad_disable_script("NV015' ; whoami #", "TKT-1")
