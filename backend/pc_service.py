"""Service layer for the People-Centric compliance system.

Shared by the FastAPI router (backend/pc_api.py) and the standalone Streamlit dashboard so both expose
identical behaviour: 8-step assessment, Human-in-the-loop decisions, adaptive interviews and the ablation benchmark.
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any
from uuid import uuid4

from agent_core.people_centric import hardware_agent, human_agent, software_agent
from agent_core.people_centric.adaptive_interview import AdaptiveInterviewEngine
from agent_core.people_centric.iso_rag import ISORagEngine
from agent_core.people_centric.supervisor_graph import build_supervisor_graph, resume_after_admin_approval
from backend.pc_storage import BasePCStore, COMPLIANCE_STATES, utc_now_iso
from lab_adapters.base import ExecutionAdapter
from lab_adapters.lab_adapter import LabHostConfig, RealLabExecutionAdapter
from lab_adapters.sim_adapter import SimulationExecutionAdapter
from simulation.enterprise_generator import generate_multi_enterprise_dataset
from tools.playbooks import build_default_tool_registry

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BENCHMARK_DIR = ROOT / "data" / "pc-benchmark"


def _control_sort_key(control_id: str) -> tuple[int, int]:
    _, major, minor = control_id.split(".")
    return int(major), int(minor)


DEFAULT_CONTROLS: tuple[str, ...] = tuple(
    sorted(
        set(human_agent.HUMAN_CONTROLS) | set(hardware_agent.HARDWARE_CONTROLS) | set(software_agent.SOFTWARE_CONTROLS),
        key=_control_sort_key,
    )
)


class ConflictError(ValueError):
    """Raised when a request conflicts with the current state (stale run id, already decided, already submitted)."""


class PCService:
    def __init__(
        self,
        store: BasePCStore,
        rag: ISORagEngine | None = None,
        benchmark_dir: str | Path | None = None,
    ) -> None:
        self.store = store
        self.rag = rag or ISORagEngine()
        self.benchmark_dir = Path(benchmark_dir) if benchmark_dir else DEFAULT_BENCHMARK_DIR
        self._lock = threading.RLock()

    # ---------------------------------------------------------------- companies
    def _company(self, company_id: str) -> dict[str, Any]:
        company = self.store.get_company(company_id)
        if not company:
            raise KeyError(f"Unknown company_id: {company_id}")
        return company

    def list_companies(self) -> list[dict[str, Any]]:
        rows = []
        for c in self.store.list_companies():
            rows.append(
                {
                    "company_id": c["company_id"],
                    "name": c["name"],
                    "industry": c["industry"],
                    "size_tier": c["size_tier"],
                    "employee_count": c["employee_count"],
                    "execution_mode": c["execution_mode"],
                    "soa_exclusions": c.get("soa_exclusions", []),
                }
            )
        return rows

    def generate(self, count: int = 25, seed: int = 2026, include_canonical: bool = True) -> dict[str, Any]:
        if not 1 <= count <= 100:
            raise ValueError("count phải nằm trong khoảng 1..100.")
        with self._lock:
            created = generate_multi_enterprise_dataset(self.store, count=count, seed=seed, include_canonical=include_canonical)
        return {
            "generated": len(created),
            "canonical_included": include_canonical,
            "companies": [
                {"company_id": c["company_id"], "name": c["name"], "size_tier": c["size_tier"]} for c in created
            ],
        }

    def list_employees(self, company_id: str) -> list[dict[str, Any]]:
        self._company(company_id)
        return [
            {
                "employee_id": e["employee_id"],
                "full_name": e["full_name"],
                "department": e["department"],
                "employment_status": e["employment_status"],
                "incident_process_known": e.get("incident_process_known"),
            }
            for e in self.store.list_employees(company_id)
        ]

    # ---------------------------------------------------------------- runtime
    def _build_adapter(self, company: dict[str, Any], mode: str | None) -> tuple[ExecutionAdapter, str]:
        wanted = mode or company.get("execution_mode", "simulation")
        if wanted not in ("simulation", "hybrid_lab"):
            raise ValueError("execution_mode phải là 'simulation' hoặc 'hybrid_lab'.")
        if wanted == "hybrid_lab":
            if os.getenv("ISO_LAB_ENABLE_REAL") == "1":
                cfg = company.get("lab_config") or {}
                ws_hosts = dict(cfg.get("workstation_hosts", {}))
                if os.getenv("LAB_PC02_HOST"):
                    ws_hosts["PC-02"] = os.environ["LAB_PC02_HOST"]
                ad_host = os.getenv("LAB_AD_HOST") or cfg.get("ad_server_host", "")
                ad_user = os.getenv("LAB_AD_USER") or os.getenv("ISO_LAB_AD_USERNAME", "Administrator")
                return (
                    RealLabExecutionAdapter(
                        self.store,
                        LabHostConfig(
                            ad_server_host=ad_host,
                            ad_username=ad_user,
                            workstation_hosts=ws_hosts,
                        ),
                    ),
                    "hybrid_lab",
                )
            # Real WinRM/SSH execution is opt-in; never touch a lab implicitly.
            return SimulationExecutionAdapter(self.store), "simulation (hybrid_lab chưa bật: ISO_LAB_ENABLE_REAL!=1)"
        return SimulationExecutionAdapter(self.store), "simulation"

    def _runtime(self, company: dict[str, Any], mode: str | None):
        adapter, effective = self._build_adapter(company, mode)
        registry = build_default_tool_registry(self.store, adapter)
        graph = build_supervisor_graph(self.store, registry, rag=self.rag)
        return registry, graph, effective

    @staticmethod
    def _summarize(out: dict[str, Any]) -> dict[str, Any]:
        return {
            "control_id": out["control_id"],
            "pillar": out["pillar"],
            "assessment_run_id": out["assessment_run_id"],
            "initial_status": out["initial_status"],
            "status": out["compliance_status"],
            "stage_history": out["stage_history"],
            "pending_approval_action_ids": out.get("pending_approval_action_ids", []),
            "executed_actions": [
                {
                    "tool_name": a.get("tool_name"),
                    "risk_level": a.get("risk_level"),
                    "status": a.get("status"),
                    "action_id": a.get("action_id"),
                }
                for a in out.get("executed_actions", [])
            ],
            "findings": out.get("findings", []),
            "rationale": out.get("rationale", ""),
            "verification_summary": out.get("verification_summary", ""),
            "prompt_injection_alerts": out.get("prompt_injection_alerts", []),
            "llm_execution_log": out.get("llm_execution_log", []),
            "confidence": out.get("confidence", 1.0),
        }

    # ---------------------------------------------------------------- assessment
    def assess_company(
        self,
        company_id: str,
        *,
        controls: list[str] | None = None,
        auto_remediate: bool = True,
        use_llm: bool = False,
        dry_run: bool = False,
        execution_mode: str | None = None,
        require_medium_approval: bool = False,
        max_remediation_retries: int = 2,
    ) -> dict[str, Any]:
        company = self._company(company_id)
        selected = list(dict.fromkeys(controls)) if controls else list(DEFAULT_CONTROLS)
        unknown = [c for c in selected if c not in DEFAULT_CONTROLS]
        if unknown:
            raise ValueError(f"Control chưa được hỗ trợ: {unknown}")
        with self._lock:
            _, graph, effective = self._runtime(company, execution_mode)
            results = []
            for control_id in selected:
                out = graph.invoke(
                    {
                        "company_id": company_id,
                        "control_id": control_id,
                        "auto_remediate": auto_remediate,
                        "use_llm": use_llm,
                        "dry_run": dry_run,
                        "require_medium_approval": require_medium_approval,
                        "max_remediation_retries": max_remediation_retries,
                    }
                )
                results.append(self._summarize(out))
        counts = {state: 0 for state in COMPLIANCE_STATES}
        for r in results:
            counts[r["status"]] += 1
        return {
            "assessment_batch_id": str(uuid4()),
            "company_id": company_id,
            "effective_execution_mode": effective,
            "dry_run": dry_run,
            "completed_at_utc": utc_now_iso(),
            "status_counts": counts,
            "controls": results,
        }

    def latest_assessments(self, company_id: str) -> list[dict[str, Any]]:
        self._company(company_id)
        rows = self.store.list_assessments(company_id)
        if self.store.__class__.__name__ == "PostgresPCStore":
            rows = list(reversed(rows))  # Postgres returns newest first; keep oldest->newest so the newest wins below
        latest: dict[str, dict[str, Any]] = {}
        for row in rows:
            latest[row["control_id"]] = row
        return sorted(latest.values(), key=lambda r: _control_sort_key(r["control_id"]))

    # ---------------------------------------------------------------- actions / HITL
    def list_actions(self, company_id: str, status: str | None = None) -> list[dict[str, Any]]:
        self._company(company_id)
        return self.store.list_remediation_actions(company_id, approval_status=status)

    def decide(
        self,
        company_id: str,
        action_id: str,
        decision: str,
        admin_actor: str,
        reason: str = "",
        assessment_run_id: str | None = None,
        execution_mode: str | None = None,
    ) -> dict[str, Any]:
        decision = decision.upper()
        if decision not in ("APPROVE", "REJECT"):
            raise ValueError("decision phải là APPROVE hoặc REJECT.")
        company = self._company(company_id)
        with self._lock:
            action = self.store.get_remediation_action(company_id, action_id)
            if not action:
                raise KeyError(f"Remediation action not found: {action_id}")
            if assessment_run_id and action.get("assessment_run_id") and assessment_run_id != action["assessment_run_id"]:
                raise ConflictError("assessment_run_id không khớp với hành động (kết quả đánh giá đã cũ).")
            if action["approval_status"] != "PENDING_APPROVAL":
                raise ConflictError(f"Hành động đang ở trạng thái {action['approval_status']}, không còn chờ duyệt.")

            registry, graph, effective = self._runtime(company, execution_mode)
            if decision == "APPROVE":
                result = resume_after_admin_approval(
                    store=self.store,
                    registry=registry,
                    company_id=company_id,
                    action_id=action_id,
                    admin_actor=admin_actor,
                )
                return {
                    "decision": "APPROVE",
                    "effective_execution_mode": effective,
                    "action": result["execution"]["action"],
                    "verification": result["verification"],
                    "assessment": result["assessment"],
                }

            if len(reason.strip()) < 5:
                raise ValueError("Cần ghi lý do từ chối (tối thiểu 5 ký tự).")
            rejected = registry.reject_action(company_id, action_id, admin_actor, reason.strip())
            # The gap is still open: re-assess the same run without remediation so the status stays truthful.
            out = graph.invoke(
                {
                    "company_id": company_id,
                    "control_id": action["control_id"],
                    "assessment_run_id": action.get("assessment_run_id") or str(uuid4()),
                    "auto_remediate": False,
                }
            )
            return {
                "decision": "REJECT",
                "effective_execution_mode": effective,
                "action": rejected["action"],
                "assessment": self._summarize(out),
            }

    # ---------------------------------------------------------------- interviews
    def start_interview(self, company_id: str, employee_id: str, control_id: str = "A.6.8") -> dict[str, Any]:
        self._company(company_id)
        with self._lock:
            return AdaptiveInterviewEngine(self.store).start_session(company_id, employee_id, control_id)

    def _find_session(self, company_id: str, session_id: str) -> dict[str, Any]:
        self._company(company_id)
        session = next((s for s in self.store.list_interview_sessions(company_id) if s["session_id"] == session_id), None)
        if not session:
            raise KeyError(f"Interview session not found: {session_id}")
        return session

    def submit_interview(
        self, company_id: str, session_id: str, answers: list[str], use_llm: bool = False
    ) -> dict[str, Any]:
        with self._lock:
            session = self._find_session(company_id, session_id)
            if session.get("slm_score") is not None:
                raise ConflictError("Phiên phỏng vấn đã được nộp bài và chấm điểm.")
            return AdaptiveInterviewEngine(self.store).submit_session(
                company_id=company_id, session_id=session_id, answers=answers, use_llm=use_llm
            )

    def verify_interview(
        self, company_id: str, session_id: str, reviewer_id: str, confirmed_passed: bool
    ) -> dict[str, Any]:
        with self._lock:
            session = self._find_session(company_id, session_id)
            if session.get("slm_score") is None:
                raise ConflictError("Phiên chưa được nộp bài nên chưa thể xác minh.")
            return AdaptiveInterviewEngine(self.store).human_verify_session(
                company_id=company_id, session_id=session_id, reviewer_id=reviewer_id, confirmed_passed=confirmed_passed
            )

    def list_interviews(self, company_id: str, employee_id: str | None = None) -> list[dict[str, Any]]:
        self._company(company_id)
        return self.store.list_interview_sessions(company_id, employee_id=employee_id)

    # ---------------------------------------------------------------- benchmark
    def run_benchmark(self, enterprise_count: int = 25, seed: int = 2026, use_live_ollama: bool = False) -> dict[str, Any]:
        from benchmark.ablation_runner import export_benchmark_results, run_ablation_benchmark

        if enterprise_count < 25:
            raise ValueError("Benchmark yêu cầu tối thiểu 25 doanh nghiệp.")
        report = run_ablation_benchmark(enterprise_count=enterprise_count, seed=seed, use_live_ollama=use_live_ollama)
        paths = export_benchmark_results(report, self.benchmark_dir)
        return {**{k: v for k, v in report.items() if k != "outcomes"}, "exports": paths}

    def latest_benchmark(self) -> dict[str, Any] | None:
        path = self.benchmark_dir / "ablation_benchmark_report.json"
        if not path.is_file():
            return None
        report = json.loads(path.read_text(encoding="utf-8"))
        return {
            **{k: v for k, v in report.items() if k != "outcomes"},
            "exports": {
                "json_path": str(path),
                "csv_path": str(self.benchmark_dir / "ablation_benchmark_summary.csv"),
            },
        }
