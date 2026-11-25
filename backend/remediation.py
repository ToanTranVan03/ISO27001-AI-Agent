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


def dashboard(records,controls,today):
    """Observed workflow counts only; zero denominators stay unknown."""
    from collections import Counter
    from datetime import timedelta
    findings=[r for r in records if r['kind']=='finding']
    actions=[a for r in findings for a in r['document']['actions']]
    done=sum(a['state'] in ('VERIFIED','CLOSED') for a in actions)
    active=[a for a in actions if a['state'] not in ('VERIFIED','CLOSED')]
    limit=(date.fromisoformat(today)+timedelta(days=3)).isoformat()
    states=dict(Counter(a['state'] for a in actions))
    task_labels={
        'missing_sources':'Bổ sung nguồn bằng chứng gốc',
        'unusable_sources':'Thay thế nguồn không đủ chất lượng',
        'needs_assessment_check':'Chạy Agent đánh giá nguồn hiện hành',
        'needs_review':'Chuyên viên thẩm định từng tiêu chí',
        'needs_applicability':'Ghi quyết định tính áp dụng (SoA)',
        'has_finding':'Rà phát hiện và lập/duyệt kế hoạch khắc phục',
        'remediating':'Thực hiện công việc và đính kèm bằng chứng sau',
        'awaiting_verification':'Chuyên viên xác minh độc lập và đánh giá lại',
        'has_verified_action':'Kiểm tra hiệu lực xác minh trước khi chốt hồ sơ',
    }
    work=[]
    for c in controls:
        fs=[r for r in findings if r['document']['control_id']==c['control_id']]
        related=[a for r in fs for a in r['document']['actions']]
        sources=[e for e in c.get('evidence',[]) if e.get('is_synthetic') is False or (e.get('source') or '').startswith('a8-capture://')]
        usable=[e for e in sources if e.get('source_quality',{}).get('usable') is not False]
        flags=[]
        if not sources:flags.append('missing_sources')
        elif not usable:flags.append('unusable_sources')
        if not c.get('latest_evaluation_id') or c.get('assessment_state') in ('failed','stale','not_evaluated'):flags.append('needs_assessment_check')
        if not c.get('human_review_current'):flags.append('needs_review')
        if not c.get('applicability'):flags.append('needs_applicability')
        if fs:flags.append('has_finding')
        if any(a['state'] in ('IN_PROGRESS','REWORK','NEEDS_INFORMATION','NOT_STARTED') for a in related):flags.append('remediating')
        if any(a['state']=='AWAITING_VERIFICATION' for a in related):flags.append('awaiting_verification')
        if any(a['state'] in ('VERIFIED','CLOSED') for a in related):flags.append('has_verified_action')
        required_tasks=[task_labels[f] for f in flags if f in task_labels]
        effective=c['human_review']['conclusion'] if c.get('human_review_current') and c.get('human_review') else c.get('conclusion')
        work.append(dict(control_id=c['control_id'],name=c.get('name',''),conclusion=effective,machine_conclusion=c.get('conclusion'),flags=flags,required_tasks=required_tasks,findings=len(fs),actions=len(related),usable_sources=len(usable)))
    planned_resources=[dict(action_id=a.get('action_id'),title=a.get('title'),resources=a.get('resources'),estimated_effort=a.get('estimated_effort'))
        for a in actions if a.get('resources') or a.get('estimated_effort')]
    remaining_issues=[dict(control_id=r['document']['control_id'],finding_id=r['record_id'],description=r['document']['description'],risk=r['document'].get('risk','unconfirmed'))
        for r in findings if not r['document']['actions'] or any(a['state'] not in ('VERIFIED','CLOSED') for a in r['document']['actions'])]
    return dict(findings=len(findings),actions=len(actions),by_state=states,
        overdue=sum(bool(a.get('due_date')) and a['due_date']<today for a in active),
        due_soon=sum(bool(a.get('due_date')) and today<=a['due_date']<=limit for a in active),
        completed=done,completion_percent=round(100*done/len(actions),2) if actions else None,
        risk_proposals=dict(Counter(r['document'].get('risk','unconfirmed') for r in findings)),
        urgent=[dict(control_id=r['document']['control_id'],finding_id=r['record_id'],description=r['document']['description']) for r in findings if r['document'].get('risk')=='high'],
        conclusions=dict(Counter((c['human_review']['conclusion'] if c.get('human_review_current') and c.get('human_review') else c.get('conclusion')) or 'Insufficient Evidence' for c in controls)),
        decisions_pending=sum(not c.get('applicability') for c in controls),estimated_cost=None,
        planned_resources=planned_resources,remaining_issues=remaining_issues,
        worklist=work,scope_note='Số công việc theo quyền hiện tại; tỷ lệ hoàn thành không phải tỷ lệ tuân thủ. Chi phí chưa có dữ liệu.')


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
        for key in ('title','steps','acceptance','resources','department','priority','problem','possible_causes','clarification_questions','objective','rationale','target_location','estimated_effort','required_evidence','recheck_method'):
            if key in payload:item[key]=payload[key]
        if 'tasks' in payload:item['tasks']=[dict(task_id=str(uuid4()),title=t,done=False) for t in payload['tasks']]
    elif command=='assign_task':
        if role!='consultant' or before not in ('NOT_STARTED','IN_PROGRESS','REWORK','NEEDS_INFORMATION'):raise PermissionError('Chỉ tư vấn phân công bước khi đang thực hiện.')
        target=payload.get('task_assignee')
        if target not in [item.get('assignee'),*item.get('collaborator_ids',[])]:raise ValueError('Người nhận bước phải là người chính hoặc người phối hợp đã giao.')
        task=next((t for t in item['tasks'] if t['task_id']==payload.get('task_id')),None)
        if not task or task['done']:raise ValueError('Chỉ phân công công việc con chưa hoàn tất.')
        task['assignee']=target
    elif command in ('start','task','attach','submit'):
        if not operator:raise PermissionError('Chỉ người được giao thực hiện công việc.')
        if before not in ('NOT_STARTED','IN_PROGRESS','NEEDS_INFORMATION','REWORK'):raise ValueError('Trạng thái không cho cập nhật thực hiện.')
        if command=='start':item['state']='IN_PROGRESS'
        if command=='task':
            task=next((t for t in item['tasks'] if t['task_id']==payload.get('task_id')),None)
            if not task or type(payload.get('done')) is not bool:raise ValueError('Công việc/trạng thái không hợp lệ.')
            if task.get('assignee') and str(task['assignee'])!=str(actor) and str(item['assignee'])!=str(actor):raise PermissionError('Bước đã giao cho thành viên khác; người chính có thể điều phối.')
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
