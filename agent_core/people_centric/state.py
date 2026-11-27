"""Shared state, 6 compliance statuses, 8 closed-loop stages, and Pydantic schemas."""
from __future__ import annotations

from typing import Any, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, ConfigDict, Field

ComplianceStatus = Literal[
    "Compliant",
    "Non-compliant",
    "Partial",
    "Insufficient Evidence",
    "Not Applicable",
    "Pending Remediation",
]

ClosedLoopStage = Literal[
    "Observe",
    "Assess",
    "Detect",
    "Plan",
    "Act",
    "Verify",
    "Report",
    "Monitor",
]

PillarType = Literal["human", "hardware", "software", "cross_domain"]


class SLMAssessmentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: ComplianceStatus
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(min_length=5, max_length=2500)


class SLMPlannedCall(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_name: str = Field(min_length=3, max_length=64)
    params: dict[str, Any]
    description: str = Field(default="", max_length=500)


class SLMToolPlanOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actions: list[SLMPlannedCall] = Field(default_factory=list, max_length=20)


class InterviewGradeOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    score: float = Field(ge=0.0, le=10.0)
    passed: bool
    feedback: str = Field(min_length=5, max_length=2000)
    detected_concepts: list[str] = Field(default_factory=list)


class SupervisorState(TypedDict, total=False):
    assessment_run_id: str
    company_id: str
    control_id: str
    pillar: PillarType
    use_llm: bool
    auto_remediate: bool
    require_medium_approval: bool
    dry_run: bool
    max_remediation_retries: int
    remediation_attempts: int
    current_stage: ClosedLoopStage
    stage_history: list[str]
    rag_context: list[dict[str, Any]]
    prompt_injection_alerts: list[str]
    observations: dict[str, Any]
    evidence_refs: list[dict[str, Any]]
    compliance_status: ComplianceStatus
    initial_status: ComplianceStatus
    confidence: float
    findings: list[dict[str, Any]]
    rationale: str
    planned_actions: list[dict[str, Any]]
    executed_actions: list[dict[str, Any]]
    pending_approval_action_ids: list[str]
    verification_passed: bool
    verification_summary: str
    needs_retry: bool
    final_report: dict[str, Any]
    monitoring_schedule: dict[str, Any]
    token_usage: dict[str, int]
    llm_execution_log: list[str]
