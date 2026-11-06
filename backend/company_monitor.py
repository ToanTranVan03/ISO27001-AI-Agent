"""Live projections read the shared PostgreSQL company; SQLite holds task traces only."""
import os
import threading
from pathlib import Path
from psycopg.types.json import Jsonb
from agent_core.live import LiveMonitor, ACTIONS, evidence_changes
from agent_core.autonomous import AgentStore, agent_events
from agent_core.simulation import evaluate_enterprise
from agent_core.triad import analyze_triad
from backend.database import get_connection
from backend import company


class CompanyMonitor(LiveMonitor):
    def __init__(self, assessment_id):
        self.assessment_id = str(assessment_id)
        self.store = AgentStore(Path(__file__).resolve().parent.parent / 'work' / 'company-traces' / self.assessment_id)
        self.mode = os.getenv('LIVE_AGENT_MODE', 'workflow')
        self.thread = None
        self.thread_lock = threading.Lock()
        self.run_lock = threading.Lock()
        self.stopping = threading.Event()
        self.wake = threading.Event()
        self.active_revision = None

    def state(self):
        data = company.snapshot(self.assessment_id)
        with get_connection() as con, con.cursor() as cur:
            cur.execute('SELECT metadata FROM enterprise_company WHERE assessment_id=%s', (self.assessment_id,))
            metadata = cur.fetchone()[0]
            cur.execute('''SELECT change_id,created_at,employee_id,action,before_state,after_state,submitted_by
                FROM enterprise_company_changes WHERE assessment_id=%s ORDER BY change_id DESC LIMIT 20''', (self.assessment_id,))
            events = [{'revision': r[0], 'created_at': r[1].isoformat(), 'person_id': r[2], 'action': r[3],
                       'submitted_by': str(r[6]) if r[6] else None,
                       'changes': evidence_changes(r[4], r[5])} for r in cur.fetchall()]
        report = metadata.get('live_report')
        current = metadata.get('processed_hash') == data['snapshot_hash']
        revision = int(data['snapshot_hash'][:12], 16)
        return {'assessment_id': self.assessment_id, 'revision': revision,
            'processed_revision': revision if current else None, 'enterprise': data,
            'snapshot_hash': data['snapshot_hash'], 'status': ('failed' if metadata.get('live_error') else 'complete') if current else ('processing' if self.run_lock.locked() else 'pending'),
            'error': metadata.get('live_error'), 'progress': [], 'report': report, 'report_current': current,
            'controls': evaluate_enterprise(data), 'mode': self.mode, 'active_revision': self.active_revision,
            'triad': analyze_triad(data), 'events': events,
            'actions': [{'id': key, 'name': name} for key, name in ACTIONS.items()]}

    def change(self, person_id, action, actor_id=None):
        result = company.change(self.assessment_id, person_id, action, actor_id=actor_id)
        self.wake.set()
        return result

    def process_pending(self):
        if not self.run_lock.acquire(blocking=False):
            return False
        try:
            data = company.snapshot(self.assessment_id)
            with get_connection() as con, con.cursor() as cur:
                cur.execute('SELECT metadata FROM enterprise_company WHERE assessment_id=%s', (self.assessment_id,))
                if cur.fetchone()[0].get('processed_hash') == data['snapshot_hash']:
                    return False
            self.active_revision = int(data['snapshot_hash'][:12], 16)
            report, error = None, None
            for event in agent_events('Kiểm tra bằng chứng doanh nghiệp hiện tại.', self.mode, self.store,
                    snapshot=(data, f'company:{self.assessment_id}', data['snapshot_hash'])):
                if event['type'] == 'complete':
                    report = event['report']
                    report['trigger_revision'] = self.active_revision
                elif event['type'] == 'error':
                    error = event['message']
            if report is None and error is None:
                error = 'Agent chưa hoàn tất kiểm tra snapshot.'
            with get_connection() as con, con.cursor() as cur:
                cur.execute('UPDATE enterprise_company SET metadata=metadata||%s WHERE assessment_id=%s',
                    (Jsonb({'processed_hash': data['snapshot_hash'], 'live_report': report, 'live_error': error}), self.assessment_id))
            return True
        finally:
            self.active_revision = None
            self.run_lock.release()
