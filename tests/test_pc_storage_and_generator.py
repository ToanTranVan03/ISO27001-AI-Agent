"""Unit tests for Phase 1: Multi-tenant PC storage, catalogs, 4 canonical scenarios, and Enterprise Generator."""
import pytest

from backend.pc_storage import (
    COMPLIANCE_STATES,
    CLOSED_LOOP_STAGES,
    InMemoryPCStore,
    SCHEMA_STATEMENTS,
    load_iso_knowledge_base,
    load_pc_controls,
)
from simulation.enterprise_generator import generate_multi_enterprise_dataset
from simulation.scenarios import seed_canonical_company


def test_catalogs_and_schema_completeness():
    controls = load_pc_controls()
    control_ids = {c["control_id"] for c in controls}
    required = {
        "A.5.9", "A.5.11", "A.5.16", "A.5.18",
        "A.6.1", "A.6.2", "A.6.3", "A.6.4", "A.6.5", "A.6.6", "A.6.7", "A.6.8",
        "A.7.7", "A.7.9", "A.7.10", "A.7.14",
        "A.8.1", "A.8.2", "A.8.5", "A.8.7", "A.8.8", "A.8.9", "A.8.15", "A.8.19", "A.8.24", "A.8.32",
    }
    assert required.issubset(control_ids)
    assert len(COMPLIANCE_STATES) == 6
    assert len(CLOSED_LOOP_STAGES) == 8
    assert len(SCHEMA_STATEMENTS) == 10

    kb = load_iso_knowledge_base()
    standards = {chunk["standard_ref"] for chunk in kb}
    assert "ISO/IEC 27001:2022" in standards
    assert "ISO/IEC 27002:2022" in standards
    assert "ISO/IEC 27007:2020" in standards


def test_canonical_company_embeds_all_four_scenarios_precisely():
    store = InMemoryPCStore()
    seed_canonical_company(store, company_id="COMP-CANONICAL-01")

    # Scenario 1 (A.8.8): 10 PCs, 7/10 compliant, 3 missing patches (PC-03, PC-06, PC-09)
    pcs = [d for d in store.list_devices("COMP-CANONICAL-01") if d["device_id"].startswith("PC-")]
    assert len(pcs) == 10
    unpatched = sorted(d["device_id"] for d in pcs if not d["patch_compliant"])
    assert unpatched == ["PC-03", "PC-06", "PC-09"]

    # Scenario 2 (A.8.9): PC-02 fails 4/6 baseline criteria, passes Antivirus & NTP
    pc02 = store.list_devices("COMP-CANONICAL-01", device_ids=["PC-02"])[0]
    assert pc02["firewall_enabled"] is False
    assert pc02["screen_lock_minutes"] == 30
    assert pc02["disk_encrypted"] is False
    assert pc02["password_policy_ok"] is False
    assert pc02["antivirus_active"] is True
    assert pc02["ntp_synced"] is True

    # Scenario 3 (People - 50 employees): 35/50 training, 45/50 NDA, 38/50 MFA, 30/50 incident, 32/50 phishing
    employees = store.list_employees("COMP-CANONICAL-01")
    assert len(employees) == 50
    assert sum(1 for e in employees if e["training_completed"]) == 35
    assert sum(1 for e in employees if e["nda_signed"]) == 45
    assert sum(1 for e in employees if e["incident_process_known"]) == 30
    assert sum(1 for e in employees if e["phishing_passed"]) == 32
    ad_accounts = store.list_accounts("COMP-CANONICAL-01", systems=["active_directory"])
    assert len(ad_accounts) == 50
    assert sum(1 for a in ad_accounts if a["mfa_enabled"]) == 38

    # Scenario 4 (Cross-Domain NV015 - Phòng Kế toán)
    nv015 = store.list_employees("COMP-CANONICAL-01", employee_id="NV015")[0]
    assert nv015["department"] == "Phòng Kế toán"
    assert nv015["employment_status"] == "terminated"
    nv015_accs = store.list_accounts("COMP-CANONICAL-01", employee_id="NV015")
    assert {a["system_type"] for a in nv015_accs if a["is_active"]} == {
        "active_directory", "vpn", "email", "accounting_app"
    }
    lt = store.list_devices("COMP-CANONICAL-01", employee_id="NV015")[0]
    assert lt["device_id"] == "LT-NV015"
    assert lt["returned_to_it"] is False
    assert lt["badge_card_active"] is True


def test_multi_enterprise_generator_and_ground_truth_isolation():
    store = InMemoryPCStore()
    companies = generate_multi_enterprise_dataset(store, count=25, seed=2026)
    assert len(companies) == 25
    assert len(store.list_companies()) == 25

    tiers = {c["size_tier"] for c in companies}
    assert tiers == {"small", "medium", "enterprise"}

    # Strict Ground Truth Isolation: agent without benchmark token is rejected
    with pytest.raises(PermissionError):
        store.get_ground_truth("COMP-001", evaluator_token="AGENT_RUNTIME")

    # Benchmark evaluator can inspect Ground Truth and verify coverage of compliance states
    observed_gt_statuses = set()
    for c in companies:
        gt = store.get_ground_truth(c["company_id"], evaluator_token="BENCHMARK_EVALUATOR_ONLY")
        for item in gt.values():
            observed_gt_statuses.add(item["expected_status"])
    assert {"Compliant", "Partial", "Non-compliant", "Insufficient Evidence", "Not Applicable"}.issubset(
        observed_gt_statuses
    )

    # Tenant isolation: employees of COMP-001 never leak into COMP-002
    e1 = store.list_employees("COMP-001")
    e2 = store.list_employees("COMP-002")
    assert all(e["company_id"] == "COMP-001" for e in e1)
    assert all(e["company_id"] == "COMP-002" for e in e2)
