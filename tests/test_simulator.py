from pathlib import Path

from compliance_ai.catalog import load_catalog
from compliance_ai.rules import Observation, evaluate
from compliance_ai.scenarios import build_cases
from compliance_ai.simulator import CLOCK, GeneratorConfig, generate


def test_deterministic_generator_has_50_abc_and_25_holdout_tenants() -> None:
    catalog = load_catalog(Path("configs"))
    demo = generate(GeneratorConfig(42, 1, None, "demo"), catalog)[0]
    assert len(demo.employees) == 50 and "NV015" in demo.employees
    config = GeneratorConfig(2026, 25, None, "test")
    tenants = generate(config, catalog)
    assert tenants == generate(config, catalog)
    assert len({tenant.id for tenant in tenants}) == 25
    assert {len(tenant.employees) for tenant in tenants} == {10, 50, 200}
    assert tenants != generate(GeneratorConfig(2026, 25, None, "dev"), catalog)


def test_labeled_fixtures_match_rubric_with_clean_missing_conflict_and_exclusion() -> None:
    catalog = load_catalog(Path("configs"))
    config = GeneratorConfig(42, 1, None, "demo")
    tenant = generate(config, catalog)[0]
    cases = build_cases(config, catalog, tenant)
    assert len({case.scenario_id for case in cases}) == 20
    assert cases == build_cases(config, catalog, tenant)
    criteria = {criterion.id: criterion for criterion in catalog.criteria}
    for case in cases:
        policy = tenant.policy
        if case.exclusion:
            policy = policy.model_copy(
                update={
                    "scope_exclusions": {
                        case.criterion_id: case.exclusion,
                    }
                }
            )
        observations = [
            Observation(f"{key}/{index}", key, value, CLOCK)
            for key, values in case.evidence.items()
            for index, value in enumerate(values if isinstance(values, list) else [values])
        ]
        assert evaluate(criteria[case.criterion_id], policy, observations, CLOCK).status == (
            case.expected
        )
