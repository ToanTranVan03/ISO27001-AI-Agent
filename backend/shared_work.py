"""Shared assessment queue: reuse fresh results; never equate execution with compliance."""
import hashlib
import json
from backend import teamwork
from backend.database import get_connection


def dossier(assessment_id):
    from backend.compliance_report import build_dossier, campaign_evidence
    from backend.company import snapshot
    board = teamwork.progress_board(assessment_id)
    history = {c['control_id']: teamwork.list_history(assessment_id, c['control_id'])
               for c in board if c.get('latest_evaluation_id')}
    return build_dossier(assessment_id, board, campaign_evidence(assessment_id), history, snapshot(assessment_id))


def state(control):
    if control['workflow_status'] == 'RUNNING':
        return 'running'
    if control['assessment_state'] == 'stale':
        return 'stale'
    if control['workflow_status'] == 'FAILED':
        return 'failed'
    if control['assessment_state'] == 'not_evaluated':
        return 'not_started'
    if control['workflow_status'] == 'NEEDS_REVIEW':
        return 'awaiting_review'
    if control['workflow_status'] == 'WAITING_EVIDENCE':
        return 'waiting_evidence'
    return 'evaluated'


def board(assessment_id):
    report = dossier(assessment_id)
    for c in report['controls']:
        c['shared_state'] = state(c)
    candidates = [c for c in report['controls'] if c['collector_supported'] and
                  c['shared_state'] in ('not_started', 'stale', 'failed')]
    candidates.sort(key=lambda c: (0 if c['shared_state'] == 'stale' else 1,
                                   tuple(int(x) for x in c['control_id'].split('.')[1:])))
    report['next_control_id'] = candidates[0]['control_id'] if candidates else None
    report['automation_policy'] = 'Ưu tiên kết quả cũ cần đánh giá lại, sau đó kiểm soát chưa chạy/lỗi. Không tự duyệt; chờ bổ sung bằng chứng không tự chạy lặp.'
    report.pop('sha256', None)
    report['sha256'] = hashlib.sha256(json.dumps(report, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()
    return report


def start(assessment_id, user_id, control_id=None, force=False):
    # All shared starts serialize selection + claim across API processes.
    # Existing claim_job also atomically protects against legacy/manual runs.
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', ('shared-work:' + assessment_id,))
            report = board(assessment_id)
            cid = control_id or report['next_control_id']
            if cid is None:
                return {'action': 'nothing_pending', 'message': 'Không có kiểm soát tự động cần chạy. Xem hồ sơ chờ bằng chứng/duyệt.'}
            c = next((c for c in report['controls'] if c['control_id'] == cid), None)
            if not c or not c['collector_supported']:
                raise ValueError('Kiểm soát chưa có collector tự động.')
            if c['shared_state'] == 'running':
                return {'action': 'following', 'control_id': cid, 'job_id': c['active_job_id'], 'assigned_to': c['assigned_to']}
            if not force and c['shared_state'] in ('evaluated', 'awaiting_review', 'waiting_evidence'):
                return {'action': 'reused', 'control_id': cid, 'evaluation_id': c['latest_evaluation_id'], 'conclusion': c['conclusion']}
            try:
                job = teamwork.claim_job(assessment_id, cid, user_id)
            except ValueError:
                current = next((x for x in teamwork.progress_board(assessment_id) if x['control_id'] == cid), {})
                if current.get('active_job_id'):
                    return {'action': 'following', 'control_id': cid, 'job_id': current['active_job_id'], 'assigned_to': current.get('assigned_to')}
                raise
            return {**job, 'control_id': cid, 'action': 'started'}
