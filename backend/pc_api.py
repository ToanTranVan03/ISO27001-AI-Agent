"""FastAPI endpoints for the People-Centric ISO/IEC 27001:2022 compliance system.

All routes require a Bearer session (same auth as the rest of the API). Decisions on remediation actions,
data generation, interview verification and benchmark runs are admin-only. Synthetic enterprises are demo data
and are not mapped to platform campaigns, so tenant isolation here is by `company_id` inside the tool registry.
"""
from __future__ import annotations

import os
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from backend.pc_service import ConflictError, PCService
from backend.pc_storage import BasePCStore, InMemoryPCStore
from backend.team_api import require_user
from tools.registry import ToolSecurityError

router = APIRouter(prefix="/api/pc", tags=["People-centric compliance"])

_service: PCService | None = None


def _build_default_store() -> BasePCStore:
    if not os.getenv("DATABASE_URL") and os.getenv("POSTGRES_URL"):
        os.environ["DATABASE_URL"] = os.environ["POSTGRES_URL"]
    mode = os.getenv("PC_STORAGE", "auto").lower()
    if mode == "memory":
        return InMemoryPCStore()
    if mode == "postgres":
        from backend.pc_storage import PostgresPCStore, initialize_pc_schema

        initialize_pc_schema()
        return PostgresPCStore()
    # mode == "auto": prefer real PostgreSQL pc_* tables whenever DATABASE_URL is reachable
    if os.getenv("DATABASE_URL"):
        try:
            from backend.pc_storage import PostgresPCStore, initialize_pc_schema

            initialize_pc_schema()
            return PostgresPCStore()
        except Exception:
            pass
    return InMemoryPCStore()


def initialize_on_startup() -> None:
    """Called from backend.main lifespan to ensure pc_* schema & active store are initialized."""
    get_service()


def get_service() -> PCService:
    global _service
    if _service is None:
        _service = PCService(_build_default_store())
    return _service


def set_service(service: PCService | None) -> None:
    """Replace the process-wide service (tests / embedding)."""
    global _service
    _service = service


