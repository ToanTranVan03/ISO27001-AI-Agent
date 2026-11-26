from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from compliance_ai.catalog import Criterion, Pillar, Policy


class Status(StrEnum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    PARTIAL = "PARTIAL"
    UNKNOWN = "INSUFFICIENT_EVIDENCE"
    NA = "NOT_APPLICABLE"


@dataclass(frozen=True)
class Observation:
    id: str
    key: str
    value: bool | int
    observed_at: datetime
    valid_until: datetime | None = None
    verified: bool = True


@dataclass(frozen=True)
class Outcome:
    status: Status
    evidence_ids: tuple[str, ...] = ()
    missing_evidence: tuple[str, ...] = ()
    rationale: str = ""


def evaluate(
    criterion: Criterion,
    policy: Policy,
    observations: list[Observation],
    now: datetime,
) -> Outcome:
    exclusion = policy.scope_exclusions.get(criterion.id)
    if exclusion:
        return Outcome(Status.NA, rationale=exclusion)
    if now.utcoffset() is None:
        raise ValueError("Clock must include a timezone")
    required = set(criterion.required_evidence)
    groups: dict[str, list[Observation]] = defaultdict(list)
    for item in observations:
        if item.key not in required or not item.verified:
            continue
        if item.observed_at.utcoffset() is None or (
            item.valid_until is not None and item.valid_until.utcoffset() is None
        ):
            raise ValueError("Observation timestamps must include a timezone")
        valid = now - timedelta(hours=criterion.evidence_freshness_hours) <= item.observed_at <= now
        if valid and (item.valid_until is None or now < item.valid_until):
            groups[item.key].append(item)
    usable = tuple(sorted({item.id for items in groups.values() for item in items}))
    numeric_bounds = {}
    if criterion.predicate_or_rubric == "training":
        numeric_bounds = {
            "training_completion_age_days": (0, policy.training_max_age_days),
            "training_score": (policy.training_min_score, 100),
        }
    elif criterion.predicate_or_rubric == "screen":
        numeric_bounds = {"screen_lock_seconds": (1, policy.screen_lock_max_seconds)}
    missing = []
    checks = []
    for key in criterion.required_evidence:
        values = {(type(item.value), item.value) for item in groups[key]}
        if len(values) != 1:
            missing.append(key)
            continue
        kind, value = next(iter(values))
        if key in numeric_bounds and kind is int:
            low, high = numeric_bounds[key]
            checks.append(low <= value <= high)
        elif key not in numeric_bounds and kind is bool:
            checks.append(bool(value))
        else:
            missing.append(key)
    if missing:
        rationale = "Thiếu bằng chứng còn hiệu lực, đúng kiểu hoặc nhất quán."
        if criterion.predicate_or_rubric == "manual_review":
            rationale = "Cần biên bản thẩm định do người có thẩm quyền xác nhận."
        return Outcome(Status.UNKNOWN, usable, tuple(missing), rationale)
    if all(checks):
        return Outcome(Status.COMPLIANT, usable, rationale="Các kiểm tra bằng chứng đều đạt.")
    if any(checks):
        return Outcome(Status.PARTIAL, usable, rationale="Một phần kiểm tra bằng chứng đạt.")
    return Outcome(Status.NON_COMPLIANT, usable, rationale="Kiểm tra bằng chứng không đạt.")


@dataclass(frozen=True)
class Instance:
    criterion: Criterion
    target_id: str
    outcome: Outcome


@dataclass(frozen=True)
class Score:
    known_score: float | None
    coverage: float | None
    lower: float | None
    upper: float | None
    applicable_count: int
    unknown_count: int


@dataclass(frozen=True)
class Scores:
    pillars: dict[Pillar, Score]
    unweighted: Score
    weighted: Score


POINTS = {Status.COMPLIANT: 1.0, Status.PARTIAL: 0.5, Status.NON_COMPLIANT: 0.0}
PILLAR_WEIGHTS: dict[Pillar, float] = {"people": 0.6, "hardware": 0.2, "software": 0.2}


def aggregate(groups: list[list[Instance]], use_weights: bool) -> Score:
    applicable = unknown = 0
    total_weight = known_weight = points = 0.0
    for group in groups:
        relevant = [item for item in group if item.outcome.status != Status.NA]
        if not relevant:
            continue
        group_weight = group[0].criterion.weight if use_weights else 1.0
        per_target = group_weight / len(relevant)
        applicable += len(relevant)
        total_weight += group_weight
        for item in relevant:
            result = POINTS.get(item.outcome.status)
            if result is None:
                unknown += 1
            else:
                known_weight += per_target
                points += per_target * result
    if not total_weight:
        return Score(None, None, None, None, 0, 0)
    coverage = known_weight / total_weight if unknown else 1.0
    return Score(
        100 * points / known_weight if known_weight else None,
        coverage,
        min(100.0, 100 * points / total_weight),
        min(100.0, 100 * (points / total_weight + 1 - coverage)),
        applicable,
        unknown,
    )


def score(instances: list[Instance]) -> Scores:
    unique: dict[tuple[str, str], Instance] = {}
    groups: dict[str, list[Instance]] = defaultdict(list)
    for item in instances:
        key = (item.criterion.id, item.target_id)
        if key in unique and unique[key] != item:
            raise ValueError("Conflicting results for the same criterion and target")
        unique[key] = item
    for item in unique.values():
        groups[item.criterion.id].append(item)
    if any(item.criterion != group[0].criterion for group in groups.values() for item in group):
        raise ValueError("Mixed revisions or criteria in the same score")
    pillars = {
        pillar: aggregate(
            [group for group in groups.values() if group[0].criterion.primary_pillar == pillar],
            use_weights=True,
        )
        for pillar in PILLAR_WEIGHTS
    }
    unweighted = aggregate(list(groups.values()), use_weights=False)

    def combine(values: dict[Pillar, float | None]) -> float | None:
        if any(value is None for value in values.values()):
            return None
        return sum(
            PILLAR_WEIGHTS[pillar] * value for pillar, value in values.items() if value is not None
        )

    weighted = Score(
        combine({key: value.known_score for key, value in pillars.items()}),
        combine({key: value.coverage for key, value in pillars.items()}),
        combine({key: value.lower for key, value in pillars.items()}),
        combine({key: value.upper for key, value in pillars.items()}),
        unweighted.applicable_count,
        unweighted.unknown_count,
    )
    return Scores(pillars, unweighted, weighted)
