from dataclasses import dataclass
from random import Random
from typing import TYPE_CHECKING
from uuid import UUID, uuid5

from compliance_ai.catalog import Catalog, Criterion, Policy

if TYPE_CHECKING:
    from compliance_ai.simulator import GeneratorConfig, Tenant


@dataclass(frozen=True)
class Case:
    id: UUID
    scenario_id: str
    criterion_id: str
    evidence: dict[str, bool | int | list[bool | int]]
    exclusion: str | None
    expected: str


def passing_values(criterion: Criterion, policy: Policy) -> dict[str, bool | int]:
    thresholds = {
        "training_completion_age_days": policy.training_max_age_days - 1,
        "training_score": policy.training_min_score,
        "screen_lock_seconds": policy.screen_lock_max_seconds,
    }
    return {key: thresholds.get(key, True) for key in criterion.required_evidence}


def build_cases(config: "GeneratorConfig", catalog: Catalog, tenant: "Tenant") -> list[Case]:
    criteria = {criterion.id: criterion for criterion in catalog.criteria}
    result = []
    random = Random(tenant.seed)
    for family in catalog.scenarios:
        if config.scenario_family_ids and family.id not in config.scenario_family_ids:
            continue
        probability = random.random()
        faults = ("fault", "conflict", "missing", "excluded")
        variants = (
            ("clean", *faults)
            if config.split == "demo"
            else (
                "clean",
                random.choice(faults) if probability < config.fault_rate else "clean",
            )
        )
        for index, variant in enumerate(variants):
            for criterion_id in family.criterion_ids:
                criterion = criteria[criterion_id]
                passing = passing_values(criterion, tenant.policy)
                facts: dict[str, bool | int | list[bool | int]] = dict(passing)
                exclusion = None
                expected = "COMPLIANT"
                if variant == "fault":
                    facts = {key: False if value is True else -1 for key, value in passing.items()}
                    expected = "NON_COMPLIANT"
                if variant == "missing":
                    facts.pop(next(iter(facts)))
                    expected = "INSUFFICIENT_EVIDENCE"
                if variant == "conflict":
                    key, value = next(iter(passing.items()))
                    facts[key] = [value, False if value is True else -1]
                    expected = "INSUFFICIENT_EVIDENCE"
                if variant == "excluded":
                    exclusion = "Ca mô phỏng ngoài phạm vi theo hồ sơ được phê duyệt."
                    expected = "NOT_APPLICABLE"
                identifier = uuid5(tenant.id, f"case/{family.id}/{criterion_id}/{index}")
                result.append(Case(identifier, family.id, criterion_id, facts, exclusion, expected))
    return result
