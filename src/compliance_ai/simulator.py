from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from json import dumps
from pathlib import Path
from random import Random
from typing import Literal
from uuid import NAMESPACE_URL, UUID, uuid5

from psycopg.types.json import Jsonb

from compliance_ai.admin import demo_id, privileged_connection
from compliance_ai.catalog import Catalog, Policy, load_catalog

CLOCK = datetime(2026, 1, 1, tzinfo=UTC)
Split = Literal["demo", "dev", "test"]
KINDS = ("account", "asset", "endpoint", "training")
INDUSTRIES = ("technology", "logistics", "education")


@dataclass(frozen=True)
class GeneratorConfig:
    seed: int
    company_count: int
    employee_count: int | None
    split: Split
    observation_time: datetime = CLOCK
    industry_profile: str | None = None
    maturity_profile: str | None = None
    policy_profile: str | None = None
    scenario_family_ids: tuple[str, ...] = ()
    fault_rate: float = 0.4

    def __post_init__(self) -> None:
        if not 1 <= self.company_count <= 100:
            raise ValueError("company_count must be 1–100")
        minimum = 15 if self.split == "demo" else 1
        if self.employee_count is not None and not minimum <= self.employee_count <= 200:
            raise ValueError(f"employee_count must be {minimum}–200")
        if self.observation_time.utcoffset() is None or not 0 <= self.fault_rate <= 1:
            raise ValueError("Use a timezone-aware clock and a fault rate between zero and one")
        if self.split == "demo" and self.company_count != 1:
            raise ValueError("The ABC demo uses one company")


@dataclass(frozen=True)
class Tenant:
    id: UUID
    name: str
    seed: int
    employees: tuple[str, ...]
    policy: Policy
    industry: str
    maturity: str


def generate(config: GeneratorConfig, catalog: Catalog) -> list[Tenant]:
    policies = {policy.id: policy for policy in catalog.policies}
    results = []
    for index in range(config.company_count):
        key = f"compliance-ai/generator/v1/{config.split}/{config.seed}/{index}"
        seed = int.from_bytes(sha256(key.encode()).digest()[:8], "big")
        random = Random(seed)
        is_demo = config.split == "demo"
        tenant_id = demo_id("abc") if is_demo else uuid5(NAMESPACE_URL, key)
        industry = config.industry_profile or random.choice(INDUSTRIES)
        maturity = config.maturity_profile or random.choice(("emerging", "established", "advanced"))
        profile = config.policy_profile or ("abc" if is_demo else random.choice(sorted(policies)))
        count = config.employee_count or (50 if is_demo else random.choice((10, 50, 200)))
        name = "ABC Technology (mô phỏng)" if is_demo else f"Doanh nghiệp mô phỏng {index + 1:03}"
        results.append(
            Tenant(
                tenant_id,
                name,
                seed,
                tuple(f"NV{i:03}" for i in range(1, count + 1)),
                policies[profile],
                industry,
                maturity,
            )
        )
    return results


def employee_id(tenant: UUID, code: str) -> UUID:
    return demo_id(f"abc/{code}") if tenant == demo_id("abc") else uuid5(tenant, code)


def resource_state(kind: str, offboarded: bool, random: Random) -> dict[str, object]:
    if kind == "account":
        return {
            "enabled": True,
            "mfa_registered": not offboarded,
            "mfa_enforced": not offboarded,
            "grants": ["AD", "VPN", "APP"] if offboarded else ["APP"],
            "protected": False,
        }
    if kind == "asset":
        return {"returned": False, "return_receipt": None, "custody": "employee"}
    if kind == "endpoint":
        return {
            "screen_lock_seconds": random.choice((120, 180, 300)),
            "firewall": True,
            "malware_protection": True,
            "patches": ["SIM-001"],
            "encrypted": True,
        }
    if kind == "training":
        return {"nda_signed": not offboarded, "assignment": None}
    raise ValueError(f"Unknown resource: {kind}")


def persist(config: GeneratorConfig, root: Path = Path("configs")) -> dict[str, object]:
    from compliance_ai.scenarios import build_cases

    catalog = load_catalog(root)
    tenants = generate(config, catalog)
    case_count = 0
    with privileged_connection() as connection, connection.cursor() as cursor:
        for tenant in tenants:
            cursor.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (str(tenant.id),))
            cursor.execute(
                """
                INSERT INTO app_data.companies (id, name, synthetic)
                VALUES (%s, %s, true) ON CONFLICT (id) DO NOTHING
            """,
                (tenant.id, tenant.name),
            )
            cursor.execute(
                """
                INSERT INTO app_data.policy_versions (company_id, version, effective_at, document)
                VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING
            """,
                (
                    tenant.id,
                    tenant.policy.version,
                    config.observation_time,
                    Jsonb(tenant.policy.model_dump()),
                ),
            )
            people = []
            resources = []
            random = Random(tenant.seed)
            for code in tenant.employees:
                actor = employee_id(tenant.id, code)
                offboarded = code == "NV015"
                status = "terminated" if offboarded else "transfer" if code == "NV010" else "active"
                people.append(
                    (
                        tenant.id,
                        actor,
                        code,
                        f"Nhân viên mô phỏng {code}",
                        status,
                        config.observation_time if offboarded else None,
                    )
                )
                for kind in KINDS:
                    resources.append(
                        (
                            tenant.id,
                            uuid5(actor, kind),
                            actor,
                            kind,
                            Jsonb(resource_state(kind, offboarded, random)),
                            config.observation_time,
                        )
                    )
            cursor.executemany(
                """
                INSERT INTO app_data.employees
                    (company_id,id,code,display_name,employment_status,termination_effective_at)
                    VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (company_id,id) DO NOTHING
            """,
                people,
            )
            cursor.executemany(
                """
                INSERT INTO app_data.sim_resources
                    (company_id,id,employee_id,kind,state,updated_at)
                    VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (company_id,id) DO NOTHING
            """,
                resources,
            )
            cases = build_cases(config, catalog, tenant)
            case_count += len(cases)
            cursor.executemany(
                """
                INSERT INTO app_data.sim_cases
                    (company_id,id,scenario_id,policy_version,criterion_id,observed_at,
                     evidence,exclusion_reason,split)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING
            """,
                [
                    (
                        tenant.id,
                        case.id,
                        case.scenario_id,
                        tenant.policy.version,
                        case.criterion_id,
                        config.observation_time,
                        Jsonb(case.evidence),
                        case.exclusion,
                        config.split,
                    )
                    for case in cases
                ],
            )
            cursor.executemany(
                """
                INSERT INTO benchmark_private.expected_results
                    (id,company_id,scenario_id,criterion_id,target_id,expected_status)
                    VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING
            """,
                [
                    (
                        uuid5(case.id, "oracle"),
                        tenant.id,
                        case.scenario_id,
                        case.criterion_id,
                        case.id,
                        case.expected,
                    )
                    for case in cases
                ],
            )
    manifest = {
        "mode": "SIMULATION",
        "generator_version": 1,
        "seed": config.seed,
        "split": config.split,
        "observed_at": config.observation_time.isoformat(),
        "case_count": case_count,
        "tenants": [
            {
                "id": str(t.id),
                "employees": len(t.employees),
                "seed": t.seed,
                "industry": t.industry,
                "maturity": t.maturity,
                "policy": t.policy.id,
            }
            for t in tenants
        ],
    }
    manifest["digest"] = sha256(dumps(manifest, sort_keys=True).encode()).hexdigest()
    return manifest
