"""Shared assessment store for the local ISO Enterprise Lab MVP.

All concurrency decisions occur in PostgreSQL (not in browser or Python process).
Do not confuse workflow completion with ISO compliance.
"""
import hashlib
import hmac
import os
import re
import secrets
from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4, uuid5, NAMESPACE_URL
from typing import Any

from psycopg.types.json import Jsonb
from backend.database import get_connection

DEMO_ASSESSMENT_ID = str(uuid5(NAMESPACE_URL, 'iso-enterprise-lab/default-assessment/v1'))
USER_RE = re.compile(r'^[A-Za-z0-9_.-]{3,40}$')
WORKFLOW = {'NOT_STARTED', 'RUNNING', 'WAITING_EVIDENCE', 'NEEDS_REVIEW', 'COMPLETED', 'FAILED'}
COMPLIANCE = {'Compliant', 'Partially Compliant', 'Non-Compliant', 'Not Applicable', 'Insufficient Evidence'}


def hash_password(password: str) -> str:
    if len(password) < 12:
        raise ValueError('Mật khẩu phải có ít nhất 12 ký tự.')
    salt = secrets.token_bytes(16)
    result = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 310_000)
    return f'pbkdf2_sha256$310000${salt.hex()}${result.hex()}'


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt_hex, digest_hex = encoded.split('$')
        if algorithm != 'pbkdf2_sha256' or int(rounds) > 1_000_000:
            return False
        actual = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt_hex), int(rounds))
        return hmac.compare_digest(actual, bytes.fromhex(digest_hex))
    except (ValueError, TypeError):
        return False


