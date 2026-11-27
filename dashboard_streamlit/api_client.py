"""HTTP REST client connecting Streamlit Dashboard to FastAPI (/api/pc/*) & PostgreSQL."""
from __future__ import annotations

from typing import Any
import requests

from backend.pc_service import ConflictError


class FastAPIPCClient:
    """HTTP REST client talking directly to backend/pc_api.py (/api/pc/*) with Bearer authentication."""

    def __init__(self, base_url: str = "", token: str = "", requester: Any = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token.strip()
        self._http = requester or requests

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}" if self.base_url else path

    def _handle(self, resp: Any) -> Any:
        if resp.status_code == 409:
            raise ConflictError(resp.json().get("detail", "Conflict"))
        if resp.status_code == 404:
            raise KeyError(resp.json().get("detail", "Not found"))
        if resp.status_code == 403:
            raise PermissionError(resp.json().get("detail", "Forbidden"))
        if resp.status_code == 422:
            raise ValueError(resp.json().get("detail", "Validation error"))
        if resp.status_code >= 400:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:300]}")
        return resp.json()

    def status(self) -> dict[str, Any]:
        return self._handle(self._http.get(self._url("/api/pc/status"), headers=self._headers()))

    def list_companies(self) -> list[dict[str, Any]]:
        return self._handle(self._http.get(self._url("/api/pc/companies"), headers=self._headers()))["companies"]

    def generate(self, count: int = 25, seed: int = 2026, include_canonical: bool = True) -> dict[str, Any]:
        return self._handle(
            self._http.post(
                self._url("/api/pc/companies/generate"),
                json={"count": count, "seed": seed, "include_canonical": include_canonical},
                headers=self._headers(),
            )
        )

    def list_employees(self, company_id: str) -> list[dict[str, Any]]:
        return self._handle(
            self._http.get(self._url(f"/api/pc/companies/{company_id}/employees"), headers=self._headers())
        )["employees"]

    def assess_company(
        self,
        company_id: str,
        *,
        controls: list[str] | None = None,
        auto_remediate: bool = True,
        use_llm: bool = False,
        dry_run: bool = False,
        execution_mode: str | None = None,
    ) -> dict[str, Any]:
        return self._handle(
            self._http.post(
                self._url(f"/api/pc/companies/{company_id}/assess"),
                json={
                    "controls": controls,
                    "auto_remediate": auto_remediate,
                    "use_llm": use_llm,
                    "dry_run": dry_run,
                    "execution_mode": execution_mode,
                },
                headers=self._headers(),
            )
        )

    def latest_assessments(self, company_id: str) -> list[dict[str, Any]]:
        return self._handle(
            self._http.get(self._url(f"/api/pc/companies/{company_id}/assessments"), headers=self._headers())
        )["assessments"]

    def list_actions(self, company_id: str, status: str | None = None) -> list[dict[str, Any]]:
        path = f"/api/pc/companies/{company_id}/actions"
        if status:
            path += f"?status={status}"
        return self._handle(self._http.get(self._url(path), headers=self._headers()))["actions"]

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
        return self._handle(
            self._http.post(
                self._url(f"/api/pc/actions/{action_id}/decision"),
                json={
                    "company_id": company_id,
                    "decision": decision,
                    "reason": reason,
                    "assessment_run_id": assessment_run_id,
                    "execution_mode": execution_mode,
                },
                headers=self._headers(),
            )
        )

    def start_interview(self, company_id: str, employee_id: str, control_id: str = "A.6.8") -> dict[str, Any]:
        return self._handle(
            self._http.post(
                self._url("/api/pc/interviews/start"),
                json={"company_id": company_id, "employee_id": employee_id, "control_id": control_id},
                headers=self._headers(),
            )
        )

    def submit_interview(
        self, company_id: str, session_id: str, answers: list[str], use_llm: bool = False
    ) -> dict[str, Any]:
        return self._handle(
            self._http.post(
                self._url(f"/api/pc/interviews/{session_id}/submit"),
                json={"company_id": company_id, "answers": answers, "use_llm": use_llm},
                headers=self._headers(),
            )
        )

    def verify_interview(
        self, company_id: str, session_id: str, reviewer_id: str, confirmed_passed: bool
    ) -> dict[str, Any]:
        return self._handle(
            self._http.post(
                self._url(f"/api/pc/interviews/{session_id}/verify"),
                json={"company_id": company_id, "confirmed_passed": confirmed_passed},
                headers=self._headers(),
            )
        )

    def run_benchmark(self, enterprise_count: int = 25, seed: int = 2026, use_live_ollama: bool = False) -> dict[str, Any]:
        return self._handle(
            self._http.post(
                self._url("/api/pc/benchmark/run"),
                json={"enterprise_count": enterprise_count, "seed": seed, "use_live_ollama": use_live_ollama},
                headers=self._headers(),
            )
        )

    def latest_benchmark(self) -> dict[str, Any] | None:
        resp = self._http.get(self._url("/api/pc/benchmark/latest"), headers=self._headers())
        if resp.status_code == 404:
            return None
        return self._handle(resp)
