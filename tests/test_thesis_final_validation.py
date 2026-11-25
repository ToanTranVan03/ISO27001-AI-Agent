"""Automated thesis validation suite verifying 56-control ISO 27001:2022 scope, AI Agent guardrails,
independent scenario handling, and end-to-end compliance & remediation invariants."""
import json
from pathlib import Path
import pytest
from agent_core.graph_builder import ControlEvaluationOutput, node_evaluate, node_verify
from backend import remediation
from evidence_collectors import source_intake, source_quality

ROOT = Path(__file__).resolve().parents[1]
CONTROLS_FILE = ROOT / "docs" / "56_controls_scope.json"
RUBRICS_FILE = ROOT / "docs" / "compliance_rubrics.json"


def test_iso27001_2022_56_controls_catalog_and_rubric_completeness():
    """Verifies Section II: exact 56 controls (8 A.6, 14 A.7, 34 A.8), unique IDs, 2022 numbering,
    valid pass_criteria, expected_evidence_types, and 1-to-1 rubric linkage."""
    controls = json.loads(CONTROLS_FILE.read_text(encoding="utf-8"))
    rubrics = json.loads(RUBRICS_FILE.read_text(encoding="utf-8"))
    assert len(controls) == 56
    ids = [c["control_id"] for c in controls]
    assert len(set(ids)) == 56
    assert set(ids) == set(rubrics.keys())

    expected_a6 = [f"A.6.{i}" for i in range(1, 9)]
    expected_a7 = [f"A.7.{i}" for i in range(1, 15)]
    expected_a8 = [f"A.8.{i}" for i in range(1, 35)]
    assert ids == expected_a6 + expected_a7 + expected_a8

    for c in controls:
        cid = c["control_id"]
        assert len(c["pass_criteria"]) >= 1
        assert len(c["expected_evidence_types"]) >= 1
        rubric = rubrics[cid]
        assert {"Compliant", "Partially Compliant", "Non-Compliant"} <= set(rubric.keys())
        assert all(isinstance(rubric[k], str) and len(rubric[k].strip()) >= 10 for k in ("Compliant", "Partially Compliant", "Non-Compliant"))


def test_ai_agent_zero_evidence_and_hallucinated_citation_guardrails():
    """Verifies Section III & IV: zero evidence short-circuits without calling LLM,
    hallucinated evidence_ids are rejected by node_verify, and representative lab captures
    cannot claim full-scope Compliant in user_evidence_only mode."""
    # 1. Zero evidence -> Insufficient Evidence without calling LLM
    empty_state = {
        "source_mode": "user_evidence_only",
        "company_evaluation": None,
        "control_id": "A.7.11",
        "control_name": "Supporting utilities",
        "objective": "",
        "collected_evidences": [],
        "deterministic_rule": {},
        "compliance_status": "UNKNOWN",
        "confidence": 0.0,
        "rationale": "",
        "audit_trail": [],
        "assessment_id": "test-aid",
        "validated_evidence_ids": [],
        "proposed_evidence_ids": [],
    }
    res_empty = node_verify(node_evaluate(empty_state))
    assert res_empty["compliance_status"] == "Insufficient Evidence"
    assert res_empty["confidence"] == 0.0
    assert "EVALUATE NO USER EVIDENCE; NO MODEL CALL" in res_empty["audit_trail"]

    # 2. Hallucinated evidence ID -> rejected by node_verify
    hallucinated_state = {
        "source_mode": "user_evidence_only",
        "collected_evidences": [{"evidence_id": "REAL-EV-01", "source": "upload-source://A.8.13/real.txt"}],
        "compliance_status": "Compliant",
        "confidence": 0.95,
        "rationale": "Model claimed compliant with fake ID",
        "proposed_evidence_ids": ["FAKE-HALLUCINATED-ID"],
        "validated_evidence_ids": [],
        "audit_trail": [],
    }
    res_hallucinated = node_verify(hallucinated_state)
    assert res_hallucinated["compliance_status"] == "Insufficient Evidence"
    assert res_hallucinated["confidence"] == 0.0
    assert "VERIFY (REJECTED UNKNOWN EVIDENCE IDS)" in res_hallucinated["audit_trail"]

    # 3. Representative lab capture in user_evidence_only mode -> downgraded to Insufficient Evidence
    rep_state = {
        "source_mode": "user_evidence_only",
        "collected_evidences": [{"evidence_id": "CAP-01", "source": "a8-capture://A.8.13/probe.json"}],
        "compliance_status": "Compliant",
        "confidence": 0.9,
        "rationale": "Representative probe passed",
        "proposed_evidence_ids": ["CAP-01"],
        "validated_evidence_ids": [],
        "audit_trail": [],
    }
    res_rep = node_verify(rep_state)
    assert res_rep["compliance_status"] == "Insufficient Evidence"
    assert "VERIFY REPRESENTATIVE LAB SCOPE; FULL CONTROL NOT ESTABLISHED" in res_rep["audit_trail"]


def test_source_quality_and_wrong_control_evidence_rejection():
    """Verifies Section IV Scenarios 7 & 9: wrong evidence type for control and corrupted/1-char/repeated files are blocked."""
    # Wrong evidence type for A.8.24 (Cryptography)
    with pytest.raises(ValueError, match="Control hoặc loại bằng chứng"):
        source_intake.prepare(
            "00000000-0000-4000-8000-000000000001", "A.8.24", "badge_log.txt",
            b"Physical entry badge swipe log " * 10, "EVID_PHY_ACCESS_LOG", "Building security desk",
        )

    # 1-character file and repeated garbage character file
    assert source_quality.text_quality("x")["usable"] is False
    assert source_quality.text_quality("A" * 400)["usable"] is False
    with pytest.raises(ValueError, match="Nguồn không phải văn bản dùng được"):
        source_intake.prepare(
            "00000000-0000-4000-8000-000000000001", "A.6.2", "one_char.txt",
            b"x", "EVID_PPL_CONTRACT_NDA", "HR department",
        )
