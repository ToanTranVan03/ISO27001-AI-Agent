"""Multi-tenant PostgreSQL & In-Memory storage for People-Centric ISO 27001:2022 compliance.

Additive-only schema (pc_* tables) preserving all existing 56-control tables and tests.
All tenant queries strictly enforce company_id isolation.
"""
from __future__ import annotations

import copy
import hashlib
import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from psycopg.types.json import Jsonb
from backend.database import get_connection

ROOT_DIR = Path(__file__).resolve().parent.parent
PC_CONTROLS_PATH = ROOT_DIR / "docs" / "people_centric_controls.json"
ISO_KB_PATH = ROOT_DIR / "docs" / "iso_knowledge_base.json"

COMPLIANCE_STATES = (
    "Compliant",
    "Non-compliant",
    "Partial",
    "Insufficient Evidence",
    "Not Applicable",
    "Pending Remediation",
)

CLOSED_LOOP_STAGES = (
    "Observe",
    "Assess",
    "Detect",
    "Plan",
    "Act",
    "Verify",
    "Report",
    "Monitor",
)

RISK_LEVELS = ("LOW", "MEDIUM", "HIGH")

DEFAULT_BASELINE_POLICY: dict[str, Any] = {
    "firewall_enabled": True,
    "screen_lock_minutes_max": 5,
    "disk_encrypted": True,
    "password_policy_ok": True,
    "antivirus_active": True,
    "ntp_synced": True,
    "mfa_required": True,
    "approved_software_whitelist": [
        "Microsoft Office",
        "Google Chrome",
        "Mozilla Firefox",
        "7-Zip",
        "VS Code",
        "MISA Accounting",
        "OpenVPN Client",
        "CrowdStrike Falcon",
    ],
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_json(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_pc_controls() -> list[dict[str, Any]]:
    return json.loads(PC_CONTROLS_PATH.read_text(encoding="utf-8"))


def load_iso_knowledge_base() -> list[dict[str, Any]]:
    return json.loads(ISO_KB_PATH.read_text(encoding="utf-8"))


SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS pc_companies (
        company_id       TEXT PRIMARY KEY,
        name             TEXT NOT NULL,
        industry         TEXT NOT NULL,
        size_tier        TEXT NOT NULL CHECK (size_tier IN ('small', 'medium', 'enterprise')),
        employee_count   INTEGER NOT NULL,
        execution_mode   TEXT NOT NULL DEFAULT 'simulation' CHECK (execution_mode IN ('simulation', 'hybrid_lab')),
        baseline_policy  JSONB NOT NULL DEFAULT '{}'::jsonb,
        soa_exclusions   JSONB NOT NULL DEFAULT '[]'::jsonb,
        lab_config       JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pc_employees (
        company_id              TEXT NOT NULL REFERENCES pc_companies(company_id) ON DELETE CASCADE,
        employee_id             TEXT NOT NULL,
        full_name               TEXT NOT NULL,
        department              TEXT NOT NULL,
        role_title              TEXT NOT NULL,
        employment_status       TEXT NOT NULL CHECK (employment_status IN ('active', 'onboarding', 'terminated')),
        terminated_at           TIMESTAMPTZ,
        screened                BOOLEAN,
        contract_signed         BOOLEAN,
        nda_signed              BOOLEAN,
        training_completed      BOOLEAN,
        training_score          DOUBLE PRECISION,
        phishing_passed         BOOLEAN,
        incident_process_known  BOOLEAN,
        remote_work_compliant   BOOLEAN,
        offboarding_ack         BOOLEAN,
        metadata                JSONB NOT NULL DEFAULT '{}'::jsonb,
        updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY (company_id, employee_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pc_devices (
        company_id              TEXT NOT NULL REFERENCES pc_companies(company_id) ON DELETE CASCADE,
        device_id               TEXT NOT NULL,
        hostname                TEXT NOT NULL,
        os_type                 TEXT NOT NULL CHECK (os_type IN ('windows11', 'ubuntu', 'windows_server')),
        assigned_employee_id    TEXT,
        badge_card_active       BOOLEAN NOT NULL DEFAULT TRUE,
        returned_to_it          BOOLEAN NOT NULL DEFAULT FALSE,
        firewall_enabled        BOOLEAN,
        screen_lock_minutes     INTEGER,
        disk_encrypted          BOOLEAN,
        password_policy_ok      BOOLEAN,
        antivirus_active        BOOLEAN,
        ntp_synced              BOOLEAN,
        patch_compliant         BOOLEAN,
        missing_patches         JSONB NOT NULL DEFAULT '[]'::jsonb,
        usb_unauthorized_events INTEGER NOT NULL DEFAULT 0,
        disposal_verified       BOOLEAN,
        installed_software      JSONB NOT NULL DEFAULT '[]'::jsonb,
        audit_logging_enabled   BOOLEAN NOT NULL DEFAULT TRUE,
        updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY (company_id, device_id),
        FOREIGN KEY (company_id, assigned_employee_id)
            REFERENCES pc_employees(company_id, employee_id) ON DELETE SET NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pc_accounts (
        company_id       TEXT NOT NULL REFERENCES pc_companies(company_id) ON DELETE CASCADE,
        account_id       TEXT NOT NULL,
        employee_id      TEXT NOT NULL,
        system_type      TEXT NOT NULL CHECK (system_type IN ('active_directory', 'vpn', 'email', 'accounting_app', 'erp', 'server_ssh')),
        is_active        BOOLEAN NOT NULL DEFAULT TRUE,
        mfa_enabled      BOOLEAN,
        is_privileged    BOOLEAN NOT NULL DEFAULT FALSE,
        change_ticket_id TEXT,
        updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY (company_id, account_id),
        FOREIGN KEY (company_id, employee_id)
            REFERENCES pc_employees(company_id, employee_id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pc_assessments (
        assessment_run_id UUID PRIMARY KEY,
        company_id        TEXT NOT NULL REFERENCES pc_companies(company_id) ON DELETE CASCADE,
        control_id        TEXT NOT NULL,
        pillar            TEXT NOT NULL CHECK (pillar IN ('human', 'hardware', 'software', 'cross_domain')),
        status            TEXT NOT NULL CHECK (status IN (
                              'Compliant', 'Non-compliant', 'Partial',
                              'Insufficient Evidence', 'Not Applicable', 'Pending Remediation'
                          )),
        current_stage     TEXT NOT NULL CHECK (current_stage IN (
                              'Observe', 'Assess', 'Detect', 'Plan', 'Act', 'Verify', 'Report', 'Monitor'
                          )),
        confidence        DOUBLE PRECISION NOT NULL,
        findings          JSONB NOT NULL DEFAULT '[]'::jsonb,
        evidence_refs     JSONB NOT NULL DEFAULT '[]'::jsonb,
        rationale         TEXT NOT NULL,
        stage_history     JSONB NOT NULL DEFAULT '[]'::jsonb,
        created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pc_remediation_actions (
        action_id         UUID PRIMARY KEY,
        company_id        TEXT NOT NULL REFERENCES pc_companies(company_id) ON DELETE CASCADE,
        assessment_run_id UUID,
        control_id        TEXT NOT NULL,
        tool_name         TEXT NOT NULL,
        tool_params       JSONB NOT NULL,
        risk_level        TEXT NOT NULL CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
        approval_status   TEXT NOT NULL CHECK (approval_status IN (
                              'AUTO_APPROVED', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED',
                              'EXECUTED', 'VERIFIED', 'ROLLED_BACK', 'FAILED'
                          )),
        dry_run_preview   JSONB,
        snapshot_before   JSONB,
        execution_result  JSONB,
        verification_data JSONB,
        approved_by       TEXT,
        approved_at       TIMESTAMPTZ,
        created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pc_interview_sessions (
        session_id           UUID PRIMARY KEY,
        company_id           TEXT NOT NULL REFERENCES pc_companies(company_id) ON DELETE CASCADE,
        employee_id          TEXT NOT NULL,
        control_id           TEXT NOT NULL,
        questions            JSONB NOT NULL DEFAULT '[]'::jsonb,
        answers              JSONB NOT NULL DEFAULT '[]'::jsonb,
        slm_score            DOUBLE PRECISION,
        passed               BOOLEAN,
        slm_feedback         TEXT,
        human_verified       BOOLEAN NOT NULL DEFAULT FALSE,
        disciplinary_blocked BOOLEAN NOT NULL DEFAULT TRUE,
        created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        FOREIGN KEY (company_id, employee_id)
            REFERENCES pc_employees(company_id, employee_id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pc_ground_truth (
        company_id        TEXT NOT NULL REFERENCES pc_companies(company_id) ON DELETE CASCADE,
        control_id        TEXT NOT NULL,
        expected_status   TEXT NOT NULL,
        injected_faults   JSONB NOT NULL DEFAULT '[]'::jsonb,
        expected_actions  JSONB NOT NULL DEFAULT '[]'::jsonb,
        PRIMARY KEY (company_id, control_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pc_tool_audit_log (
        log_id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        company_id        TEXT NOT NULL,
        action_id         UUID,
        actor             TEXT NOT NULL,
        tool_name         TEXT NOT NULL,
        risk_level        TEXT NOT NULL,
        dry_run           BOOLEAN NOT NULL DEFAULT FALSE,
        params_sha256     TEXT NOT NULL,
        result_sha256     TEXT NOT NULL,
        status            TEXT NOT NULL,
        executed_at_utc   TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pc_iso_knowledge_chunks (
        chunk_id          TEXT PRIMARY KEY,
        standard_ref      TEXT NOT NULL,
        control_id        TEXT NOT NULL,
        pillar            TEXT NOT NULL,
        content           TEXT NOT NULL,
        embedding_json    JSONB,
        sha256_hash       TEXT NOT NULL
    )
    """,
)


def initialize_pc_schema() -> None:
    """Create all pc_* tables idempotently and seed ISO knowledge chunks."""
    chunks = load_iso_knowledge_base()
    with get_connection() as con, con.cursor() as cur:
        for stmt in SCHEMA_STATEMENTS:
            cur.execute(stmt)
        for chunk in chunks:
            digest = sha256_json(chunk["content"])
            cur.execute(
                """
                INSERT INTO pc_iso_knowledge_chunks (
                    chunk_id, standard_ref, control_id, pillar, content, embedding_json, sha256_hash
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (chunk_id) DO NOTHING
                """,
                (
                    chunk["chunk_id"],
                    chunk["standard_ref"],
                    chunk["control_id"],
                    chunk["pillar"],
                    chunk["content"],
                    Jsonb(None),
                    digest,
                ),
            )


class BasePCStore(ABC):
    """Multi-tenant repository interface shared by In-Memory and PostgreSQL backends."""

    @abstractmethod
    def upsert_company(self, company: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def get_company(self, company_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    def list_companies(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    def upsert_employee(self, company_id: str, employee: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def list_employees(self, company_id: str, department: str | None = None, employee_id: str | None = None) -> list[dict[str, Any]]: ...

    @abstractmethod
    def upsert_device(self, company_id: str, device: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def list_devices(self, company_id: str, device_ids: list[str] | None = None, employee_id: str | None = None) -> list[dict[str, Any]]: ...

    @abstractmethod
    def upsert_account(self, company_id: str, account: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def list_accounts(self, company_id: str, employee_id: str | None = None, systems: list[str] | None = None) -> list[dict[str, Any]]: ...

    @abstractmethod
    def save_assessment(self, assessment: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def list_assessments(self, company_id: str, control_id: str | None = None) -> list[dict[str, Any]]: ...

    @abstractmethod
    def save_remediation_action(self, action: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def get_remediation_action(self, company_id: str, action_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    def list_remediation_actions(self, company_id: str, approval_status: str | None = None) -> list[dict[str, Any]]: ...

    @abstractmethod
    def save_interview_session(self, session: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def list_interview_sessions(self, company_id: str, employee_id: str | None = None) -> list[dict[str, Any]]: ...

    @abstractmethod
    def save_ground_truth(self, company_id: str, control_id: str, expected_status: str, injected_faults: list[dict[str, Any]], expected_actions: list[str]) -> None: ...

    @abstractmethod
    def get_ground_truth(self, company_id: str, *, evaluator_token: str) -> dict[str, dict[str, Any]]: ...

    @abstractmethod
    def append_audit_log(self, entry: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def list_audit_logs(self, company_id: str) -> list[dict[str, Any]]: ...


class InMemoryPCStore(BasePCStore):
    """Fast, strictly isolated multi-tenant store for unit tests, offline demos, and benchmarks."""

    def __init__(self) -> None:
        self._companies: dict[str, dict[str, Any]] = {}
        self._employees: dict[str, dict[str, dict[str, Any]]] = {}
        self._devices: dict[str, dict[str, dict[str, Any]]] = {}
        self._accounts: dict[str, dict[str, dict[str, Any]]] = {}
        self._assessments: dict[str, list[dict[str, Any]]] = {}
        self._actions: dict[str, dict[str, dict[str, Any]]] = {}
        self._interviews: dict[str, list[dict[str, Any]]] = {}
        self._ground_truth: dict[str, dict[str, dict[str, Any]]] = {}
        self._audit_logs: list[dict[str, Any]] = []
        self._tickets: dict[str, list[dict[str, Any]]] = {}
        self._notifications: dict[str, list[dict[str, Any]]] = {}

    def _ensure_company(self, company_id: str) -> None:
        if company_id not in self._companies:
            raise KeyError(f"Unknown company_id: {company_id}")

    def upsert_company(self, company: dict[str, Any]) -> dict[str, Any]:
        cid = company["company_id"]
        record = {
            "execution_mode": "simulation",
            "baseline_policy": copy.deepcopy(DEFAULT_BASELINE_POLICY),
            "soa_exclusions": [],
            "lab_config": {},
            "created_at": utc_now_iso(),
            **copy.deepcopy(company),
        }
        self._companies[cid] = record
        self._employees.setdefault(cid, {})
        self._devices.setdefault(cid, {})
        self._accounts.setdefault(cid, {})
        self._assessments.setdefault(cid, [])
        self._actions.setdefault(cid, {})
        self._interviews.setdefault(cid, [])
        self._ground_truth.setdefault(cid, {})
        self._tickets.setdefault(cid, [])
        self._notifications.setdefault(cid, [])
        return copy.deepcopy(record)

    def get_company(self, company_id: str) -> dict[str, Any] | None:
        rec = self._companies.get(company_id)
        return copy.deepcopy(rec) if rec else None

    def list_companies(self) -> list[dict[str, Any]]:
        return [copy.deepcopy(self._companies[k]) for k in sorted(self._companies)]

    def upsert_employee(self, company_id: str, employee: dict[str, Any]) -> dict[str, Any]:
        self._ensure_company(company_id)
        eid = employee["employee_id"]
        rec = {
            "company_id": company_id,
            "employment_status": "active",
            "terminated_at": None,
            "metadata": {},
            "updated_at": utc_now_iso(),
            **copy.deepcopy(employee),
        }
        rec["company_id"] = company_id
        self._employees[company_id][eid] = rec
        return copy.deepcopy(rec)

    def list_employees(self, company_id: str, department: str | None = None, employee_id: str | None = None) -> list[dict[str, Any]]:
        self._ensure_company(company_id)
        rows = list(self._employees[company_id].values())
        if employee_id is not None:
            rows = [r for r in rows if r["employee_id"] == employee_id]
        if department is not None:
            rows = [r for r in rows if r["department"] == department]
        rows.sort(key=lambda r: r["employee_id"])
        return copy.deepcopy(rows)

    def upsert_device(self, company_id: str, device: dict[str, Any]) -> dict[str, Any]:
        self._ensure_company(company_id)
        did = device["device_id"]
        rec = {
            "company_id": company_id,
            "badge_card_active": True,
            "returned_to_it": False,
            "missing_patches": [],
            "usb_unauthorized_events": 0,
            "installed_software": [],
            "audit_logging_enabled": True,
            "updated_at": utc_now_iso(),
            **copy.deepcopy(device),
        }
        rec["company_id"] = company_id
        self._devices[company_id][did] = rec
        return copy.deepcopy(rec)

    def list_devices(self, company_id: str, device_ids: list[str] | None = None, employee_id: str | None = None) -> list[dict[str, Any]]:
        self._ensure_company(company_id)
        rows = list(self._devices[company_id].values())
        if device_ids is not None:
            wanted = set(device_ids)
            rows = [r for r in rows if r["device_id"] in wanted]
        if employee_id is not None:
            rows = [r for r in rows if r.get("assigned_employee_id") == employee_id]
        rows.sort(key=lambda r: r["device_id"])
        return copy.deepcopy(rows)

    def upsert_account(self, company_id: str, account: dict[str, Any]) -> dict[str, Any]:
        self._ensure_company(company_id)
        aid = account["account_id"]
        rec = {
            "company_id": company_id,
            "is_active": True,
            "is_privileged": False,
            "change_ticket_id": None,
            "updated_at": utc_now_iso(),
            **copy.deepcopy(account),
        }
        rec["company_id"] = company_id
        self._accounts[company_id][aid] = rec
        return copy.deepcopy(rec)

    def list_accounts(self, company_id: str, employee_id: str | None = None, systems: list[str] | None = None) -> list[dict[str, Any]]:
        self._ensure_company(company_id)
        rows = list(self._accounts[company_id].values())
        if employee_id is not None:
            rows = [r for r in rows if r["employee_id"] == employee_id]
        if systems is not None:
            wanted = set(systems)
            rows = [r for r in rows if r["system_type"] in wanted]
        rows.sort(key=lambda r: r["account_id"])
        return copy.deepcopy(rows)

    def save_assessment(self, assessment: dict[str, Any]) -> dict[str, Any]:
        cid = assessment["company_id"]
        self._ensure_company(cid)
        if assessment["status"] not in COMPLIANCE_STATES:
            raise ValueError(f"Invalid compliance status: {assessment['status']}")
        if assessment["current_stage"] not in CLOSED_LOOP_STAGES:
            raise ValueError(f"Invalid closed-loop stage: {assessment['current_stage']}")
        rec = {
            "assessment_run_id": str(uuid4()),
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
            **copy.deepcopy(assessment),
        }
        existing = self._assessments[cid]
        for idx, item in enumerate(existing):
            if item["assessment_run_id"] == rec["assessment_run_id"]:
                existing[idx] = rec
                return copy.deepcopy(rec)
        existing.append(rec)
        return copy.deepcopy(rec)

    def list_assessments(self, company_id: str, control_id: str | None = None) -> list[dict[str, Any]]:
        self._ensure_company(company_id)
        rows = self._assessments[company_id]
        if control_id is not None:
            rows = [r for r in rows if r["control_id"] == control_id]
        return copy.deepcopy(rows)

    def save_remediation_action(self, action: dict[str, Any]) -> dict[str, Any]:
        cid = action["company_id"]
        self._ensure_company(cid)
        aid = action.get("action_id") or str(uuid4())
        rec = {
            "action_id": aid,
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
            **copy.deepcopy(action),
        }
        rec["action_id"] = aid
        rec["updated_at"] = utc_now_iso()
        self._actions[cid][aid] = rec
        return copy.deepcopy(rec)

    def get_remediation_action(self, company_id: str, action_id: str) -> dict[str, Any] | None:
        self._ensure_company(company_id)
        rec = self._actions[company_id].get(action_id)
        return copy.deepcopy(rec) if rec else None

    def list_remediation_actions(self, company_id: str, approval_status: str | None = None) -> list[dict[str, Any]]:
        self._ensure_company(company_id)
        rows = list(self._actions[company_id].values())
        if approval_status is not None:
            rows = [r for r in rows if r["approval_status"] == approval_status]
        return copy.deepcopy(rows)

    def save_interview_session(self, session: dict[str, Any]) -> dict[str, Any]:
        cid = session["company_id"]
        self._ensure_company(cid)
        rec = {
            "session_id": str(uuid4()),
            "human_verified": False,
            "disciplinary_blocked": True,
            "created_at": utc_now_iso(),
            **copy.deepcopy(session),
        }
        # AI Ethics hard guardrail: never allow unverified AI output to trigger discipline
        rec["disciplinary_blocked"] = True
        existing = self._interviews[cid]
        for idx, item in enumerate(existing):
            if item["session_id"] == rec["session_id"]:
                existing[idx] = rec
                return copy.deepcopy(rec)
        existing.append(rec)
        return copy.deepcopy(rec)

    def list_interview_sessions(self, company_id: str, employee_id: str | None = None) -> list[dict[str, Any]]:
        self._ensure_company(company_id)
        rows = self._interviews[company_id]
        if employee_id is not None:
            rows = [r for r in rows if r["employee_id"] == employee_id]
        return copy.deepcopy(rows)

    def save_ground_truth(
        self,
        company_id: str,
        control_id: str,
        expected_status: str,
        injected_faults: list[dict[str, Any]],
        expected_actions: list[str],
    ) -> None:
        self._ensure_company(company_id)
        if expected_status not in COMPLIANCE_STATES:
            raise ValueError(f"Invalid expected_status: {expected_status}")
        self._ground_truth[company_id][control_id] = {
            "company_id": company_id,
            "control_id": control_id,
            "expected_status": expected_status,
            "injected_faults": copy.deepcopy(injected_faults),
            "expected_actions": list(expected_actions),
        }

    def get_ground_truth(self, company_id: str, *, evaluator_token: str) -> dict[str, dict[str, Any]]:
        if evaluator_token != "BENCHMARK_EVALUATOR_ONLY":
            raise PermissionError("Ground truth is isolated from runtime Agents.")
        self._ensure_company(company_id)
        return copy.deepcopy(self._ground_truth[company_id])

    def append_audit_log(self, entry: dict[str, Any]) -> dict[str, Any]:
        rec = {
            "log_id": len(self._audit_logs) + 1,
            "executed_at_utc": utc_now_iso(),
            **copy.deepcopy(entry),
        }
        self._audit_logs.append(rec)
        return copy.deepcopy(rec)

    def list_audit_logs(self, company_id: str) -> list[dict[str, Any]]:
        return [copy.deepcopy(r) for r in self._audit_logs if r["company_id"] == company_id]

    def add_ticket(self, company_id: str, ticket: dict[str, Any]) -> dict[str, Any]:
        self._ensure_company(company_id)
        rec = {"ticket_id": f"TKT-{uuid4().hex[:8].upper()}", "created_at": utc_now_iso(), **copy.deepcopy(ticket)}
        self._tickets[company_id].append(rec)
        return copy.deepcopy(rec)

    def list_tickets(self, company_id: str) -> list[dict[str, Any]]:
        self._ensure_company(company_id)
        return copy.deepcopy(self._tickets[company_id])

    def add_notification(self, company_id: str, note: dict[str, Any]) -> dict[str, Any]:
        self._ensure_company(company_id)
        rec = {"notification_id": f"NTF-{uuid4().hex[:8].upper()}", "sent_at": utc_now_iso(), **copy.deepcopy(note)}
        self._notifications[company_id].append(rec)
        return copy.deepcopy(rec)

    def list_notifications(self, company_id: str) -> list[dict[str, Any]]:
        self._ensure_company(company_id)
        return copy.deepcopy(self._notifications[company_id])


class PostgresPCStore(BasePCStore):
    """Production PostgreSQL multi-tenant store backed by pc_* tables."""

    def upsert_company(self, company: dict[str, Any]) -> dict[str, Any]:
        with get_connection() as con, con.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pc_companies (
                    company_id, name, industry, size_tier, employee_count,
                    execution_mode, baseline_policy, soa_exclusions, lab_config
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (company_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    industry = EXCLUDED.industry,
                    size_tier = EXCLUDED.size_tier,
                    employee_count = EXCLUDED.employee_count,
                    execution_mode = EXCLUDED.execution_mode,
                    baseline_policy = EXCLUDED.baseline_policy,
                    soa_exclusions = EXCLUDED.soa_exclusions,
                    lab_config = EXCLUDED.lab_config
                """,
                (
                    company["company_id"],
                    company["name"],
                    company["industry"],
                    company["size_tier"],
                    int(company["employee_count"]),
                    company.get("execution_mode", "simulation"),
                    Jsonb(company.get("baseline_policy", DEFAULT_BASELINE_POLICY)),
                    Jsonb(company.get("soa_exclusions", [])),
                    Jsonb(company.get("lab_config", {})),
                ),
            )
        return self.get_company(company["company_id"]) or company

    def get_company(self, company_id: str) -> dict[str, Any] | None:
        with get_connection() as con, con.cursor() as cur:
            cur.execute(
                """
                SELECT company_id, name, industry, size_tier, employee_count,
                       execution_mode, baseline_policy, soa_exclusions, lab_config, created_at
                FROM pc_companies WHERE company_id = %s
                """,
                (company_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        return {
            "company_id": row[0],
            "name": row[1],
            "industry": row[2],
            "size_tier": row[3],
            "employee_count": row[4],
            "execution_mode": row[5],
            "baseline_policy": row[6],
            "soa_exclusions": row[7],
            "lab_config": row[8],
            "created_at": row[9].isoformat(),
        }

    def list_companies(self) -> list[dict[str, Any]]:
        with get_connection() as con, con.cursor() as cur:
            cur.execute(
                """
                SELECT company_id, name, industry, size_tier, employee_count,
                       execution_mode, baseline_policy, soa_exclusions, lab_config, created_at
                FROM pc_companies ORDER BY company_id
                """
            )
            rows = cur.fetchall()
        return [
            {
                "company_id": r[0], "name": r[1], "industry": r[2], "size_tier": r[3],
                "employee_count": r[4], "execution_mode": r[5], "baseline_policy": r[6],
                "soa_exclusions": r[7], "lab_config": r[8], "created_at": r[9].isoformat(),
            }
            for r in rows
        ]

    def upsert_employee(self, company_id: str, employee: dict[str, Any]) -> dict[str, Any]:
        with get_connection() as con, con.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pc_employees (
                    company_id, employee_id, full_name, department, role_title,
                    employment_status, terminated_at, screened, contract_signed, nda_signed,
                    training_completed, training_score, phishing_passed,
                    incident_process_known, remote_work_compliant, offboarding_ack, metadata, updated_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                ON CONFLICT (company_id, employee_id) DO UPDATE SET
                    full_name=EXCLUDED.full_name, department=EXCLUDED.department,
                    role_title=EXCLUDED.role_title, employment_status=EXCLUDED.employment_status,
                    terminated_at=EXCLUDED.terminated_at, screened=EXCLUDED.screened,
                    contract_signed=EXCLUDED.contract_signed, nda_signed=EXCLUDED.nda_signed,
                    training_completed=EXCLUDED.training_completed, training_score=EXCLUDED.training_score,
                    phishing_passed=EXCLUDED.phishing_passed,
                    incident_process_known=EXCLUDED.incident_process_known,
                    remote_work_compliant=EXCLUDED.remote_work_compliant,
                    offboarding_ack=EXCLUDED.offboarding_ack, metadata=EXCLUDED.metadata,
                    updated_at=NOW()
                """,
                (
                    company_id, employee["employee_id"], employee["full_name"],
                    employee["department"], employee["role_title"],
                    employee.get("employment_status", "active"), employee.get("terminated_at"),
                    employee.get("screened"), employee.get("contract_signed"), employee.get("nda_signed"),
                    employee.get("training_completed"), employee.get("training_score"),
                    employee.get("phishing_passed"), employee.get("incident_process_known"),
                    employee.get("remote_work_compliant"), employee.get("offboarding_ack"),
                    Jsonb(employee.get("metadata", {})),
                ),
            )
        return {**employee, "company_id": company_id}

    def list_employees(self, company_id: str, department: str | None = None, employee_id: str | None = None) -> list[dict[str, Any]]:
        clauses = ["company_id = %s"]
        params: list[Any] = [company_id]
        if department is not None:
            clauses.append("department = %s")
            params.append(department)
        if employee_id is not None:
            clauses.append("employee_id = %s")
            params.append(employee_id)
        sql = f"""
            SELECT company_id, employee_id, full_name, department, role_title,
                   employment_status, terminated_at, screened, contract_signed, nda_signed,
                   training_completed, training_score, phishing_passed,
                   incident_process_known, remote_work_compliant, offboarding_ack, metadata
            FROM pc_employees WHERE {' AND '.join(clauses)} ORDER BY employee_id
        """
        with get_connection() as con, con.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        cols = [
            "company_id", "employee_id", "full_name", "department", "role_title",
            "employment_status", "terminated_at", "screened", "contract_signed", "nda_signed",
            "training_completed", "training_score", "phishing_passed",
            "incident_process_known", "remote_work_compliant", "offboarding_ack", "metadata",
        ]
        result = []
        for r in rows:
            item = dict(zip(cols, r))
            if item["terminated_at"] is not None:
                item["terminated_at"] = item["terminated_at"].isoformat()
            result.append(item)
        return result

    def upsert_device(self, company_id: str, device: dict[str, Any]) -> dict[str, Any]:
        with get_connection() as con, con.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pc_devices (
                    company_id, device_id, hostname, os_type, assigned_employee_id,
                    badge_card_active, returned_to_it, firewall_enabled, screen_lock_minutes,
                    disk_encrypted, password_policy_ok, antivirus_active, ntp_synced,
                    patch_compliant, missing_patches, usb_unauthorized_events,
                    disposal_verified, installed_software, audit_logging_enabled, updated_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                ON CONFLICT (company_id, device_id) DO UPDATE SET
                    hostname=EXCLUDED.hostname, os_type=EXCLUDED.os_type,
                    assigned_employee_id=EXCLUDED.assigned_employee_id,
                    badge_card_active=EXCLUDED.badge_card_active, returned_to_it=EXCLUDED.returned_to_it,
                    firewall_enabled=EXCLUDED.firewall_enabled, screen_lock_minutes=EXCLUDED.screen_lock_minutes,
                    disk_encrypted=EXCLUDED.disk_encrypted, password_policy_ok=EXCLUDED.password_policy_ok,
                    antivirus_active=EXCLUDED.antivirus_active, ntp_synced=EXCLUDED.ntp_synced,
                    patch_compliant=EXCLUDED.patch_compliant, missing_patches=EXCLUDED.missing_patches,
                    usb_unauthorized_events=EXCLUDED.usb_unauthorized_events,
                    disposal_verified=EXCLUDED.disposal_verified,
                    installed_software=EXCLUDED.installed_software,
                    audit_logging_enabled=EXCLUDED.audit_logging_enabled, updated_at=NOW()
                """,
                (
                    company_id, device["device_id"], device["hostname"], device["os_type"],
                    device.get("assigned_employee_id"), device.get("badge_card_active", True),
                    device.get("returned_to_it", False), device.get("firewall_enabled"),
                    device.get("screen_lock_minutes"), device.get("disk_encrypted"),
                    device.get("password_policy_ok"), device.get("antivirus_active"),
                    device.get("ntp_synced"), device.get("patch_compliant"),
                    Jsonb(device.get("missing_patches", [])), int(device.get("usb_unauthorized_events", 0)),
                    device.get("disposal_verified"), Jsonb(device.get("installed_software", [])),
                    device.get("audit_logging_enabled", True),
                ),
            )
        return {**device, "company_id": company_id}

    def list_devices(self, company_id: str, device_ids: list[str] | None = None, employee_id: str | None = None) -> list[dict[str, Any]]:
        clauses = ["company_id = %s"]
        params: list[Any] = [company_id]
        if device_ids is not None:
            clauses.append("device_id = ANY(%s)")
            params.append(device_ids)
        if employee_id is not None:
            clauses.append("assigned_employee_id = %s")
            params.append(employee_id)
        sql = f"""
            SELECT company_id, device_id, hostname, os_type, assigned_employee_id,
                   badge_card_active, returned_to_it, firewall_enabled, screen_lock_minutes,
                   disk_encrypted, password_policy_ok, antivirus_active, ntp_synced,
                   patch_compliant, missing_patches, usb_unauthorized_events,
                   disposal_verified, installed_software, audit_logging_enabled
            FROM pc_devices WHERE {' AND '.join(clauses)} ORDER BY device_id
        """
        with get_connection() as con, con.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        cols = [
            "company_id", "device_id", "hostname", "os_type", "assigned_employee_id",
            "badge_card_active", "returned_to_it", "firewall_enabled", "screen_lock_minutes",
            "disk_encrypted", "password_policy_ok", "antivirus_active", "ntp_synced",
            "patch_compliant", "missing_patches", "usb_unauthorized_events",
            "disposal_verified", "installed_software", "audit_logging_enabled",
        ]
        return [dict(zip(cols, r)) for r in rows]

    def upsert_account(self, company_id: str, account: dict[str, Any]) -> dict[str, Any]:
        with get_connection() as con, con.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pc_accounts (
                    company_id, account_id, employee_id, system_type,
                    is_active, mfa_enabled, is_privileged, change_ticket_id, updated_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                ON CONFLICT (company_id, account_id) DO UPDATE SET
                    is_active=EXCLUDED.is_active, mfa_enabled=EXCLUDED.mfa_enabled,
                    is_privileged=EXCLUDED.is_privileged, change_ticket_id=EXCLUDED.change_ticket_id,
                    updated_at=NOW()
                """,
                (
                    company_id, account["account_id"], account["employee_id"],
                    account["system_type"], account.get("is_active", True),
                    account.get("mfa_enabled"), account.get("is_privileged", False),
                    account.get("change_ticket_id"),
                ),
            )
        return {**account, "company_id": company_id}

    def list_accounts(self, company_id: str, employee_id: str | None = None, systems: list[str] | None = None) -> list[dict[str, Any]]:
        clauses = ["company_id = %s"]
        params: list[Any] = [company_id]
        if employee_id is not None:
            clauses.append("employee_id = %s")
            params.append(employee_id)
        if systems is not None:
            clauses.append("system_type = ANY(%s)")
            params.append(systems)
        sql = f"""
            SELECT company_id, account_id, employee_id, system_type,
                   is_active, mfa_enabled, is_privileged, change_ticket_id
            FROM pc_accounts WHERE {' AND '.join(clauses)} ORDER BY account_id
        """
        with get_connection() as con, con.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        cols = ["company_id", "account_id", "employee_id", "system_type", "is_active", "mfa_enabled", "is_privileged", "change_ticket_id"]
        return [dict(zip(cols, r)) for r in rows]

    def save_assessment(self, assessment: dict[str, Any]) -> dict[str, Any]:
        run_id = assessment.get("assessment_run_id") or str(uuid4())
        with get_connection() as con, con.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pc_assessments (
                    assessment_run_id, company_id, control_id, pillar, status,
                    current_stage, confidence, findings, evidence_refs, rationale, stage_history, updated_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                ON CONFLICT (assessment_run_id) DO UPDATE SET
                    status=EXCLUDED.status, current_stage=EXCLUDED.current_stage,
                    confidence=EXCLUDED.confidence, findings=EXCLUDED.findings,
                    evidence_refs=EXCLUDED.evidence_refs, rationale=EXCLUDED.rationale,
                    stage_history=EXCLUDED.stage_history, updated_at=NOW()
                """,
                (
                    run_id, assessment["company_id"], assessment["control_id"], assessment["pillar"],
                    assessment["status"], assessment["current_stage"], float(assessment["confidence"]),
                    Jsonb(assessment.get("findings", [])), Jsonb(assessment.get("evidence_refs", [])),
                    assessment["rationale"], Jsonb(assessment.get("stage_history", [])),
                ),
            )
        return {**assessment, "assessment_run_id": run_id}

    def list_assessments(self, company_id: str, control_id: str | None = None) -> list[dict[str, Any]]:
        clauses = ["company_id = %s"]
        params: list[Any] = [company_id]
        if control_id:
            clauses.append("control_id = %s")
            params.append(control_id)
        with get_connection() as con, con.cursor() as cur:
            cur.execute(
                f"""
                SELECT assessment_run_id, company_id, control_id, pillar, status, current_stage,
                       confidence, findings, evidence_refs, rationale, stage_history
                FROM pc_assessments WHERE {' AND '.join(clauses)} ORDER BY created_at DESC
                """,
                params,
            )
            rows = cur.fetchall()
        cols = ["assessment_run_id", "company_id", "control_id", "pillar", "status", "current_stage", "confidence", "findings", "evidence_refs", "rationale", "stage_history"]
        return [{**dict(zip(cols, r)), "assessment_run_id": str(r[0])} for r in rows]

    def save_remediation_action(self, action: dict[str, Any]) -> dict[str, Any]:
        aid = action.get("action_id") or str(uuid4())
        with get_connection() as con, con.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pc_remediation_actions (
                    action_id, company_id, assessment_run_id, control_id, tool_name,
                    tool_params, risk_level, approval_status, dry_run_preview,
                    snapshot_before, execution_result, verification_data, approved_by, approved_at, updated_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                ON CONFLICT (action_id) DO UPDATE SET
                    approval_status=EXCLUDED.approval_status, dry_run_preview=EXCLUDED.dry_run_preview,
                    snapshot_before=EXCLUDED.snapshot_before, execution_result=EXCLUDED.execution_result,
                    verification_data=EXCLUDED.verification_data, approved_by=EXCLUDED.approved_by,
                    approved_at=EXCLUDED.approved_at, updated_at=NOW()
                """,
                (
                    aid, action["company_id"], action.get("assessment_run_id"), action["control_id"],
                    action["tool_name"], Jsonb(action["tool_params"]), action["risk_level"],
                    action["approval_status"], Jsonb(action.get("dry_run_preview")),
                    Jsonb(action.get("snapshot_before")), Jsonb(action.get("execution_result")),
                    Jsonb(action.get("verification_data")), action.get("approved_by"),
                    action.get("approved_at"),
                ),
            )
        return {**action, "action_id": aid}

    def get_remediation_action(self, company_id: str, action_id: str) -> dict[str, Any] | None:
        with get_connection() as con, con.cursor() as cur:
            cur.execute(
                """
                SELECT action_id, company_id, assessment_run_id, control_id, tool_name, tool_params,
                       risk_level, approval_status, dry_run_preview, snapshot_before,
                       execution_result, verification_data, approved_by, approved_at
                FROM pc_remediation_actions WHERE company_id=%s AND action_id=%s
                """,
                (company_id, action_id),
            )
            r = cur.fetchone()
        if not r:
            return None
        cols = ["action_id", "company_id", "assessment_run_id", "control_id", "tool_name", "tool_params", "risk_level", "approval_status", "dry_run_preview", "snapshot_before", "execution_result", "verification_data", "approved_by", "approved_at"]
        rec = dict(zip(cols, r))
        rec["action_id"] = str(rec["action_id"])
        if rec["assessment_run_id"]:
            rec["assessment_run_id"] = str(rec["assessment_run_id"])
        if rec["approved_at"]:
            rec["approved_at"] = rec["approved_at"].isoformat()
        return rec

    def list_remediation_actions(self, company_id: str, approval_status: str | None = None) -> list[dict[str, Any]]:
        clauses = ["company_id = %s"]
        params: list[Any] = [company_id]
        if approval_status:
            clauses.append("approval_status = %s")
            params.append(approval_status)
        with get_connection() as con, con.cursor() as cur:
            cur.execute(
                f"""
                SELECT action_id, company_id, assessment_run_id, control_id, tool_name, tool_params,
                       risk_level, approval_status, dry_run_preview, snapshot_before,
                       execution_result, verification_data, approved_by, approved_at
                FROM pc_remediation_actions WHERE {' AND '.join(clauses)} ORDER BY created_at DESC
                """,
                params,
            )
            rows = cur.fetchall()
        cols = ["action_id", "company_id", "assessment_run_id", "control_id", "tool_name", "tool_params", "risk_level", "approval_status", "dry_run_preview", "snapshot_before", "execution_result", "verification_data", "approved_by", "approved_at"]
        out = []
        for r in rows:
            rec = dict(zip(cols, r))
            rec["action_id"] = str(rec["action_id"])
            if rec["assessment_run_id"]:
                rec["assessment_run_id"] = str(rec["assessment_run_id"])
            if rec["approved_at"]:
                rec["approved_at"] = rec["approved_at"].isoformat()
            out.append(rec)
        return out

    def save_interview_session(self, session: dict[str, Any]) -> dict[str, Any]:
        sid = session.get("session_id") or str(uuid4())
        with get_connection() as con, con.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pc_interview_sessions (
                    session_id, company_id, employee_id, control_id, questions, answers,
                    slm_score, passed, slm_feedback, human_verified, disciplinary_blocked
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,TRUE)
                ON CONFLICT (session_id) DO UPDATE SET
                    answers=EXCLUDED.answers, slm_score=EXCLUDED.slm_score,
                    passed=EXCLUDED.passed, slm_feedback=EXCLUDED.slm_feedback,
                    human_verified=EXCLUDED.human_verified
                """,
                (
                    sid, session["company_id"], session["employee_id"], session["control_id"],
                    Jsonb(session.get("questions", [])), Jsonb(session.get("answers", [])),
                    session.get("slm_score"), session.get("passed"), session.get("slm_feedback"),
                    bool(session.get("human_verified", False)),
                ),
            )
        return {**session, "session_id": sid, "disciplinary_blocked": True}

    def list_interview_sessions(self, company_id: str, employee_id: str | None = None) -> list[dict[str, Any]]:
        clauses = ["company_id = %s"]
        params: list[Any] = [company_id]
        if employee_id:
            clauses.append("employee_id = %s")
            params.append(employee_id)
        with get_connection() as con, con.cursor() as cur:
            cur.execute(
                f"""
                SELECT session_id, company_id, employee_id, control_id, questions, answers,
                       slm_score, passed, slm_feedback, human_verified, disciplinary_blocked
                FROM pc_interview_sessions WHERE {' AND '.join(clauses)} ORDER BY created_at DESC
                """,
                params,
            )
            rows = cur.fetchall()
        cols = ["session_id", "company_id", "employee_id", "control_id", "questions", "answers", "slm_score", "passed", "slm_feedback", "human_verified", "disciplinary_blocked"]
        return [{**dict(zip(cols, r)), "session_id": str(r[0])} for r in rows]

    def save_ground_truth(self, company_id: str, control_id: str, expected_status: str, injected_faults: list[dict[str, Any]], expected_actions: list[str]) -> None:
        with get_connection() as con, con.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pc_ground_truth (company_id, control_id, expected_status, injected_faults, expected_actions)
                VALUES (%s,%s,%s,%s,%s)
                ON CONFLICT (company_id, control_id) DO UPDATE SET
                    expected_status=EXCLUDED.expected_status,
                    injected_faults=EXCLUDED.injected_faults,
                    expected_actions=EXCLUDED.expected_actions
                """,
                (company_id, control_id, expected_status, Jsonb(injected_faults), Jsonb(expected_actions)),
            )

    def get_ground_truth(self, company_id: str, *, evaluator_token: str) -> dict[str, dict[str, Any]]:
        if evaluator_token != "BENCHMARK_EVALUATOR_ONLY":
            raise PermissionError("Ground truth is isolated from runtime Agents.")
        with get_connection() as con, con.cursor() as cur:
            cur.execute(
                "SELECT control_id, expected_status, injected_faults, expected_actions FROM pc_ground_truth WHERE company_id=%s",
                (company_id,),
            )
            rows = cur.fetchall()
        return {
            r[0]: {"company_id": company_id, "control_id": r[0], "expected_status": r[1], "injected_faults": r[2], "expected_actions": r[3]}
            for r in rows
        }

    def append_audit_log(self, entry: dict[str, Any]) -> dict[str, Any]:
        with get_connection() as con, con.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pc_tool_audit_log (
                    company_id, action_id, actor, tool_name, risk_level,
                    dry_run, params_sha256, result_sha256, status
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING log_id, executed_at_utc
                """,
                (
                    entry["company_id"], entry.get("action_id"), entry["actor"],
                    entry["tool_name"], entry["risk_level"], bool(entry.get("dry_run", False)),
                    entry["params_sha256"], entry["result_sha256"], entry["status"],
                ),
            )
            log_id, executed_at = cur.fetchone()
        return {**entry, "log_id": log_id, "executed_at_utc": executed_at.isoformat()}

    def list_audit_logs(self, company_id: str) -> list[dict[str, Any]]:
        with get_connection() as con, con.cursor() as cur:
            cur.execute(
                """
                SELECT log_id, company_id, action_id, actor, tool_name, risk_level,
                       dry_run, params_sha256, result_sha256, status, executed_at_utc
                FROM pc_tool_audit_log WHERE company_id=%s ORDER BY log_id ASC
                """,
                (company_id,),
            )
            rows = cur.fetchall()
        cols = ["log_id", "company_id", "action_id", "actor", "tool_name", "risk_level", "dry_run", "params_sha256", "result_sha256", "status", "executed_at_utc"]
        out = []
        for r in rows:
            rec = dict(zip(cols, r))
            if rec["action_id"]:
                rec["action_id"] = str(rec["action_id"])
            rec["executed_at_utc"] = rec["executed_at_utc"].isoformat()
            out.append(rec)
        return out
