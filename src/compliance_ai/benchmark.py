from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from json import dumps
from os import getenv
from pathlib import Path
from time import monotonic
from typing import Literal
from urllib.error import URLError
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row
from sqlalchemy.engine import make_url

from compliance_ai.admin import privileged_connection
from compliance_ai.assessments import CaseValue, case_result, research_catalog
from compliance_ai.catalog import Policy
from compliance_ai.provider import ollama_predict
from compliance_ai.rules import Status

METHODS = ("M1", "M2", "M3", "M4")
VIOLATIONS = {Status.NON_COMPLIANT, Status.PARTIAL}
Mode = Literal["mock", "llm"]


@dataclass(frozen=True)
class BenchCase:
    id: UUID
    tenant: UUID
    scenario: str
    criterion: str
    document: dict
    facts: dict[str, CaseValue]
    observed_at: datetime
    exclusion: str | None


def load_inputs(split: str, limit: int, max_cases: int) -> list[BenchCase]:
    with privileged_connection() as connection, connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            """
            WITH tenants AS (
                SELECT DISTINCT company_id FROM app_data.sim_cases
                WHERE split=%s ORDER BY company_id LIMIT %s
            ), cases AS (
                SELECT c.*, p.document,
                row_number() OVER (PARTITION BY c.company_id ORDER BY c.id) AS seq
                FROM app_data.sim_cases c JOIN tenants t USING (company_id)
                JOIN app_data.policy_versions p ON (p.company_id,p.version) =
                    (c.company_id,c.policy_version) WHERE c.split=%s
            )
            SELECT id,company_id AS tenant,scenario_id AS scenario,criterion_id AS criterion,
                document,evidence AS facts,observed_at,exclusion_reason AS exclusion
            FROM cases WHERE seq<=%s ORDER BY tenant,seq
        """,
            (split, limit, split, max_cases),
        )
        return [BenchCase(**row) for row in cursor]


def independent_labels(identifiers: list[UUID]) -> dict[UUID, Status]:
    url = getenv("BENCHMARK_EVALUATOR_DATABASE_URL")
    if url:
        parsed = make_url(url).set(drivername="postgresql")
        if parsed.username != "compliance_evaluator":
            raise ValueError("Benchmark evaluator must use the compliance_evaluator role")
    else:
        migration = make_url(getenv("MIGRATION_DATABASE_URL", ""))
        parsed = migration.set(
            drivername="postgresql",
            username="compliance_evaluator",
            password=getenv("EVALUATOR_DB_PASSWORD"),
        )
    with psycopg.connect(parsed.render_as_string(hide_password=False), connect_timeout=4) as db:
        records = db.execute(
            """
            SELECT target_id,expected_status FROM benchmark_private.expected_results
            WHERE target_id = ANY(%s)
        """,
            (identifiers,),
        )
        return {identifier: Status(status) for identifier, status in records}


def score_predictions(pairs: list[tuple[Status, Status]]) -> dict[str, object]:
    tp = fp = tn = fn = 0
    matrix: Counter[str] = Counter()
    unknown = 0
    applicable = 0
    for expected, predicted in pairs:
        matrix[f"{expected}/{predicted}"] += 1
        if expected == Status.NA:
            continue
        applicable += 1
        unknown += predicted == Status.UNKNOWN
        if expected == Status.UNKNOWN:
            continue
        if expected in VIOLATIONS:
            tp += predicted in VIOLATIONS
            fn += predicted not in VIOLATIONS
        elif predicted in VIOLATIONS:
            fp += 1
        else:
            tn += 1

    def div(a: int, b: int) -> float | None:
        return a / b if b else None

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "confusion": dict(matrix),
        "precision": div(tp, tp + fp),
        "recall": div(tp, tp + fn),
        "f1": div(2 * tp, 2 * tp + fp + fn),
        "fpr": div(fp, fp + tn),
        "applicable": applicable,
        "unknown_predictions": unknown,
        "coverage": div(applicable - unknown, applicable),
        "action_metrics": None,
    }


