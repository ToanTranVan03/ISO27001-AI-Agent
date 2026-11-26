from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator

Pillar = Literal["people", "hardware", "software"]
Predicate = Literal["checklist", "training", "screen", "manual_review"]


class CatalogModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class Control(CatalogModel):
    id: str = Field(pattern=r"^A\.[5-8]\.\d+$")
    title: str = Field(min_length=1)
    primary_pillar: Pillar
    mappings: list[Pillar] = Field(min_length=1)


class Source(CatalogModel):
    source_type: Literal["research_rubric"]
    reference: str


class Criterion(CatalogModel):
    id: str = Field(pattern=r"^[HDMS]\d{2}$")
    control_ids: list[str] = Field(min_length=1)
    primary_pillar: Pillar
    target_type: Literal["employee", "account", "device", "media", "organization", "change"]
    applies_when: Literal["approved_policy_scope"]
    policy_keys: list[str]
    required_evidence: list[str] = Field(min_length=1)
    evidence_freshness_hours: int = Field(gt=0)
    predicate_or_rubric: Predicate
    status_mapping: Literal["verified_checks_v1"]
    severity: Literal["medium", "high"]
    read_tool: str
    allowed_actions: list[str] = Field(min_length=1)
    risk_class: Literal["low", "medium", "high"]
    verification_tool: str
    weight: float = Field(gt=0, allow_inf_nan=False)
    source_ref: Source
    version: int = Field(ge=1)


class Scenario(CatalogModel):
    id: str = Field(pattern=r"^SC-[HDS]\d{2}$")
    criterion_ids: list[str] = Field(min_length=1)


class Policy(CatalogModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]*$")
    version: int = Field(ge=1)
    training_max_age_days: int = Field(gt=0)
    training_min_score: int = Field(ge=0, le=100)
    screen_lock_max_seconds: int = Field(gt=0)
    termination_access_hours: int = Field(ge=0)
    asset_return_business_days: int = Field(ge=0)
    scope_exclusions: dict[str, str]

    @field_validator("scope_exclusions")
    @classmethod
    def require_rationale(cls, value: dict[str, str]) -> dict[str, str]:
        if any(not reason.strip() for reason in value.values()):
            raise ValueError("Loại trừ cần có lý do.")
        return value


class InterviewItem(CatalogModel):
    id: str
    weight: int = Field(gt=0, le=100)
    description: str


class InterviewRubric(CatalogModel):
    id: str
    version: int = Field(ge=1)
    language: Literal["vi"]
    source_type: Literal["research_rubric"]
    criteria: list[InterviewItem] = Field(min_length=1)
    initial: str
    retest: str
    ambiguous: Literal["human_review"]


class Catalog(CatalogModel):
    controls: list[Control]
    criteria: list[Criterion]
    scenarios: list[Scenario]
    policies: list[Policy]
    interview: InterviewRubric


def load_catalog(root: Path) -> Catalog:
    # Catalog files use the JSON subset of YAML, which keeps the loader dependency-free.
    catalog = Catalog(
        controls=TypeAdapter(list[Control]).validate_json((root / "controls.yaml").read_bytes()),
        criteria=TypeAdapter(list[Criterion]).validate_json((root / "criteria.yaml").read_bytes()),
        scenarios=TypeAdapter(list[Scenario]).validate_json((root / "scenarios.yaml").read_bytes()),
        policies=[
            Policy.model_validate_json(path.read_bytes())
            for path in sorted((root / "policies").glob("*.yaml"))
        ],
        interview=InterviewRubric.model_validate_json((root / "interview.yaml").read_bytes()),
    )
    check_catalog(catalog)
    return catalog


@lru_cache(maxsize=1)
def research_catalog() -> Catalog:
    return load_catalog(Path("configs"))


def check_catalog(catalog: Catalog) -> None:
    controls = {control.id: control for control in catalog.controls}
    criteria = {criterion.id: criterion for criterion in catalog.criteria}
    expected_scenarios = {
        f"SC-{pillar}{index:02}"
        for pillar, count in (("H", 12), ("D", 4), ("S", 4))
        for index in range(1, count + 1)
    }
    if len(controls) != 26 or len(catalog.controls) != len(controls):
        raise ValueError("Cần 26 mã tham chiếu duy nhất.")
    if len(criteria) != len(catalog.criteria):
        raise ValueError("Mã tiêu chí phải duy nhất.")
    if len(catalog.scenarios) != 20 or {s.id for s in catalog.scenarios} != expected_scenarios:
        raise ValueError("Danh mục kịch bản cần 12 nhóm con người, 4 phần cứng và 4 phần mềm.")
    used_controls: set[str] = set()
    for criterion in criteria.values():
        refs = set(criterion.control_ids)
        if not refs <= controls.keys() or criterion.source_ref.reference not in refs:
            raise ValueError(f"Tham chiếu không hợp lệ cho {criterion.id}.")
        if any(controls[ref].primary_pillar != criterion.primary_pillar for ref in refs):
            raise ValueError(f"Trụ cột chính không khớp ở {criterion.id}.")
        if not set(criterion.policy_keys) <= Policy.model_fields.keys():
            raise ValueError(f"Khóa chính sách không hợp lệ cho {criterion.id}.")
        used_controls.update(refs)
    mapped_criteria = {criterion for item in catalog.scenarios for criterion in item.criterion_ids}
    if used_controls != controls.keys() or mapped_criteria != criteria.keys():
        raise ValueError("Danh mục có liên kết thiếu hoặc không hợp lệ.")
    if len({(p.id, p.version) for p in catalog.policies}) != len(catalog.policies):
        raise ValueError("Phiên bản chính sách bị trùng.")
    if len({p.id for p in catalog.policies}) < 3:
        raise ValueError("Cần ABC và ít nhất hai hồ sơ chính sách so sánh.")
    if any(not p.scope_exclusions.keys() <= criteria.keys() for p in catalog.policies):
        raise ValueError("Mã tiêu chí loại trừ không tồn tại.")
    items = catalog.interview.criteria
    if len({item.id for item in items}) != len(items) or sum(i.weight for i in items) != 100:
        raise ValueError("Rubric phỏng vấn cần các mục duy nhất và tổng trọng số bằng 100.")
