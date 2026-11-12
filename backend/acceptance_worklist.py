"""Actionable evidence/review gaps, not a compliance percentage."""
from collections import Counter


def build_worklist(scope):
    tasks=[]
    def add(stage,owner,message,control=None):
        tasks.append(dict(stage=stage,owner_role=owner,control_id=control['control_id'] if control else None,
                          priority_a8=control.get('priority_a8',False) if control else False,message=message))
    if not scope['rubric_approval']:
        add('rubric','Người phụ trách','Rà tiêu chí, ngưỡng và nguồn được chấp nhận; ghi xác nhận rubric đúng phiên bản.')
    for row in scope['controls']:
        decision=row['applicability']
        if decision is None:add('applicability','Người phụ trách','Xác định tính áp dụng và kế hoạch xử lý có căn cứ.',row)
        if decision and not decision['applicable']:continue
        if decision and any(not decision.get(key) for key in ('treatment_owner','treatment_due','verification_plan')):
            add('treatment','Người phụ trách','Bổ sung người chịu trách nhiệm, hạn xử lý và cách kiểm tra lại; kế hoạch đã ghi không tự chứng minh công việc hoàn tất.',row)
        if not row['explicit_source_count']:add('sources','Chủ sở hữu hồ sơ','Thu nguồn gốc/hồ sơ hoặc nhập bản capture live; preset tự sinh và mẫu trống chưa thay thế nguồn để thẩm định.',row)
        elif row['assessment_state']!='evaluated':add('evaluation','Điều phối Agent','Đánh giá hoặc tái đánh giá nguồn hiện hành; không thay bằng kết quả ca thử.',row)
        if not row['human_review_current']:add('review','Người đánh giá','Thẩm định từng tiêu chí, căn cứ và viện dẫn; giữ chưa rõ khi thiếu nguồn.',row)
    if not scope['soa']['approval_ready']:add('approval','Người phụ trách','Hoàn tất các điều kiện quyết định/thẩm định/rubric trước khi trình duyệt SoA.')
    elif scope['soa']['approval']!='HUMAN_APPROVED_PROJECT_SCOPE':add('approval','Người phụ trách','Rà fingerprint, lý do áp dụng và kế hoạch; quyết định duyệt SoA trong phạm vi.')
    order={'rubric':0,'applicability':1,'sources':2,'evaluation':3,'review':4,'treatment':5,'approval':6}
    tasks.sort(key=lambda t:(order[t['stage']],not t['priority_a8'],t['control_id'] or ''))
    return dict(tasks=tasks,by_stage=dict(Counter(t['stage'] for t in tasks)),
        scope_total=scope['scope_total'],soa_approved=scope['acceptance']['soa_approved'],
        rubric_sha256=scope['rubric_sha256'],soa_fingerprint=scope['soa']['fingerprint'],
        note='Danh sách việc còn thiếu, không phải tỷ lệ tuân thủ. Có nguồn không đồng nghĩa nguồn đúng. SoA được duyệt không đồng nghĩa mọi control đạt.')
