"""Project SoA submission gates, separate from a compliance score or certification."""
from collections import Counter
from datetime import date,datetime
from zoneinfo import ZoneInfo

PROTOCOL='scope56-approval-v2-followup'
LABELS={
 'applicability_missing':'Chưa ghi quyết định tính áp dụng',
 'applicability_reason_missing':'Thiếu căn cứ áp dụng / loại trừ',
 'running':'Agent đang xử lý nguồn',
 'review_missing':'Chưa có thẩm định từng tiêu chí hiện hành',
 'treatment_missing':'Thiếu kế hoạch xử lý / duy trì',
 'owner_missing':'Chưa ghi người chịu trách nhiệm',
 'due_missing':'Chưa ghi hạn / kỳ kiểm tra lại',
 'due_invalid':'Hạn xử lý không hợp lệ',
 'verification_missing':'Thiếu cách thu lại nguồn và kiểm tra kết quả',
}


def build_readiness(controls,rubric_approved,as_of=None):
    today=as_of or datetime.now(ZoneInfo('Asia/Bangkok')).date()
    rows=[]
    for c in controls:
        d=c.get('applicability');blockers=[];due=None
        if c.get('workflow_status')=='RUNNING':blockers.append('running')
        if d is None:blockers.append('applicability_missing')
        else:
            if len((d.get('reason') or '').strip())<10:blockers.append('applicability_reason_missing')
            if d.get('applicable'):
                if not c.get('human_review_current'):blockers.append('review_missing')
                if len((d.get('treatment') or '').strip())<10:blockers.append('treatment_missing')
                if not (d.get('treatment_owner') or '').strip():blockers.append('owner_missing')
                if len((d.get('verification_plan') or '').strip())<10:blockers.append('verification_missing')
                value=d.get('treatment_due')
                if not value:blockers.append('due_missing')
                else:
                    try:due=date.fromisoformat(value)
                    except (TypeError,ValueError):blockers.append('due_invalid')
        rows.append(dict(control_id=c['control_id'],name=c['name'],applicable=d.get('applicable') if d else None,
            blockers=blockers,blocker_labels=[LABELS[b] for b in blockers],ready=not blockers,
            owner=d.get('treatment_owner') if d else None,due_date=due.isoformat() if due else None,
            due_state='past_due_date' if due and due<today else 'due_today' if due==today else 'scheduled' if due else 'not_recorded'))
    pending=[r['control_id'] for r in rows if not r['ready']]
    return dict(protocol=PROTOCOL,as_of=today.isoformat(),timezone='Asia/Bangkok',controls=rows,
        total_controls=len(rows),ready_controls=len(rows)-len(pending),pending_controls=pending,
        by_blocker=dict(Counter(b for r in rows for b in r['blockers'])),
        past_due_controls=[r['control_id'] for r in rows if r['due_state']=='past_due_date'],
        global_blockers=[] if rubric_approved else ['rubric_not_approved'],
        approval_ready=not pending and bool(rubric_approved),
        note='Điều kiện trình duyệt SoA của đồ án, không phải tỷ lệ đạt ISO. Hạn kế hoạch đã qua là cảnh báo cần rà; không tự kết luận chưa hoàn thành, không tự gia hạn hoặc duyệt.')
