"""Sequential, database-tracked autonomous lab audit of ISO A.6/A.7/A.8 controls.

No evidence uploads. Missing evidence is recorded as a gap, not fabricated.
Workers are in-process for the local prototype; interrupted runs are explicitly
marked INTERRUPTED on restart. For production use a persistent task queue.
"""
import logging
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import errors
from psycopg.types.json import Jsonb

from backend import database, teamwork, auto_sources
from backend.team_api import execute_agent_job, require_campaign, require_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Autonomous lab audit"])
worker_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="auto-audit")


def initialize_auto_audit():
    """Additive tables; preserves existing assessment and evaluation records."""
    with database.get_connection() as con:
        with con.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS auto_audit_runs (
                    run_id UUID PRIMARY KEY,
                    assessment_id UUID NOT NULL REFERENCES assessment_campaigns(assessment_id),
                    created_by UUID NOT NULL REFERENCES team_users(user_id),
                    status TEXT NOT NULL CHECK(status IN (
                        'RUNNING','COMPLETED','COMPLETED_WITH_GAPS','FAILED','INTERRUPTED')),
                    total INTEGER NOT NULL,
                    processed INTEGER NOT NULL DEFAULT 0,
                    gaps INTEGER NOT NULL DEFAULT 0,
                    failed INTEGER NOT NULL DEFAULT 0,
                    current_control TEXT,
                    error_message TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    finished_at TIMESTAMPTZ
                )
            """)
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS auto_audit_one_running
                ON auto_audit_runs(assessment_id) WHERE status='RUNNING'
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS auto_audit_events (
                    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    run_id UUID NOT NULL REFERENCES auto_audit_runs(run_id) ON DELETE CASCADE,
                    control_id TEXT,
                    event_type TEXT NOT NULL,
                    details JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            # An interrupted process cannot claim that evaluation finished.
            cur.execute("""
                UPDATE auto_audit_runs SET status='INTERRUPTED',
                    error_message='API restarted while Auto-Audit was running',
                    finished_at=NOW()
                WHERE status='RUNNING' RETURNING run_id
            """)
            for (run_id,) in cur.fetchall():
                _event(cur, str(run_id), None, "RUN_INTERRUPTED", {
                    "message": "API restarted; previous run stopped. Start a new run to retry."})


def _event(cur, run_id, control_id, kind, details=None):
    cur.execute("""
        INSERT INTO auto_audit_events(run_id,control_id,event_type,details)
        VALUES(%s,%s,%s,%s)
    """, (run_id, control_id, kind, Jsonb(details or {})))


def control_scope():
    controls = database.list_controls()
    return sorted(
        [c["control_id"] for c in controls if c["control_id"].startswith(("A.6.", "A.7.", "A.8."))],
        key=lambda c: tuple(int(x) for x in c.split(".")[1:]),
    )


def create_run(assessment_id, user_id):
    controls = control_scope()
    if not controls:
        raise ValueError("No ISO control records exist in the database.")
    run_id = str(uuid4())
    try:
        with database.get_connection() as con:
            with con.cursor() as cur:
                cur.execute("""
                    INSERT INTO auto_audit_runs(run_id,assessment_id,created_by,status,total)
                    VALUES(%s,%s,%s,'RUNNING',%s)
                """, (run_id, assessment_id, user_id, len(controls)))
                _event(cur, run_id, None, "RUN_STARTED", {
                    "total": len(controls), "mode": "SYNTHETIC_ENTERPRISE_LAB",
                    "message": "Started a real backend workflow; lab evidence may be synthetic."})
    except errors.UniqueViolation as exc:
        raise ValueError("This assessment already has an active Auto-Audit.") from exc
    return run_id, controls


def finish_run(run_id, status, error=None):
    with database.get_connection() as con:
        with con.cursor() as cur:
            cur.execute("""
                UPDATE auto_audit_runs SET status=%s, error_message=%s,
                    current_control=NULL, finished_at=NOW()
                WHERE run_id=%s AND status='RUNNING'
                RETURNING processed,total,gaps,failed
            """, (status, error, run_id))
            values = cur.fetchone()
            if values:
                _event(cur, run_id, None, "RUN_FINISHED", {
                    "status": status, "processed": values[0], "total": values[1],
                    "gaps": values[2], "failed": values[3], "error": error,
                    "message": "Evaluation summary; no ISO certification is implied."})


def mark_one_done(run_id, control_id, outcome, result=None, error_type=None):
    gap = outcome in ("WAITING_EVIDENCE", "NEEDS_REVIEW")
    failed = outcome == "FAILED"
    with database.get_connection() as con:
        with con.cursor() as cur:
            cur.execute("""
                UPDATE auto_audit_runs SET processed=processed+1,
                  gaps=gaps+%s, failed=failed+%s,
                  current_control=NULL
                WHERE run_id=%s AND status='RUNNING'
            """, (int(gap), int(failed), run_id))
            for step in (result or {}).get("audit_trail", [])[:30]:
                # Saved by LangGraph; not fabricated browser events.
                _event(cur, run_id, control_id, "PIPELINE_STEP", {"step": str(step)[:250]})
            _event(cur, run_id, control_id, "CONTROL_FINISHED", {
                "workflow_status": outcome,
                "compliance_status": (result or {}).get("compliance_status"),
                "evaluation_id": (result or {}).get("evaluation_id"),
                "evidence_count": (result or {}).get("evidence_count", 0),
                "synthetic_evidence_count": (result or {}).get("synthetic_evidence_count", 0),
                "message": "Missing evidence is recorded; run proceeds to next control." if gap else "Control processing ended.",
                "error_type": error_type
            })


def _read_result(assessment_id, control_id):
    """Never manufacture evidence; report only saved references."""
    with database.get_connection() as con:
        with con.cursor() as cur:
            cur.execute("""
                SELECT p.workflow_status,p.compliance_status,p.latest_evaluation_id,
                       e.evidence_ids,e.audit_trail
                FROM control_progress p
                LEFT JOIN evaluations e ON e.evaluation_id=p.latest_evaluation_id
                WHERE p.assessment_id=%s AND p.control_id=%s
            """, (assessment_id, control_id))
            row = cur.fetchone()
            if not row:
                return "FAILED", None
            evidence_ids = row[3] or []
            synthetic = 0
            if evidence_ids:
                cur.execute("""
                    SELECT COUNT(*) FROM evidence
                    WHERE evidence_id = ANY(%s) AND (is_synthetic=TRUE OR is_sample=TRUE)
                """, (evidence_ids,))
                synthetic = cur.fetchone()[0]
    return row[0], {
        "compliance_status": row[1], "evaluation_id": row[2],
        "evidence_count": len(evidence_ids), "synthetic_evidence_count": synthetic,
        "audit_trail": row[4] or []
    }


def execute_run(run_id, assessment_id, user_id, controls):
    try:
        for control_id in controls:
            with database.get_connection() as con:
                with con.cursor() as cur:
                    cur.execute("""
                        UPDATE auto_audit_runs SET current_control=%s
                        WHERE run_id=%s AND status='RUNNING'
                    """, (control_id, run_id))
                    _event(cur, run_id, control_id, "CONTROL_STARTED", {
                        "message": "Calling existing LangGraph PLAN/COLLECT/EVALUATE/VERIFY/REPORT pipeline."
                    })
            try:
                # Opt-in authorized folder only: source discovery happens before
                # the control is locked by claim_job(). No browser upload.
                def source_event(kind, details):
                    with database.get_connection() as source_con:
                        with source_con.cursor() as source_cur:
                            _event(source_cur, run_id, control_id, kind, details)
                auto_sources.import_for_control(
                    assessment_id, control_id, user_id, source_event
                )
                claim = teamwork.claim_job(assessment_id, control_id, user_id)
                with database.get_connection() as con:
                    with con.cursor() as cur:
                        _event(cur, run_id, control_id, "JOB_CLAIMED", {"job_id": claim["job_id"]})
                # Reuse the existing job executor: a true LangGraph/Ollama evaluation,
                # not a fabricated timer. Sequential execution avoids GPU overload.
                execute_agent_job(claim["job_id"], assessment_id, control_id)
                job = teamwork.get_job(claim["job_id"])
                outcome, result = _read_result(assessment_id, control_id)
                if not job or job["status"] != "SUCCEEDED":
                    outcome, result = "FAILED", None
                    if job:
                        source_event("JOB_FAILURE", {
                            "job_id": claim["job_id"],
                            "error": job.get("error_message") or "Job failed; inspect FastAPI logs."
                        })
                mark_one_done(run_id, control_id, outcome, result)
            except Exception as exc:
                logger.exception("Auto-Audit control %s failed", control_id)
                with database.get_connection() as con:
                    with con.cursor() as cur:
                        _event(cur, run_id, control_id, "CONTROL_ERROR", {
                            "category": type(exc).__name__,
                            "message": "Agent failed. Inspect backend console logs for traceback."
                        })
                mark_one_done(run_id, control_id, "FAILED", error_type=type(exc).__name__)
        with database.get_connection() as con:
            with con.cursor() as cur:
                cur.execute("SELECT gaps,failed FROM auto_audit_runs WHERE run_id=%s", (run_id,))
                gaps, failures = cur.fetchone()
        finish_run(run_id, "COMPLETED_WITH_GAPS" if gaps or failures else "COMPLETED")
    except Exception:
        logger.exception("Auto-Audit run %s failed", run_id)
        finish_run(run_id, "FAILED", "Auto-Audit interrupted by a backend error.")


def _serialize_run(row):
    return {
        "run_id": str(row[0]), "assessment_id": str(row[1]), "status": row[2],
        "total": row[3], "processed": row[4], "gaps": row[5],
        "failed": row[6], "current_control": row[7], "error_message": row[8],
        "created_at": row[9].isoformat(),
        "finished_at": row[10].isoformat() if row[10] else None,
        "mode": "SYNTHETIC_ENTERPRISE_LAB",
    }


def get_run(run_id):
    with database.get_connection() as con:
        with con.cursor() as cur:
            cur.execute("""
                SELECT run_id,assessment_id,status,total,processed,gaps,failed,
                       current_control,error_message,created_at,finished_at
                FROM auto_audit_runs WHERE run_id=%s
            """, (run_id,))
            row = cur.fetchone()
    return _serialize_run(row) if row else None


@router.post("/assessments/{assessment_id}/auto-audits", status_code=202)
def start_auto_audit(assessment_id: UUID, user: dict = Depends(require_user)):
    require_campaign(assessment_id, user)
    try:
        run_id, controls = create_run(str(assessment_id), user["user_id"])
    except ValueError as exc:
        raise HTTPException(409, detail=str(exc)) from exc
    try:
        worker_pool.submit(execute_run, run_id, str(assessment_id), user["user_id"], controls)
    except RuntimeError as exc:
        finish_run(run_id, "FAILED", "Worker unavailable")
        raise HTTPException(503, detail="Worker unavailable") from exc
    return get_run(run_id)


@router.get("/assessments/{assessment_id}/auto-audits/latest")
def latest_auto_audit(assessment_id: UUID, user: dict = Depends(require_user)):
    require_campaign(assessment_id, user)
    with database.get_connection() as con:
        with con.cursor() as cur:
            cur.execute("""
                SELECT run_id FROM auto_audit_runs
                WHERE assessment_id=%s ORDER BY created_at DESC, run_id DESC LIMIT 1
            """, (str(assessment_id),))
            row = cur.fetchone()
    return get_run(str(row[0])) if row else None


@router.get("/auto-audits/{run_id}")
def read_auto_audit(run_id: UUID, user: dict = Depends(require_user)):
    run = get_run(str(run_id))
    if not run:
        raise HTTPException(404, detail="Auto-Audit run not found")
    require_campaign(UUID(run["assessment_id"]), user)
    return run


@router.get("/auto-audits/{run_id}/events")
def read_auto_events(run_id: UUID, after: int = Query(0, ge=0),
                     user: dict = Depends(require_user)):
    run = get_run(str(run_id))
    if not run:
        raise HTTPException(404, detail="Auto-Audit run not found")
    require_campaign(UUID(run["assessment_id"]), user)
    with database.get_connection() as con:
        with con.cursor() as cur:
            cur.execute("""
                SELECT event_id,control_id,event_type,details,created_at
                FROM auto_audit_events WHERE run_id=%s AND event_id>%s
                ORDER BY event_id ASC LIMIT 200
            """, (str(run_id), after))
            rows = cur.fetchall()
    return [{"event_id": r[0], "control_id": r[1], "event_type": r[2],
             "details": r[3], "created_at": r[4].isoformat()} for r in rows]


@router.get("/auto-audits/{run_id}/failures")
def read_auto_failures(run_id: UUID, user: dict = Depends(require_user)):
    """Details of failed controls in a historical run; permissions scoped by campaign."""
    run = get_run(str(run_id))
    if not run:
        raise HTTPException(404, detail="Auto-Audit run not found")
    require_campaign(UUID(run["assessment_id"]), user)
    with database.get_connection() as con:
        with con.cursor() as cur:
            cur.execute("""
                SELECT e.control_id,
                       (SELECT x.details->>'job_id'
                        FROM auto_audit_events x
                        WHERE x.run_id=e.run_id AND x.control_id=e.control_id
                          AND x.event_type='JOB_CLAIMED'
                        ORDER BY x.event_id DESC LIMIT 1),
                       e.details->>'error_type'
                FROM auto_audit_events e
                WHERE e.run_id=%s
                  AND e.event_type='CONTROL_FINISHED'
                  AND e.details->>'workflow_status'='FAILED'
                ORDER BY e.event_id ASC
            """, (str(run_id),))
            rows = cur.fetchall()
    result = []
    for control_id, job_id, error_type in rows:
        job = teamwork.get_job(job_id) if job_id else None
        result.append({
            "control_id": control_id,
            "job_id": job_id,
            "job_status": job.get("status") if job else None,
            "reason": job.get("error_message") if job else None,
            "error_type": error_type,
        })
    return {"run_id": str(run_id), "failed_controls": result, "count": len(result)}


@router.get("/assessments/{assessment_id}/auto-audits/sources")
def source_status(assessment_id: UUID, user: dict = Depends(require_user)):
    """Read-only source readiness; no full local path or document contents exposed."""
    require_campaign(assessment_id, user)
    try:
        _, entries = auto_sources.get_manifest()
        return {
            "enabled": auto_sources.source_directory() is not None,
            "configured_items": len(entries),
            "message": "Source folder is opt-in; each manifest item is validated before indexing.",
        }
    except auto_sources.SourceConfigurationError as exc:
        return {"enabled": True, "configured_items": 0, "error": str(exc)}
