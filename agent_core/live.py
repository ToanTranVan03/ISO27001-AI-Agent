"""Persistent business events trigger the bounded agent on the server."""
import copy
import hashlib
import json
import logging
import threading
from datetime import timedelta

from agent_core.autonomous import AgentStore, ROOT, agent_events, now
from agent_core.simulation import build_enterprise, evaluate_enterprise
from agent_core.evidence_context import assessment_date

ACTIONS = {
    'terminate': 'Ghi nhận nghỉ việc',
    'recover_access': 'Thu hồi tài khoản và nhận lại laptop',
    'training_missing': 'Ghi nhận chưa hoàn tất đào tạo',
    'training_complete': 'Ghi nhận hoàn tất đào tạo và đạt kiểm tra',
    'training_unverified': 'Chưa xác minh được kết quả đào tạo (thiếu bằng chứng)',
    'training_expired': 'Ghi nhận chứng nhận đào tạo đã hết hạn',
    'training_conflict': 'Ghi nhận HR và LMS mâu thuẫn kết quả đào tạo',
    'role_change': 'Chuyển vai trò, chưa rà soát quyền cũ',
    'role_review': 'Xác nhận đã rà soát quyền theo vai trò mới',
    'retention_request': 'Nghỉ việc: đề nghị giữ tài khoản HR để bàn giao',
    'retention_approve': 'Ghi nhận quản lý phê duyệt ngoại lệ giữ HR (mô phỏng)',
    'retention_expire': 'Ghi nhận ngoại lệ giữ HR đã hết hạn',
    'advance_day': 'Chuyển ngày mô phỏng: tự đối chiếu thời hạn toàn doanh nghiệp',
    'nda_missing': 'Ghi nhận chưa ký NDA và cam kết lao động',
    'nda_signed': 'Ghi nhận đã ký NDA và cam kết lao động',
    'remote_unprotected': 'Làm từ xa, laptop và VPN chưa được bảo vệ',
    'remote_protected': 'Bật mã hóa laptop, MFA VPN và xác nhận chính sách',
    'screening_missing': 'Ghi nhận thiếu hồ sơ thẩm tra',
    'screening_complete': 'Bổ sung hồ sơ thẩm tra',
    'discipline_missing': 'Chưa phổ biến quy trình xử lý vi phạm',
    'discipline_complete': 'Đã phổ biến quy trình xử lý vi phạm',
    'report_missing': 'Ghi nhận sự kiện chưa được báo cáo',
    'report_complete': 'Ghi nhận đã hướng dẫn và báo cáo sự kiện',
}