def init_teamwork() -> None:
    """Idempotent schema creation. Existing Khoa project tables remain intact."""
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS team_users (
                    user_id UUID PRIMARY KEY, username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL, display_name TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('admin', 'assessor')),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS team_sessions (
                    token_hash TEXT PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES team_users(user_id) ON DELETE CASCADE,
                    expires_at TIMESTAMPTZ NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS assessment_campaigns (
                    assessment_id UUID PRIMARY KEY, name TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS assessment_members (
                    assessment_id UUID REFERENCES assessment_campaigns(assessment_id) ON DELETE CASCADE,
                    user_id UUID REFERENCES team_users(user_id) ON DELETE CASCADE,
                    PRIMARY KEY (assessment_id, user_id)
                )''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS control_progress (
                    assessment_id UUID NOT NULL REFERENCES assessment_campaigns(assessment_id),
                    control_id TEXT NOT NULL REFERENCES controls(control_id),
                    workflow_status TEXT NOT NULL DEFAULT 'NOT_STARTED',
                    compliance_status TEXT,
                    assigned_to UUID REFERENCES team_users(user_id),
                    active_job_id UUID,
                    latest_evaluation_id BIGINT REFERENCES evaluations(evaluation_id),
                    started_at TIMESTAMPTZ,
                    completed_at TIMESTAMPTZ,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (assessment_id, control_id)
                )''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS agent_jobs (
                    job_id UUID PRIMARY KEY,
                    assessment_id UUID NOT NULL,
                    control_id TEXT NOT NULL,
                    user_id UUID NOT NULL REFERENCES team_users(user_id),
                    status TEXT NOT NULL,
                    error_message TEXT,
                    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    finished_at TIMESTAMPTZ,
                    FOREIGN KEY (assessment_id, control_id)
                       REFERENCES control_progress(assessment_id, control_id)
                )''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS assessment_events (
                    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    assessment_id UUID NOT NULL,
                    control_id TEXT,
                    user_id UUID,
                    event_type TEXT NOT NULL,
                    details JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )''')
            # Migration: attach each upload and evaluation to a campaign (nullable for legacy data).
            cur.execute('ALTER TABLE evidence ADD COLUMN IF NOT EXISTS assessment_id UUID')
            cur.execute('ALTER TABLE evidence ADD COLUMN IF NOT EXISTS uploaded_by UUID')
            cur.execute('ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS assessment_id UUID')
            cur.execute('ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS evaluated_by UUID')
            cur.execute('ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS agent_job_id UUID')
            cur.execute('''INSERT INTO assessment_campaigns (assessment_id, name)
                           VALUES (%s, 'ISO Enterprise Lab — Đánh giá nhóm 11')
                           ON CONFLICT DO NOTHING''', (DEMO_ASSESSMENT_ID,))
            cur.execute('''INSERT INTO control_progress (assessment_id, control_id)
                           SELECT %s, control_id FROM controls
                           ON CONFLICT DO NOTHING''', (DEMO_ASSESSMENT_ID,))
            # Interrupted thread-based jobs must never leave controls locked after API restart.
            cur.execute("UPDATE agent_jobs SET status='INTERRUPTED', finished_at=NOW(), error_message='API restarted during evaluation' WHERE status='RUNNING'")
            cur.execute("UPDATE control_progress SET workflow_status='FAILED', active_job_id=NULL, updated_at=NOW() WHERE workflow_status='RUNNING'")
            # Default team is shared intentionally in this single-enterprise MVP.
            cur.execute('''INSERT INTO assessment_members (assessment_id, user_id)
                           SELECT %s, user_id FROM team_users ON CONFLICT DO NOTHING''',
                        (DEMO_ASSESSMENT_ID,))
            cur.execute("CREATE TABLE IF NOT EXISTS login_attempts (username TEXT NOT NULL, attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
            cur.execute("CREATE INDEX IF NOT EXISTS login_attempts_idx ON login_attempts(username,attempted_at)")
            cur.execute('SELECT COUNT(*) FROM team_users')
            has_users = cur.fetchone()[0] > 0
            if not has_users:
                username = os.getenv('INITIAL_ADMIN_USERNAME', '').strip()
                password = os.getenv('INITIAL_ADMIN_PASSWORD', '')
                if not USER_RE.fullmatch(username) or len(password) < 12:
                    raise RuntimeError('First run requires INITIAL_ADMIN_USERNAME and INITIAL_ADMIN_PASSWORD (>=12 characters) in .env')
                user_id = str(uuid4())
                cur.execute('''INSERT INTO team_users (user_id, username, password_hash, display_name, role)
                               VALUES (%s,%s,%s,%s,'admin')''',
                            (user_id, username, hash_password(password), username))
                cur.execute('''INSERT INTO assessment_members (assessment_id, user_id)
                               VALUES (%s,%s) ON CONFLICT DO NOTHING''',
                            (DEMO_ASSESSMENT_ID, user_id))


def create_user(actor: dict[str, Any], username: str, display_name: str, password: str) -> dict:
    if actor['role'] != 'admin':
        raise PermissionError('Only admin may create members.')
    if not USER_RE.fullmatch(username):
        raise ValueError('Username: 3–40 ký tự, chữ/số/_.-')
    if not display_name.strip() or len(display_name) > 100:
        raise ValueError('Display name invalid.')
    uid = str(uuid4())
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute('''INSERT INTO team_users(user_id,username,password_hash,display_name,role)
                           VALUES (%s,%s,%s,%s,'assessor')''',
                        (uid, username, hash_password(password), display_name.strip()))
            cur.execute('''INSERT INTO assessment_members (assessment_id,user_id)
                           VALUES (%s,%s)''', (DEMO_ASSESSMENT_ID,uid))
    return {'user_id':uid, 'username':username, 'display_name':display_name, 'role':'assessor'}


def login(username: str, password: str) -> dict | None:
    # DB-backed throttle: five failed attempts lock the username for 15 minutes.
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM login_attempts WHERE username=%s AND attempted_at>NOW()-INTERVAL '15 minutes'", (username,))
            if cur.fetchone()[0]>=5:
                return None
            cur.execute('SELECT user_id,username,password_hash,display_name,role FROM team_users WHERE username=%s',(username,))
            user=cur.fetchone()
            if not user or not verify_password(password,user[2]):
                cur.execute('INSERT INTO login_attempts(username) VALUES (%s)',(username,))
                return None
            cur.execute('DELETE FROM login_attempts WHERE username=%s',(username,))
            token=secrets.token_urlsafe(40)
            expires=datetime.now(timezone.utc)+timedelta(hours=8)
            cur.execute('INSERT INTO team_sessions(token_hash,user_id,expires_at) VALUES (%s,%s,%s)',(hashlib.sha256(token.encode()).hexdigest(),user[0],expires))
            return {'access_token':token,'expires_at':expires.isoformat(),
                    'user':{'user_id':str(user[0]),'username':user[1],
                            'display_name':user[3],'role':user[4]}}


def store_campaign_evidence(assessment_id: str, control_id: str, user_id: str,
                            evidence_id: str, evidence_type: str, source: str,
                            extracted_text: str, sha256_hash: str) -> None:
    """Atomic upload vs. evaluate lock: avoid changing evidence while a job runs."""
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute('SELECT workflow_status FROM control_progress WHERE assessment_id=%s AND control_id=%s FOR UPDATE',(assessment_id,control_id))
            row=cur.fetchone()
            if not row:raise ValueError('Control không thuộc đợt đánh giá.')
            if row[0]=='RUNNING':raise ValueError('Control đang đánh giá, không thể thêm bằng chứng lúc này.')
            cur.execute('INSERT INTO evidence(evidence_id,control_id,evidence_type,source,extracted_text,sha256_hash,assessment_id,uploaded_by) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',(evidence_id,control_id,evidence_type,source,extracted_text,sha256_hash,assessment_id,user_id))
            log_event(cur,assessment_id,control_id,user_id,'EVIDENCE_UPLOADED',{'evidence_id':evidence_id})

def get_user_from_token(token: str) -> dict | None:
    if not token or len(token) > 200:
        return None
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute('''SELECT u.user_id,u.username,u.display_name,u.role
                           FROM team_sessions s JOIN team_users u ON s.user_id=u.user_id
                           WHERE s.token_hash=%s AND s.expires_at>NOW()''',
                        (hashlib.sha256(token.encode()).hexdigest(),))
            user=cur.fetchone()
    return None if not user else {'user_id':str(user[0]),'username':user[1],
                                  'display_name':user[2],'role':user[3]}


def logout(token: str) -> None:
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute('DELETE FROM team_sessions WHERE token_hash=%s',
                        (hashlib.sha256(token.encode()).hexdigest(),))


def require_member(assessment_id: str, user_id: str) -> None:
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute('''SELECT 1 FROM assessment_members
                           WHERE assessment_id=%s AND user_id=%s''', (assessment_id,user_id))
            if not cur.fetchone():
                raise PermissionError('You are not a member of this assessment.')


def list_assessments(user_id: str) -> list[dict]:
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute('''SELECT c.assessment_id,c.name FROM assessment_campaigns c
                           JOIN assessment_members m USING (assessment_id)
                           WHERE m.user_id=%s ORDER BY c.created_at''',(user_id,))
            return [{'assessment_id':str(row[0]),'name':row[1]} for row in cur.fetchall()]


def progress_board(assessment_id: str) -> list[dict]:
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute('''SELECT p.control_id,c.name,c.group_name,c.objective,
                                  c.expected_evidence_types,p.workflow_status,p.compliance_status,
                                  u.display_name,p.active_job_id,p.updated_at,p.completed_at,
                                  p.latest_evaluation_id
                           FROM control_progress p JOIN controls c USING(control_id)
                           LEFT JOIN team_users u ON u.user_id=p.assigned_to
                           WHERE p.assessment_id=%s
                           ORDER BY split_part(p.control_id,'.',2)::int,
                                    split_part(p.control_id,'.',3)::int''',(assessment_id,))
            rows = cur.fetchall()
    return [{'control_id':r[0], 'name':r[1], 'group':r[2], 'objective':r[3],
             'expected_evidence_types':r[4], 'workflow_status':r[5],
             'compliance_status':r[6], 'assigned_to':r[7],
             'active_job_id':str(r[8]) if r[8] else None,
             'updated_at':r[9].isoformat(),
             'completed_at':r[10].isoformat() if r[10] else None,
             'latest_evaluation_id':r[11]} for r in rows]


def log_event(cur, assessment_id: str, control_id: str | None, user_id: str | None, event: str, details: dict | None = None):
    cur.execute('''INSERT INTO assessment_events(assessment_id,control_id,user_id,event_type,details)
                   VALUES (%s,%s,%s,%s,%s)''',
                (assessment_id,control_id,user_id,event,Jsonb(details or {})))


def claim_job(assessment_id: str, control_id: str, user_id: str) -> dict:
    """Atomic optimistic lock: only one concurrent click may claim the control."""
    job_id = str(uuid4())
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute('''UPDATE control_progress SET workflow_status='RUNNING',
                           assigned_to=%s, active_job_id=%s, started_at=NOW(),
                           completed_at=NULL, updated_at=NOW()
                           WHERE assessment_id=%s AND control_id=%s
                             AND workflow_status <> 'RUNNING'
                           RETURNING control_id''', (user_id,job_id,assessment_id,control_id))
            if not cur.fetchone():
                raise ValueError('CONTROL_BUSY_OR_NOT_FOUND')
            cur.execute('''INSERT INTO agent_jobs(job_id,assessment_id,control_id,user_id,status)
                           VALUES (%s,%s,%s,%s,'RUNNING')''',
                        (job_id,assessment_id,control_id,user_id))
            log_event(cur,assessment_id,control_id,user_id,'JOB_STARTED',{'job_id':job_id})
    return {'job_id':job_id,'workflow_status':'RUNNING'}


def finish_job(job_id: str, result: dict | None, error: str | None = None) -> None:
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute('''SELECT assessment_id,control_id,user_id FROM agent_jobs
                           WHERE job_id=%s AND status='RUNNING' FOR UPDATE''',(job_id,))
            job=cur.fetchone()
            if not job:return
            assessment_id,control_id,user_id=map(str,job)
            if error:
                cur.execute('''UPDATE agent_jobs SET status='FAILED',error_message=%s,
                               finished_at=NOW() WHERE job_id=%s''',(error[:700],job_id))
                cur.execute('''UPDATE control_progress SET workflow_status='FAILED',
                               active_job_id=NULL, updated_at=NOW()
                               WHERE assessment_id=%s AND control_id=%s
                                 AND active_job_id=%s''',(assessment_id,control_id,job_id))
                log_event(cur,assessment_id,control_id,user_id,'JOB_FAILED',{'job_id':job_id,'reason':error[:240]})
                return
            status=result['status']
            if status not in COMPLIANCE:
                raise ValueError('Invalid compliance status from Agent.')
            flow = 'WAITING_EVIDENCE' if status=='Insufficient Evidence' else ('NEEDS_REVIEW' if status=='Not Applicable' else 'COMPLETED')
            cur.execute('''INSERT INTO evaluations(control_id,status,confidence,rationale,
                           evidence_ids,audit_trail,assessment_id,evaluated_by,agent_job_id)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING evaluation_id''',
                        (control_id,status,result['confidence'],result['rationale'],
                         Jsonb(result['evidence_ids']),Jsonb(result['audit_trail']),
                         assessment_id,user_id,job_id))
            eval_id=cur.fetchone()[0]
            cur.execute('''UPDATE agent_jobs SET status='SUCCEEDED',finished_at=NOW() WHERE job_id=%s''',(job_id,))
            cur.execute('''UPDATE control_progress SET workflow_status=%s,
                           compliance_status=%s, latest_evaluation_id=%s,
                           active_job_id=NULL, updated_at=NOW(),
                           completed_at=CASE WHEN %s='COMPLETED' THEN NOW() ELSE NULL END
                           WHERE assessment_id=%s AND control_id=%s AND active_job_id=%s''',
                        (flow,status,eval_id,flow,assessment_id,control_id,job_id))
            log_event(cur,assessment_id,control_id,user_id,'JOB_FINISHED',
                      {'job_id':job_id,'evaluation_id':eval_id,'status':status,'workflow_status':flow})


def get_job(job_id: str) -> dict | None:
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute('''SELECT job_id,assessment_id,control_id,status,error_message,started_at,finished_at
                           FROM agent_jobs WHERE job_id=%s''',(job_id,))
            row=cur.fetchone()
    if not row:return None
    return {'job_id':str(row[0]),'assessment_id':str(row[1]),'control_id':row[2],
            'status':row[3],'error_message':row[4],
            'started_at':row[5].isoformat(),
            'finished_at':row[6].isoformat() if row[6] else None}


def list_history(assessment_id: str, control_id: str) -> list[dict]:
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute('''SELECT e.evaluation_id,e.status,e.confidence,e.rationale,
                                  e.evidence_ids,e.audit_trail,e.created_at,u.display_name
                           FROM evaluations e LEFT JOIN team_users u ON e.evaluated_by=u.user_id
                           WHERE e.assessment_id=%s AND e.control_id=%s
                           ORDER BY e.evaluation_id DESC LIMIT 30''',(assessment_id,control_id))
            rows=cur.fetchall()
    return [{'evaluation_id':r[0],'status':r[1],'confidence':r[2],
             'rationale':r[3],'evidence_ids':r[4],'audit_trail':r[5],
             'created_at':r[6].isoformat(),'performed_by':r[7]} for r in rows]


def evidence_uploaded(assessment_id: str, control_id: str, user_id: str, evidence_id: str) -> None:
    with get_connection() as con:
        with con.cursor() as cur:
            log_event(cur,assessment_id,control_id,user_id,'EVIDENCE_UPLOADED',{'evidence_id':evidence_id})


def review(assessment_id: str, control_id: str, user_id: str, note: str) -> None:
    if len(note.strip()) < 5:
        raise ValueError('Hãy nhập lý do xác nhận tối thiểu 5 ký tự.')
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute('''UPDATE control_progress SET workflow_status='COMPLETED',
                           completed_at=NOW(),updated_at=NOW()
                           WHERE assessment_id=%s AND control_id=%s
                             AND workflow_status='NEEDS_REVIEW' RETURNING control_id''',
                        (assessment_id,control_id))
            if not cur.fetchone():raise ValueError('Control is not awaiting review.')
            log_event(cur,assessment_id,control_id,user_id,'HUMAN_APPROVED',{'note':note.strip()})
