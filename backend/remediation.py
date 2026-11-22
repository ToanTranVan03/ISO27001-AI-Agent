"""Evidence-bound corrective action lifecycle; never a certification decision."""
from copy import deepcopy
from datetime import date,datetime,timezone
from uuid import uuid4
from zoneinfo import ZoneInfo
import hashlib
import json


def now():return datetime.now(timezone.utc).isoformat()


def review_signature(control):
    return hashlib.sha256(json.dumps(control.get('human_review'),sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def finding(control,description,location,cause,risk):
    if control['applicability'] and control['applicability'].get('applicable') is False:
        raise ValueError('Control đã có quyết định loại trừ; rà quyết định trước khi mở khắc phục.')
    return dict(finding_id=str(uuid4()),control_id=control['control_id'],description=description,
        location=location,root_cause=cause,risk=risk,root_cause_confirmed=False,
        baseline=dict(review_token=control['review_token'],conclusion=control['conclusion'],
            human_review=deepcopy(control['human_review']) if control['human_review_current'] else None,
            evidence=[{k:e.get(k) for k in ('evidence_id','sha256_hash','source','evidence_type')} for e in control['evidence']],
            criteria=deepcopy(control['pass_criteria'])),
        created_at=now(),actions=[],history=[],certification_claim=False)


def action(proposal,origin):
    value=deepcopy(proposal)
    value.update(action_id=str(uuid4()),state='PENDING_APPROVAL',proposal_origin=origin,
        assignee=None,due_date=None,tasks=[dict(task_id=str(uuid4()),title=t,done=False) for t in proposal.get('tasks',[])],
        evidence=[],verifications=[])
    return value


def transition(document,action_id,command,payload,actor,role,control):
    doc=deepcopy(document)
    item=next((a for a in doc['actions'] if a['action_id']==action_id),None)
    if item is None:raise ValueError('Không tìm thấy hành động.')
    before=item['state']
    consultant=role in ('consultant','verifier')
    operator=str(item.get('assignee'))==str(actor) or str(actor) in item.get('collaborator_ids',[])
    if command=='approve':
        if role!='consultant' or before!='PENDING_APPROVAL':raise PermissionError('Chỉ tư vấn phê duyệt đề xuất đang chờ.')
        if doc['baseline']['review_token']!=control['review_token']:raise ValueError('Nguồn/kết quả đã đổi; mở phát hiện mới trên snapshot hiện hành.')
        if not payload.get('assignee') or not payload.get('due_date'):raise ValueError('Cần người thực hiện và hạn.')
        due=date.fromisoformat(payload['due_date'])
        if due<datetime.now(ZoneInfo('Asia/Bangkok')).date():raise ValueError('Hạn giao mới không được ở quá khứ.')
        if not item['tasks']:raise ValueError('Cần ít nhất một công việc.')
        item.update(state='NOT_STARTED',assignee=payload['assignee'],collaborator_ids=payload.get('collaborator_ids',[]),due_date=due.isoformat(),approved_by=actor)
    elif command=='edit':
        if role!='consultant' or before!='PENDING_APPROVAL':raise PermissionError('Chỉ sửa đề xuất chưa phê duyệt.')
        for key in ('title','steps','acceptance','resources','department','priority'):
            if key in payload:item[key]=payload[key]
        if 'tasks' in payload:item['tasks']=[dict(task_id=str(uuid4()),title=t,done=False) for t in payload['tasks']]
    elif command in ('start','task','attach','submit'):
        if not operator:raise PermissionError('Chỉ người được giao thực hiện công việc.')
        if before not in ('NOT_STARTED','IN_PROGRESS','NEEDS_INFORMATION','REWORK'):raise ValueError('Trạng thái không cho cập nhật thực hiện.')
        if command=='start':item['state']='IN_PROGRESS'
        if command=='task':
            task=next((t for t in item['tasks'] if t['task_id']==payload.get('task_id')),None)
            if not task or type(payload.get('done')) is not bool:raise ValueError('Công việc/trạng thái không hợp lệ.')
            index=item['tasks'].index(task)
            if payload['done'] and any(not t['done'] for t in item['tasks'][:index]):raise ValueError('Hoàn tất các bước trước theo thứ tự phụ thuộc.')
            if not payload['done'] and any(t['done'] for t in item['tasks'][index+1:]):raise ValueError('Bỏ hoàn tất các bước phụ thuộc phía sau trước.')
            task['done']=payload['done'];item['state']='IN_PROGRESS'
        if command=='attach':
            evidence=next((e for e in control['evidence'] if e['evidence_id']==payload.get('evidence_id')),None)
            if not evidence or evidence.get('source_quality',{}).get('usable') is False:raise ValueError('Nguồn không thuộc control hoặc không dùng được.')
            if not (evidence.get('is_synthetic') is False or (evidence.get('source') or '').startswith('a8-capture://')):
                raise ValueError('Snapshot/preset tự sinh không thay bằng chứng thực hiện; cần nguồn nộp hoặc bản thu lab rõ xuất xứ.')
            baseline={e['evidence_id'] for e in doc['baseline']['evidence']}
            if evidence['evidence_id'] in baseline:raise ValueError('Nguồn này đã có trước khắc phục; cần nguồn sau thực hiện.')
            ref=dict(evidence_id=evidence['evidence_id'],sha256_hash=evidence['sha256_hash'])
            if ref not in item['evidence']:item['evidence'].append(ref)
        if command=='submit':
            if str(item.get('assignee'))!=str(actor):raise PermissionError('Người chịu trách nhiệm chính gửi hồ sơ xác minh.')
            if not all(t['done'] for t in item['tasks']) or not item['evidence']:raise ValueError('Hoàn tất công việc và đính kèm nguồn sau thực hiện trước khi gửi.')
            item.update(state='AWAITING_VERIFICATION',submitted_token=control['review_token'])
    elif command=='verify':
        if not consultant or operator:raise PermissionError('Người thực hiện không được tự xác minh; cần tư vấn/người xác minh.')
        if before!='AWAITING_VERIFICATION':raise ValueError('Chưa gửi xác minh.')
        if control['review_token']!=item['submitted_token']:raise ValueError('Nguồn/kết quả đã đổi sau khi gửi; cần yêu cầu bổ sung và gửi lại.')
        outcome=payload.get('outcome')
        if outcome not in ('accepted','rework','partial','more_information'):raise ValueError('Kết quả xác minh không hợp lệ.')
        current={e['evidence_id']:e for e in control['evidence']}
        for ref in item['evidence']:
            e=current.get(ref['evidence_id'])
            if not e or e['sha256_hash']!=ref['sha256_hash'] or e.get('source_quality',{}).get('usable') is False:
                raise ValueError('Bằng chứng sau khắc phục thiếu, đổi hoặc không dùng được.')
        if outcome=='accepted':
            review=control['human_review']
            if not control['human_review_current'] or review['conclusion']!='Compliant':raise ValueError('Cần thẩm định từng tiêu chí hiện hành kết luận tuân thủ trước khi xác minh đạt.')
            if str(review.get('reviewed_by'))!=str(actor):raise ValueError('Người xác minh phải tự thẩm định hiện hành, không dùng xác nhận của người thực hiện.')
            cited=set(review['evidence_ids'])
            if not cited.intersection(e['evidence_id'] for e in item['evidence']):raise ValueError('Thẩm định phải viện dẫn nguồn sau khắc phục.')
        item['state']={'accepted':'VERIFIED','rework':'REWORK','partial':'REWORK','more_information':'NEEDS_INFORMATION'}[outcome]
        item['verifications'].append(dict(outcome=outcome,reviewer_id=actor,note=payload['note'],at=now(),
            human_review_signature=review_signature(control),
            human_reviewed_at=control['human_review'].get('reviewed_at') if control['human_review_current'] else None,
            review_token=control['review_token'],conclusion=control['human_review']['conclusion'] if control['human_review_current'] else None))
    elif command=='return':
        if not consultant or operator or before!='AWAITING_VERIFICATION':raise PermissionError('Chỉ người xác minh trả hồ sơ đang chờ.')
        item['state']='NEEDS_INFORMATION'
    elif command=='close':
        if not consultant or operator or before!='VERIFIED':raise PermissionError('Chỉ đóng hành động đã xác minh đạt.')
        if (not control['human_review_current'] or control['review_token']!=item['verifications'][-1]['review_token'] or
            control['human_review']['conclusion']!='Compliant' or review_signature(control)!=item['verifications'][-1]['human_review_signature']):
            raise ValueError('Thẩm định đã cũ, không đóng hành động trên nguồn khác.')
        item['state']='CLOSED'
    else:raise ValueError('Lệnh không được hỗ trợ.')
    doc['history'].append(dict(actor=actor,role=role,command=command,action_id=action_id,
        before=before,after=item['state'],at=now(),note=payload.get('note','')))
    return doc