def run_benchmark(
    mode: Mode,
    split: str,
    limit: int,
    max_cases: int,
    model: str,
    methods: tuple[str, ...],
) -> Path:
    if split not in ("dev", "test") or not 1 <= limit <= 100 or not 1 <= max_cases <= 165:
        raise ValueError("Invalid benchmark scope")
    if mode == "llm" and max_cases > 12:
        raise ValueError("Local model mode supports at most 12 cases per tenant")
    if not methods or not set(methods) <= set(METHODS) or len(set(methods)) != len(methods):
        raise ValueError("Use unique methods M1–M4")
    cases = load_inputs(split, limit, max_cases)
    if not cases:
        raise ValueError("Generate synthetic tenants before benchmarking")
    rubric = research_catalog()
    criteria = {criterion.id: criterion for criterion in rubric.criteria}
    control_names = {control.id: control.title for control in rubric.controls}
    rules = {
        case.id: case_result(
            criteria[case.criterion],
            Policy.model_validate(case.document),
            case.id,
            case.facts,
            case.observed_at,
            case.exclusion,
        ).status
        for case in cases
    }
    llm_outputs: dict[UUID, Status] = {}
    failures = []
    traces = []
    started = monotonic()
    by_tenant: dict[UUID, list[BenchCase]] = {}
    for item in cases:
        by_tenant.setdefault(item.tenant, []).append(item)
    for tenant, group in by_tenant.items():
        if mode == "mock":
            for item in group:
                llm_outputs[item.id] = (
                    Status.NA
                    if item.exclusion
                    else Status.NON_COMPLIANT
                    if any(value is False for value in item.facts.values())
                    else Status.COMPLIANT
                )
        elif any(method != "M1" for method in methods):
            payload = []
            for index, item in enumerate(group):
                criterion = criteria[item.criterion]
                payload.append(
                    {
                        "index": index,
                        "criteria": criterion.required_evidence,
                        "rubric_reference": {
                            ref: control_names[ref] for ref in criterion.control_ids
                        },
                        "limits": {key: item.document.get(key) for key in criterion.policy_keys},
                        "facts": item.facts,
                        "scope_exclusion": item.exclusion,
                    }
                )
            try:
                model_output, trace = ollama_predict(model, payload)
                llm_outputs.update(
                    {group[item.index].id: item.status for item in model_output.predictions}
                )
                traces.append({"tenant": str(tenant), **trace})
            except (URLError, ValueError, TimeoutError, KeyError, TypeError) as error:
                failures.append({"tenant": str(tenant), "error": type(error).__name__})
    predictions = {}
    for method in methods:
        outputs = {}
        for case in cases:
            proposed = llm_outputs.get(case.id, Status.UNKNOWN)
            if method == "M1":
                result = rules[case.id]
            elif method == "M4":
                result = rules[case.id] if rules[case.id] == proposed else Status.UNKNOWN
            else:
                result = proposed
            outputs[case.id] = result
        predictions[method] = outputs

    labels = independent_labels([case.id for case in cases])
    if set(labels) != {case.id for case in cases}:
        raise ValueError("Benchmark labels missing or outside selected snapshots")
    metrics = {
        method: score_predictions([(labels[case.id], outputs[case.id]) for case in cases])
        for method, outputs in predictions.items()
    }
    for method, outputs in predictions.items():
        metrics[method]["by_scenario"] = {
            scenario: score_predictions(
                [(labels[case.id], outputs[case.id]) for case in cases if case.scenario == scenario]
            )
            for scenario in sorted({case.scenario for case in cases})
        }
    root = Path("artifacts/benchmarks") / str(uuid4())
    root.mkdir(parents=True, exist_ok=False)

    def save_json(name: str, data: object) -> None:
        (root / name).write_text(dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def save_jsonl(name: str, data: list[dict]) -> None:
        (root / name).write_text("".join(dumps(item) + "\n" for item in data), encoding="utf-8")

    label = "MOCK_TEST_ONLY" if mode == "mock" else "OLLAMA_LOCAL_RESEARCH"
    save_json(
        "manifest.json",
        {
            "mode": label,
            "split": split,
            "methods": list(methods),
            "tenants": len(by_tenant),
            "cases": len(cases),
            "model": model if mode == "llm" else None,
            "generated_at": datetime.now(UTC).isoformat(),
            "duration_seconds": monotonic() - started,
            "provider_calls": traces,
            "failed_calls": len(failures),
            "policy_versions": sorted(
                set((case.document["id"], case.document["version"]) for case in cases)
            ),
            "scope": "structured detection only; M2/M3 share outputs; no action metrics",
            "m4_policy": "abstain on model/rule conflict",
            "generator_version": 1,
            "prompt_version": 1,
        },
    )
    save_json("metrics.json", metrics)
    save_jsonl(
        "cases.jsonl",
        [
            {
                "id": str(item.id),
                "tenant": str(item.tenant),
                "scenario": item.scenario,
                "criterion": item.criterion,
            }
            for item in cases
        ],
    )
    save_jsonl(
        "predictions.jsonl",
        [
            {"method": method, "id": str(identifier), "prediction": status}
            for method, outputs in predictions.items()
            for identifier, status in outputs.items()
        ],
    )
    save_jsonl("failures.jsonl", failures)
    columns = ("method", "precision", "recall", "f1", "fpr", "coverage")
    csv_rows = [",".join(columns)] + [
        ",".join(
            str(value) if value is not None else ""
            for value in (
                method,
                *(metrics[method][column] for column in columns[1:]),
            )
        )
        for method in predictions
    ]
    (root / "metrics.csv").write_text("\n".join(csv_rows) + "\n", encoding="utf-8")
    (root / "report.md").write_text(
        f"# Benchmark {label}\n\n{len(cases)} ca trên {len(by_tenant)} doanh nghiệp mô phỏng. "
        "Phạm vi đo là phát hiện có cấu trúc. M2 và M3 dùng chung dự đoán phát hiện. "
        "Chỉ số hành động chưa được đo. Phương pháp M4 từ chối kết luận khi mô hình và quy tắc "
        "mâu thuẫn. Không suy rộng kết quả sang dữ liệu hoặc người dùng thật.\n",
        encoding="utf-8",
    )
    return root