def digest(enterprise):
    return hashlib.sha256(json.dumps(enterprise, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def evidence_changes(before, after):
    """Expose only changed fields with stable record IDs, preserving null as unknown."""
    changes = []
    if before.get('assessment_date') != after.get('assessment_date'):
        changes.append({'record_id': 'SIM-CLOCK', 'field': 'assessment_date',
                        'before': before.get('assessment_date'), 'after': after.get('assessment_date')})
    for group in ('person', 'accounts', 'devices'):
        old_records = [before[group]] if group == 'person' else before[group]
        new_records = [after[group]] if group == 'person' else after[group]
        old_by_id = {record['id']: record for record in old_records}
        for record in new_records:
            old = old_by_id.get(record['id'], {})
            for field in sorted(set(old) | set(record)):
                if old.get(field) != record.get(field):
                    changes.append({'record_id': record['id'], 'field': field,
                                    'before': old.get(field), 'after': record.get(field)})
    return changes


class LiveMonitor:
    def __init__(self, directory=None, mode='ai'):
        self.store = AgentStore(directory or ROOT / 'data' / 'live')
        self.mode = mode
        self.wake = threading.Event()
        self.stopping = threading.Event()
        self.run_lock = threading.Lock()
        self.thread_lock = threading.Lock()
        self.thread = None
        self.active_revision = None
        with self.store.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS live_state (
                    id INTEGER PRIMARY KEY CHECK(id=1), revision INTEGER,
                    processed_revision INTEGER, enterprise TEXT, status TEXT,
                    error TEXT, progress TEXT, report TEXT);
                CREATE TABLE IF NOT EXISTS live_events (
                    revision INTEGER PRIMARY KEY, created_at TEXT,
                    person_id TEXT, action TEXT, before_json TEXT, after_json TEXT);
            ''')
            db.execute('INSERT OR IGNORE INTO live_state VALUES (1,0,0,?,\'watching\',NULL,\'[]\',NULL)',
                       (json.dumps(build_enterprise(), ensure_ascii=False),))

    def start(self):
        with self.thread_lock:
            if self.thread is None or not self.thread.is_alive():
                self.stopping.clear()
                self.thread = threading.Thread(target=self._watch, name='hivefive-event-agent', daemon=True)
                self.thread.start()

    def stop(self):
        self.stopping.set()
        self.wake.set()
        if self.thread:
            self.thread.join(timeout=1)

    def _watch(self):
        while not self.stopping.is_set():
            self.wake.clear()
            try:
                while not self.stopping.is_set() and self.process_pending():
                    pass
            except Exception:
                logging.exception('HiveFive event monitor could not process pending evidence')
            self.wake.wait(timeout=2)

    def state(self):
        with self.store.connect() as db:
            row = db.execute('SELECT revision,processed_revision,enterprise,status,error,progress,report FROM live_state WHERE id=1').fetchone()
            events = db.execute('SELECT revision,created_at,person_id,action,before_json,after_json FROM live_events ORDER BY revision DESC LIMIT 20').fetchall()
        enterprise = json.loads(row[2])
        from agent_core.triad import analyze_triad
        return {'revision': row[0], 'processed_revision': row[1], 'enterprise': enterprise,
                'snapshot_hash': digest(enterprise), 'status': row[3], 'error': row[4],
                'progress': json.loads(row[5]), 'report': json.loads(row[6]) if row[6] else None,
                'controls': evaluate_enterprise(enterprise), 'mode': self.mode, 'active_revision': self.active_revision,
                'triad': analyze_triad(enterprise),
                'events': [dict(zip(('revision', 'created_at', 'person_id', 'action'), event[:4]),
                                changes=evidence_changes(json.loads(event[4]), json.loads(event[5]))) for event in events],
                'actions': [{'id': key, 'name': name} for key, name in ACTIONS.items()]}

    def change(self, person_id, action):
        if action not in ACTIONS:
            raise ValueError('Thao tác doanh nghiệp không hợp lệ.')
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            revision, payload = db.execute('SELECT revision,enterprise FROM live_state WHERE id=1').fetchone()
            enterprise = json.loads(payload)
            person = next((p for p in enterprise['people'] if p['id'] == person_id), None)
            if person is None:
                raise ValueError('Không tìm thấy nhân sự.')
            accounts = [a for a in enterprise['accounts'] if a['person_id'] == person_id]
            devices = [d for d in enterprise['devices'] if d['person_id'] == person_id]
            before = copy.deepcopy({'person': person, 'accounts': accounts, 'devices': devices,
                                    'assessment_date': assessment_date(enterprise).isoformat()})
            if action == 'advance_day':
                enterprise['assessment_date'] = (assessment_date(enterprise) + timedelta(days=1)).isoformat()
            elif action == 'terminate':
                person['status'] = 'terminated'
            elif action == 'recover_access':
                if person['status'] != 'terminated':
                    raise ValueError('Thao tác thu hồi khi nghỉ việc chỉ áp dụng cho người đã nghỉ việc.')
                for account in accounts:
                    account['active'] = False
                for device in devices:
                    device['returned'] = True
                person['post_employment_ack'] = True
            elif action in ('training_expired', 'training_conflict'):
                person.update(training_complete=True, training_passed=True)
                if action == 'training_expired':
                    person['training_valid_until'] = (assessment_date(enterprise) - timedelta(days=1)).isoformat()
                else:
                    person['lms_training_passed'] = False
            elif action.startswith('training_'):
                complete = None if action == 'training_unverified' else action == 'training_complete'
                person.update(training_complete=complete, training_passed=complete)
                if action == 'training_complete':
                    if 'training_valid_until' in person:
                        person['training_valid_until'] = (assessment_date(enterprise) + timedelta(days=365)).isoformat()
                    if 'lms_training_passed' in person:
                        person['lms_training_passed'] = True
            elif action in ('role_change', 'role_review'):
                if person['status'] != 'active':
                    raise ValueError('Chuyển vai trò và rà soát quyền chỉ áp dụng cho người đang làm việc.')
                if action == 'role_review' and not person.get('access_review_required'):
                    raise ValueError('Chưa có yêu cầu rà soát quyền khi chuyển vai trò.')
                person.update(role='Điều phối viên', access_review_required=True)
                for account in accounts:
                    account['role_reviewed'] = action == 'role_review'
            elif action.startswith('retention_'):
                if person['status'] != 'terminated':
                    raise ValueError('Ngoại lệ bàn giao chỉ áp dụng cho người đã nghỉ việc.')
                hr = next(a for a in accounts if a['system'] == 'HR')
                if action == 'retention_request':
                    for account in accounts:
                        account['active'] = account is hr
                    for device in devices:
                        device['returned'] = True
                    person['post_employment_ack'] = True
                    hr['retention_exception'] = {'account_id': hr['id'], 'scope': 'offboarding-retention',
                        'approved': False, 'approver': None, 'reason': 'Đối chiếu hồ sơ bàn giao (giả lập)',
                        'expires_on': (assessment_date(enterprise) + timedelta(days=1)).isoformat()}
                else:
                    exception = hr.get('retention_exception')
                    if not exception or not hr['active']:
                        raise ValueError('Cần đề nghị giữ tài khoản HR đang mở trước khi ghi nhận phê duyệt/hết hạn.')
                    if action == 'retention_approve':
                        exception.update(approved=True, approver='IT Manager (giả lập)')
                    else:
                        exception['expires_on'] = (assessment_date(enterprise) - timedelta(days=1)).isoformat()
            elif action.startswith('nda_'):
                signed = action == 'nda_signed'
                person.update(nda_signed=signed, terms_signed=signed)
            elif action.startswith('remote_'):
                protected = action == 'remote_protected'
                person.update(remote=True, remote_policy_ack=protected)
                for device in devices:
                    device['encrypted'] = protected
                for account in accounts:
                    if account['system'] == 'VPN':
                        account['mfa'] = protected
            elif action.startswith('screening_'):
                person['screened'] = action == 'screening_complete'
            elif action.startswith('discipline_'):
                person['disciplinary_informed'] = action == 'discipline_complete'
            elif action.startswith('report_'):
                complete = action == 'report_complete'
                person.update(reporting_trained=complete, event_reported=complete)
            after = {'person': person, 'accounts': accounts, 'devices': devices,
                     'assessment_date': assessment_date(enterprise).isoformat()}
            if before == after:
                return {'changed': False, 'revision': revision}
            revision += 1
            db.execute('INSERT INTO live_events VALUES (?,?,?,?,?,?)',
                       (revision, now(), person_id, action, json.dumps(before, ensure_ascii=False), json.dumps(after, ensure_ascii=False)))
            db.execute("UPDATE live_state SET revision=?,enterprise=?,status=CASE WHEN status='processing' THEN status ELSE 'pending' END,error=NULL WHERE id=1",
                       (revision, json.dumps(enterprise, ensure_ascii=False)))
        self.wake.set()
        return {'changed': True, 'revision': revision}

    def process_pending(self):
        if not self.run_lock.acquire(blocking=False):
            return False
        try:
            with self.store.connect() as db:
                revision, processed, payload = db.execute('SELECT revision,processed_revision,enterprise FROM live_state WHERE id=1').fetchone()
                if revision <= processed:
                    return False
                self.active_revision = revision
                triggers = db.execute('SELECT person_id,action FROM live_events WHERE revision>? AND revision<=? ORDER BY revision', (processed, revision)).fetchall()
                db.execute("UPDATE live_state SET status='processing',progress='[]',error=NULL WHERE id=1")
            enterprise = json.loads(payload)
            # Bound model context even when many changes are queued together.
            trigger_text = '; '.join(f'{pid}: {ACTIONS[action]}' for pid, action in triggers[-10:])
            goal = f'Tự kiểm tra sau thay đổi doanh nghiệp #{revision}: {trigger_text}. Xác định kiểm soát vi phạm, bằng chứng và cách xử lý.'[:1000]
            progress, report, error = [], None, None
            for event in agent_events(goal, self.mode, self.store, snapshot=(enterprise, f'HIVEFIVE-LIVE-r{revision}', digest(enterprise))):
                if event['type'] in ('action', 'tool_result'):
                    progress.append(event)
                    with self.store.connect() as db:
                        db.execute('UPDATE live_state SET progress=? WHERE id=1', (json.dumps(progress, ensure_ascii=False),))
                elif event['type'] == 'complete':
                    report = event['report']
                    report['trigger_revision'] = revision
                elif event['type'] == 'error':
                    error = event['message']
            if report is None and error is None:
                error = 'Agent chưa hoàn tất kiểm tra sự kiện.'
            with self.store.connect() as db:
                db.execute("UPDATE live_state SET processed_revision=?,status=CASE WHEN revision>? THEN 'pending' ELSE ? END,error=?,report=COALESCE(?,report) WHERE id=1",
                           (revision, revision, 'failed' if error else 'complete', error, json.dumps(report, ensure_ascii=False) if report else None))
            return True
        finally:
            self.run_lock.release()
