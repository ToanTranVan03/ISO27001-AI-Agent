"""Unit tests for Phase 5: 4-Model Ablation Benchmark, Metric Formulas, Ground Truth Isolation & CSV/JSON Export."""
import csv
import json

import pytest

from benchmark.ablation_runner import (
    compute_binary_metrics,
    export_benchmark_results,
    prepare_benchmark_corpus,
    run_ablation_benchmark,
)
from benchmark.models import clone_store_without_ground_truth


def test_metric_formulas_and_physical_ground_truth_isolation():
    metrics = compute_binary_metrics(tp=80, fp=20, fn=10, tn=90)
    assert metrics["precision"] == 0.8
    assert metrics["recall"] == round(80 / 90, 4)
    assert metrics["f1_score"] == round(2 * 0.8 * (80 / 90) / (0.8 + 80 / 90), 4)
    assert metrics["fpr"] == round(20 / 110, 4)

    # Verify >= 25 enterprise requirement
    with pytest.raises(ValueError):
        prepare_benchmark_corpus(count=10)

    master = prepare_benchmark_corpus(count=25, seed=2026)
    cloned = clone_store_without_ground_truth(master)
    for comp in cloned.list_companies():
        cid = comp["company_id"]
        assert cloned.get_ground_truth(cid, evaluator_token="BENCHMARK_EVALUATOR_ONLY") == {}
        assert len(master.get_ground_truth(cid, evaluator_token="BENCHMARK_EVALUATOR_ONLY")) > 0


def test_ablation_4_models_m4_outperforms_m1_m2_m3_and_exports_csv_json(tmp_path):
    report = run_ablation_benchmark(enterprise_count=25, seed=2026, use_live_ollama=False)
    assert report["enterprise_count"] == 25

    by_model = {row["model_name"]: row for row in report["summary"]}
    assert set(by_model.keys()) == {
        "M1_RuleBased",
        "M2_LLM_RAG",
        "M3_Agent_Tools",
        "M4_Proposed_ClosedLoop",
    }

    m1 = by_model["M1_RuleBased"]
    m2 = by_model["M2_LLM_RAG"]
    m3 = by_model["M3_Agent_Tools"]
    m4 = by_model["M4_Proposed_ClosedLoop"]

    # M4 (Proposed Closed-Loop) must achieve higher F1-score than M1, M2, and M3
    assert m4["f1_score"] > m1["f1_score"]
    assert m4["f1_score"] > m2["f1_score"]
    assert m4["f1_score"] > m3["f1_score"]

    # M4 must achieve strictly lower False Remediation Rate than M3 (which lacks Risk Gate & Verification)
    assert m3["false_remediation_rate"] > 0.0
    assert m4["false_remediation_rate"] < m3["false_remediation_rate"]
    assert m4["false_remediation_rate"] == 0.0

    # M1 and M2 perform zero remediation actions, while M4 achieves high Remediation Success Rate
    assert m1["remediation_success_rate"] == 0.0
    assert m2["remediation_success_rate"] == 0.0
    assert m4["remediation_success_rate"] > m3["remediation_success_rate"]
    assert m4["remediation_success_rate"] >= 0.95

    # Export to JSON and CSV and validate contents
    paths = export_benchmark_results(report, tmp_path)
    loaded_json = json.loads(open(paths["json_path"], encoding="utf-8").read())
    assert len(loaded_json["summary"]) == 4

    with open(paths["csv_path"], encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 4
    assert rows[3]["model_name"] == "M4_Proposed_ClosedLoop"