def require_admin_user(user: dict = Depends(require_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(403, detail="Chỉ quản trị viên được thực hiện thao tác này.")
    return user


def _call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except KeyError as exc:
        raise HTTPException(404, detail=str(exc.args[0]) if exc.args else "Không tìm thấy.") from exc
    except ConflictError as exc:
        raise HTTPException(409, detail=str(exc)) from exc
    except ToolSecurityError as exc:
        raise HTTPException(403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(502, detail=f"Lỗi thực thi hạ tầng: {exc}") from exc


class GenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    count: int = Field(default=25, ge=1, le=100)
    seed: int = 2026
    include_canonical: bool = True


class AssessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    controls: list[str] | None = Field(default=None, max_length=40)
    auto_remediate: bool = True
    use_llm: bool = False
    dry_run: bool = False
    execution_mode: Literal["simulation", "hybrid_lab"] | None = None
    require_medium_approval: bool = False
    max_remediation_retries: int = Field(default=2, ge=0, le=5)


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company_id: str = Field(min_length=3, max_length=64)
    decision: Literal["APPROVE", "REJECT"]
    reason: str = Field(default="", max_length=1000)
    assessment_run_id: str | None = Field(default=None, max_length=64)
    execution_mode: Literal["simulation", "hybrid_lab"] | None = None


class InterviewStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company_id: str = Field(min_length=3, max_length=64)
    employee_id: str = Field(min_length=2, max_length=64)
    control_id: Literal["A.6.8", "A.6.3"] = "A.6.8"


class InterviewSubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company_id: str = Field(min_length=3, max_length=64)
    answers: list[str] = Field(min_length=1, max_length=10)
    use_llm: bool = False


class InterviewVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company_id: str = Field(min_length=3, max_length=64)
    confirmed_passed: bool


class BenchmarkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enterprise_count: int = Field(default=25, ge=25, le=60)
    seed: int = 2026
    use_live_ollama: bool = False


@router.get("/status")
def runtime_status(user: dict = Depends(require_user)):
    svc = get_service()
    return {
        "storage_backend": svc.store.__class__.__name__,
        "ollama_host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        "ollama_model": os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
        "hybrid_lab_enabled": os.getenv("ISO_LAB_ENABLE_REAL") == "1",
    }


@router.get("/companies")
def list_companies(user: dict = Depends(require_user)):
    return {"companies": get_service().list_companies()}


@router.post("/companies/generate")
def generate_companies(req: GenerateRequest, user: dict = Depends(require_admin_user)):
    return _call(get_service().generate, req.count, req.seed, req.include_canonical)


@router.get("/companies/{company_id}/employees")
def list_employees(company_id: str, user: dict = Depends(require_user)):
    return {"employees": _call(get_service().list_employees, company_id)}


@router.get("/companies/{company_id}/assessments")
def latest_assessments(company_id: str, user: dict = Depends(require_user)):
    return {"assessments": _call(get_service().latest_assessments, company_id)}


@router.post("/companies/{company_id}/assess")
def assess(company_id: str, req: AssessRequest, user: dict = Depends(require_user)):
    return _call(
        get_service().assess_company,
        company_id,
        controls=req.controls,
        auto_remediate=req.auto_remediate,
        use_llm=req.use_llm,
        dry_run=req.dry_run,
        execution_mode=req.execution_mode,
        require_medium_approval=req.require_medium_approval,
        max_remediation_retries=req.max_remediation_retries,
    )


@router.get("/companies/{company_id}/actions")
def list_actions(
    company_id: str,
    status: Literal[
        "AUTO_APPROVED", "PENDING_APPROVAL", "APPROVED", "REJECTED", "EXECUTED", "VERIFIED", "ROLLED_BACK", "FAILED"
    ] | None = None,
    user: dict = Depends(require_user),
):
    return {"actions": _call(get_service().list_actions, company_id, status)}


@router.post("/actions/{action_id}/decision")
def decide_action(action_id: str, req: DecisionRequest, user: dict = Depends(require_admin_user)):
    return _call(
        get_service().decide,
        req.company_id,
        action_id,
        req.decision,
        user.get("username") or str(user.get("user_id")),
        req.reason,
        req.assessment_run_id,
        req.execution_mode,
    )


@router.get("/companies/{company_id}/interviews")
def list_interviews(company_id: str, employee_id: str | None = None, user: dict = Depends(require_user)):
    return {"interviews": _call(get_service().list_interviews, company_id, employee_id)}


@router.post("/interviews/start")
def start_interview(req: InterviewStartRequest, user: dict = Depends(require_user)):
    return _call(get_service().start_interview, req.company_id, req.employee_id, req.control_id)


@router.post("/interviews/{session_id}/submit")
def submit_interview(session_id: str, req: InterviewSubmitRequest, user: dict = Depends(require_user)):
    return _call(get_service().submit_interview, req.company_id, session_id, req.answers, req.use_llm)


@router.post("/interviews/{session_id}/verify")
def verify_interview(session_id: str, req: InterviewVerifyRequest, user: dict = Depends(require_admin_user)):
    return _call(
        get_service().verify_interview,
        req.company_id,
        session_id,
        user.get("username") or str(user.get("user_id")),
        req.confirmed_passed,
    )


@router.post("/benchmark/run")
def run_benchmark(req: BenchmarkRequest, user: dict = Depends(require_admin_user)):
    return _call(get_service().run_benchmark, req.enterprise_count, req.seed, req.use_live_ollama)


@router.get("/benchmark/latest")
def latest_benchmark(user: dict = Depends(require_user)):
    report = get_service().latest_benchmark()
    if report is None:
        raise HTTPException(404, detail="Chưa có kết quả benchmark. Gọi POST /api/pc/benchmark/run trước.")
    return report
