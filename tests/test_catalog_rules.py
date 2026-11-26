from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from compliance_ai.catalog import load_catalog
from compliance_ai.rules import Instance, Observation, Outcome, Status, evaluate, score

ROOT = Path(__file__).resolve().parents[1]
CATALOG = load_catalog(ROOT / "configs")
CRITERIA = {item.id: item for item in CATALOG.criteria}
POLICY = next(item for item in CATALOG.policies if item.id == "abc")
NOW = datetime(2026, 11, 26, tzinfo=UTC)


def test_catalog_has_complete_reference_mapping() -> None:
    assert len(CATALOG.controls) == len(CATALOG.criteria) == 26
    assert len(CATALOG.scenarios) == 20
    assert {item.id for item in CATALOG.policies} == {"abc", "small", "regulated"}


def test_rule_uses_policy_version_and_fresh_evidence() -> None:
    criterion = CRITERIA["H03"]
    observations = [
        Observation("lesson", "training_completion_age_days", 365, NOW),
        Observation("grade", "training_score", 80, NOW),
    ]
    assert evaluate(criterion, POLICY, observations, NOW).status == Status.COMPLIANT
    revised = POLICY.model_copy(update={"version": 2, "training_min_score": 85})
    assert evaluate(criterion, revised, observations, NOW).status == Status.PARTIAL
    assert evaluate(criterion, POLICY, observations, NOW + timedelta(days=31)).status == (
        Status.UNKNOWN
    )
    observations.append(Observation("other-grade", "training_score", 65, NOW))
    assert evaluate(criterion, POLICY, observations, NOW).missing_evidence == ("training_score",)


def test_exclusion_requires_rationale_and_pending_verification_gives_unknown() -> None:
    criterion = CRITERIA["D02"]
    pending = Observation("ticket", "return_receipt", True, NOW, verified=False)
    assert evaluate(criterion, POLICY, [pending], NOW).status == Status.UNKNOWN
    excluded = POLICY.model_copy(update={"scope_exclusions": {"D02": "Chưa cấp thiết bị."}})
    result = evaluate(criterion, excluded, [], NOW)
    assert result.status == Status.NA
    assert result.rationale == "Chưa cấp thiết bị."
    with pytest.raises(ValueError, match="lý do"):
        type(POLICY).model_validate(POLICY.model_dump() | {"scope_exclusions": {"D02": " "}})


def test_manual_review_requires_evidence() -> None:
    assert evaluate(CRITERIA["D06"], POLICY, [], NOW).status == Status.UNKNOWN


def test_score_counts_shared_and_duplicate_instances_once() -> None:
    a = Instance(CRITERIA["M01"], "access-1", Outcome(Status.COMPLIANT))
    b = Instance(CRITERIA["M01"], "access-2", Outcome(Status.UNKNOWN))
    c = Instance(CRITERIA["D02"], "device-1", Outcome(Status.NON_COMPLIANT))
    d = Instance(CRITERIA["S04"], "device-1", Outcome(Status.PARTIAL))
    e = Instance(CRITERIA["D02"], "device-2", Outcome(Status.NA, rationale="Ngoài phạm vi."))
    result = score([a, a, b, c, d, e])
    assert result.pillars["people"].known_score == 100
    assert result.pillars["people"].coverage == 0.5
    assert result.pillars["people"].lower == 50
    assert result.pillars["people"].upper == 100
    assert result.weighted.applicable_count == 4
    assert result.weighted.unknown_count == 1
    assert result.weighted.known_score == 70
    assert result.weighted.lower == 40
    assert result.unweighted.coverage == pytest.approx(2.5 / 3)
    assert score([a]).weighted.known_score is None
    assert score([]).unweighted.coverage is None
    with pytest.raises(ValueError, match="Conflicting results"):
        score([a, Instance(a.criterion, a.target_id, Outcome(Status.NON_COMPLIANT))])
