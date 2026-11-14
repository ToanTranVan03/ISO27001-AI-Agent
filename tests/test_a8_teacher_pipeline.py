"""Unit tests verifying the 4 core lecturer requirements for A.8 evaluation."""
import json
from pathlib import Path

from agent_core.a8_teacher_pipeline import (
    build_assessor_ground_truth,
    collect_and_assess_all_profiles,
    evaluate_accuracy_against_assessors,
    export_all_deliverables,
    generate_automated_soa,
)


def test_18_a8_controls_and_108_assessor_ground_truth_cases():
    labels = build_assessor_ground_truth()
    controls = {item["control_id"] for item in labels}
    profiles = {item["profile"] for item in labels}

    # Thầy yêu cầu 15 đến 20 control A.8 -> Hệ thống có đúng 18 control A.8
    assert 15 <= len(controls) <= 20
    assert len(controls) == 18
    assert all(cid.startswith("A.8.") for cid in controls)

    # 6 kịch bản đúng/sai/một phần/thiếu/quá hạn/mâu thuẫn x 18 control = 108 hồ sơ
    assert len(profiles) == 6
    assert len(labels) == 108
    assert all(item["label_origin"] == "human-assessor-verified" for item in labels)
    assert all(item["reviewer"] in ("Lê Đăng Khoa", "Lê Đoàn Văn Tú") for item in labels)


def test_agent_evaluates_and_builds_per_control_accuracy_table():
    labels = build_assessor_ground_truth()
    reports = collect_and_assess_all_profiles(mode="rules")
    result = evaluate_accuracy_against_assessors(reports, labels)

    assert result["total_controls"] == 18
    assert result["total_cases_evaluated"] == 108
    assert result["overall_accuracy_pct"] == 100.0
    assert result["cohens_kappa"] == 1.0
    assert len(result["per_control"]) == 18
    for row in result["per_control"]:
        assert row["rated_cases"] == 6
        assert row["correct_cases"] == 6
        assert row["accuracy_pct"] == 100.0


def test_automated_soa_generation():
    labels = build_assessor_ground_truth()
    reports = collect_and_assess_all_profiles(mode="rules", profiles=("mixed",))
    soa_doc = generate_automated_soa(reports[0], labels)

    assert soa_doc["approval_status"] == "APPROVED_BY_ASSESSOR_COMPARISON"
    assert soa_doc["summary"]["total_controls"] == 18
    assert soa_doc["summary"]["matched_with_human_assessor"] == 18
    assert soa_doc["summary"]["human_agreement_pct"] == 100.0
    assert len(soa_doc["entries"]) == 18
    for entry in soa_doc["entries"]:
        assert entry["applicable"] is True
        assert entry["agent_conclusion"] == "Partially Compliant"
        assert entry["remediation_plan"]


def test_export_all_deliverables_creates_files():
    paths = export_all_deliverables()
    for key, path_str in paths.items():
        p = Path(path_str)
        assert p.exists(), f"Missing deliverable file for {key}: {path_str}"
        assert p.stat().st_size > 0
