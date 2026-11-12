"""Authorized lab APIs, separate from the existing assessment/workflow API."""
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from backend.team_api import require_user, require_campaign
from backend import enterprise_lab, teamwork
from backend.enterprise_spec import CONTROL_TO_NODE, PRESETS

router = APIRouter(prefix='/api/assessments/{assessment_id}/enterprise', tags=['Enterprise Lab'])


class ScenarioInput(BaseModel):
    scenario: str = Field(pattern='^(healthy|partial|gap)$')


class CompanyEvent(BaseModel):
    employee_id: str = Field(pattern=r'^(EMP|HF)-\d{3}$')
    action: str = Field(min_length=1, max_length=80)


@router.get('/company')
def company_inventory(assessment_id: UUID, user: dict = Depends(require_user)):
    from backend.company import snapshot
    require_campaign(assessment_id, user)
    return snapshot(str(assessment_id))


@router.post('/company/events')
def company_event(assessment_id: UUID, req: CompanyEvent, user: dict = Depends(require_user)):
    from backend.company import change
    require_campaign(assessment_id, user)
    if req.action == 'retention_approve' and user['role'] != 'admin':
        raise HTTPException(403,detail='Chỉ admin ghi nhận phê duyệt ngoại lệ.')
    try:
        return change(str(assessment_id), req.employee_id, req.action, actor_id=user['user_id'])
    except ValueError as exc:
        raise HTTPException(409, detail=str(exc)) from exc


@router.get('/overview')
def overview(assessment_id: UUID, user: dict = Depends(require_user)):
    from backend.company_evidence import PEOPLE_CONTROLS
    require_campaign(assessment_id,user)
    nodes=enterprise_lab.get_lab_nodes(str(assessment_id))
    board=teamwork.progress_board(str(assessment_id))
    from backend.company_evidence import fresh_progress
    board=fresh_progress(str(assessment_id),board)
    controls={c['control_id']: c for c in board}
    for node in nodes:
        node['progress']=[{
            'control_id':cid,
            'workflow_status':controls[cid]['workflow_status'],
            'compliance_status':controls[cid]['compliance_status'],
            'assigned_to':controls[cid]['assigned_to'],
        } for cid in node['controls'] if cid in controls]
    return {'name':'ISO Enterprise Lab — Công ty giả lập',
            'assessment_id':str(assessment_id), 'is_synthetic':True,
            'node_count':len(nodes),'supported_controls':sorted(set(CONTROL_TO_NODE) | PEOPLE_CONTROLS),
            'nodes':nodes}


@router.post('/nodes/{node_key}/scenario')
def scenario(assessment_id: UUID,node_key: str, req: ScenarioInput,
             user: dict = Depends(require_user)):
    require_campaign(assessment_id,user)
    if user['role'] != 'admin':
        raise HTTPException(403,detail='Chỉ quản trị viên thay đổi tình huống lab.')
    try:
        return enterprise_lab.change_scenario(str(assessment_id),node_key,
                                              req.scenario,user['user_id'])
    except ValueError as exc:
        raise HTTPException(404,detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(409,detail=str(exc)) from exc


@router.get('/controls/{control_id}/evidence')
def evidence(assessment_id: UUID, control_id: str,user: dict=Depends(require_user)):
    from backend.company_evidence import PEOPLE_CONTROLS
    require_campaign(assessment_id,user)
    if control_id not in set(CONTROL_TO_NODE) | PEOPLE_CONTROLS:
        raise HTTPException(404,detail='Control này chưa có lab collector.')
    return enterprise_lab.list_lab_evidence(str(assessment_id),control_id)


@router.get('/compliance-report')
def compliance_report(assessment_id: UUID, user: dict = Depends(require_user)):
    from backend.compliance_report import build_dossier, campaign_evidence
    require_campaign(assessment_id, user)
    board = teamwork.progress_board(str(assessment_id))
    evidence = campaign_evidence(str(assessment_id))
    history = {item['control_id']: teamwork.list_history(str(assessment_id), item['control_id']) for item in board if item.get('latest_evaluation_id')}
    from backend.company import snapshot
    return build_dossier(assessment_id, board, evidence, history, snapshot(str(assessment_id)))


class SharedWorkInput(BaseModel):
    control_id: str | None = None
    force: bool = False


@router.get('/shared-work')
def shared_work_board(assessment_id: UUID, user: dict = Depends(require_user)):
    from backend.shared_work import board
    require_campaign(assessment_id, user)
    return board(str(assessment_id))


@router.post('/shared-work/start')
def shared_work_start(assessment_id: UUID, req: SharedWorkInput, user: dict = Depends(require_user)):
    from backend.shared_work import start
    from backend.team_api import executor, execute_agent_job
    require_campaign(assessment_id, user)
    try:
        result = start(str(assessment_id), user['user_id'], req.control_id, req.force)
    except ValueError as exc:
        raise HTTPException(409, detail=str(exc)) from exc
    if result['action'] == 'started':
        try:
            executor.submit(execute_agent_job, result['job_id'], str(assessment_id), result['control_id'])
        except RuntimeError as exc:
            teamwork.finish_job(result['job_id'], None, 'Không thể khởi tạo worker.')
            raise HTTPException(503, detail='Worker không khả dụng.') from exc
    return result


@router.get('/scope56/teacher-report')
def teacher_report(assessment_id: UUID,user: dict=Depends(require_user)):
    require_campaign(assessment_id,user)
    if user.get('role')!='admin':raise HTTPException(403,'Chỉ admin xuất báo cáo điều phối; người chấm dùng gói mù.')
    import json
    from backend import a8_api
    from backend.teacher_report import build_report
    with a8_api.lock:
        runs=[json.loads(p.read_text(encoding='utf-8')) for p in a8_api.folder(assessment_id).glob('*.json')]
        return build_report(scope56(assessment_id,user),runs,a8_api.practice_summary(assessment_id,user))


@router.get('/scope56')
def scope56(assessment_id: UUID,user: dict=Depends(require_user)):
    from backend.shared_work import dossier
    from backend.scope56 import build_scope
    from backend import a8_api
    import json
    require_campaign(assessment_id,user)
    studies={}
    for path in a8_api.folder(assessment_id).glob('*.json'):
        doc=json.loads(path.read_text(encoding='utf-8'))
        if not doc.get('report'):continue
        mine={r['control_id'] for r in doc['reviews'] if str(r.get('reviewer_id'))==str(user['user_id'])}
        if str(doc['created_by'])!=str(user['user_id']) and len(mine)<len(doc['report']['records']):continue
        for record in doc['report']['records']:
            studies.setdefault(record['control_id'],[]).append(dict(run_id=doc['run_id'],created_at=doc['created_at'],
                status=record['status'],error=record['error'],mode=doc['mode'],profile=doc['profile'],
                source='A8_EXPERIMENT_ONLY',evidence_id=record['evidence']['evidence_id'],
                evidence_sha256=record['evidence']['source_sha256']))
    for records in studies.values():records.sort(key=lambda r:r['created_at'],reverse=True)
    path=a8_api.folder(assessment_id)/'settings'/'scope56-decisions.json'
    history=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    def settings(name):
        file=a8_api.folder(assessment_id)/'settings'/name
        return json.loads(file.read_text(encoding='utf-8')) if file.exists() else []
    reviews=settings('scope56-reviews.json');approvals=settings('scope56-approvals.json')
    return build_scope(str(assessment_id),dossier(str(assessment_id)),studies,{r['control_id']:r for r in history},
                       {r['control_id']:r for r in reviews},approvals,settings('scope56-rubric-approvals.json'))


class ScopeDecision(BaseModel):
    model_config=ConfigDict(str_strip_whitespace=True,extra="forbid")
    control_id: str
    applicable: bool
    reason: str=Field(min_length=10,max_length=2000)
    treatment: str=Field(min_length=10,max_length=2000)
    treatment_owner: str | None=Field(default=None,min_length=2,max_length=200)
    treatment_due: date | None=None
    verification_plan: str | None=Field(default=None,min_length=10,max_length=2000)


@router.post('/scope56/decisions')
def scope_decision(assessment_id: UUID,req: ScopeDecision,user: dict=Depends(require_user)):
    import json
    from datetime import datetime,timezone
    from backend.scope56 import CATALOG
    from backend import a8_api
    require_campaign(assessment_id,user)
    if user.get('role')!='admin':raise HTTPException(403,'Chỉ người phụ trách admin ghi quyết định tính áp dụng.')
    if req.control_id not in {c['control_id'] for c in json.loads(CATALOG.read_text(encoding='utf-8'))}:raise HTTPException(404,'Ngoài phạm vi 56 control.')
    with a8_api.lock:
        path=a8_api.folder(assessment_id)/'settings'/'scope56-decisions.json'
        history=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
        record={**req.model_dump(mode='json'),'recorded_by':user['user_id'],'recorded_at':datetime.now(timezone.utc).isoformat()}
        history.append(record);a8_api.save(path,history)
    return record


@router.post('/scope56/packages/prepare')
def prepare_packages(assessment_id: UUID,user: dict=Depends(require_user)):
    from evidence_collectors.control_packages import prepare
    require_campaign(assessment_id,user)
    if user.get('role')!='admin':raise HTTPException(403,'Chỉ admin chuẩn bị thư mục nguồn bằng chứng.')
    try:return prepare(str(assessment_id))
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc


class CollectPackage(BaseModel):
    control_id: str | None = None


@router.post('/scope56/packages/collect')
def collect_packages(assessment_id: UUID,req: CollectPackage,user: dict=Depends(require_user)):
    from evidence_collectors.control_packages import collect,controls
    require_campaign(assessment_id,user)
    ids=[req.control_id] if req.control_id else [c['control_id'] for c in controls()]
    result=[]
    for cid in ids:
        try:result.append(collect(str(assessment_id),cid,user['user_id']))
        except (ValueError,OSError) as exc:result.append({'control_id':cid,'issues':[str(exc)[:200]],'inserted':[],'reused':[]})
    return {'results':result,'inserted_count':sum(len(r['inserted']) for r in result),
            'note':'Nguồn do người phụ trách cung cấp; chưa xác thực nội dung chỉ từ việc thu nhận/hash.'}


class CriterionReview(BaseModel):
    model_config=ConfigDict(str_strip_whitespace=True,extra='forbid')
    criterion_index: int=Field(ge=0)
    verdict: str=Field(pattern='^(met|not_met|unknown)$')
    rationale: str=Field(min_length=10,max_length=1500)
    evidence_ids: list[str]=Field(max_length=100)


class ScopeReview(BaseModel):
    model_config=ConfigDict(str_strip_whitespace=True,extra='forbid')
    control_id: str
    review_token: str=Field(min_length=64,max_length=64)
    conclusion: str=Field(pattern='^(Compliant|Partially Compliant|Non-Compliant|Insufficient Evidence)$')
    rationale: str=Field(min_length=20,max_length=3000)
    evidence_ids: list[str]=Field(max_length=100)
    criteria_reviews: list[CriterionReview]=Field(min_length=1,max_length=100)


@router.post('/scope56/reviews')
def scope_review(assessment_id: UUID,req: ScopeReview,user: dict=Depends(require_user)):
    from backend import a8_api
    from datetime import datetime,timezone
    import json
    require_campaign(assessment_id,user)
    with a8_api.lock:
        report=scope56(assessment_id,user)
        row=next((c for c in report['controls'] if c['control_id']==req.control_id),None)
        if not row:raise HTTPException(404,'Ngoài phạm vi 56 control.')
        if row['workflow_status']=='RUNNING' or req.review_token!=row['review_token']:raise HTTPException(409,'Dữ liệu/đánh giá đã thay đổi; tải lại trước khi xác nhận.')
        available={e['evidence_id'] for e in row['evidence']}
        if not set(req.evidence_ids)<=available:raise HTTPException(422,'Viện dẫn bằng chứng không thuộc control/đợt.')
        if req.conclusion in ('Compliant','Partially Compliant') and not req.evidence_ids:raise HTTPException(422,'Cần viện dẫn bằng chứng để xác nhận kết luận đạt/một phần.')
        from backend.review_criteria import validate,PROTOCOL
        try:validate(row['pass_criteria'],[c.model_dump() for c in req.criteria_reviews],req.evidence_ids,req.conclusion)
        except ValueError as exc:raise HTTPException(422,str(exc)) from exc
        path=a8_api.folder(assessment_id)/'settings'/'scope56-reviews.json'
        history=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
        record={**req.model_dump(),'reviewed_by':user['user_id'],'reviewed_at':datetime.now(timezone.utc).isoformat(),
                'protocol':PROTOCOL,'machine_conclusion':row['conclusion']}
        history.append(record);a8_api.save(path,history)
    return record


class ScopeApproval(BaseModel):
    model_config=ConfigDict(str_strip_whitespace=True,extra='forbid')
    fingerprint: str=Field(min_length=64,max_length=64)
    note: str=Field(min_length=30,max_length=3000)


@router.post('/scope56/approval')
def approve_scope56(assessment_id: UUID,req: ScopeApproval,user: dict=Depends(require_user)):
    from backend import a8_api
    from datetime import datetime,timezone
    import json
    require_campaign(assessment_id,user)
    if user.get('role')!='admin':raise HTTPException(403,'Chỉ người phụ trách admin phê duyệt SoA.')
    with a8_api.lock:
        report=scope56(assessment_id,user);soa=report['soa']
        if req.fingerprint!=soa['fingerprint'] or not soa['approval_ready']:raise HTTPException(409,detail={'message':'Chưa đủ quyết định/thẩm định hiện hành hoặc nguồn đã đổi.','pending_controls':soa['pending_controls']})
        path=a8_api.folder(assessment_id)/'settings'/'scope56-approvals.json'
        history=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
        record={**req.model_dump(),'approved_by':user['user_id'],'approved_at':datetime.now(timezone.utc).isoformat(),
                'scope_total':56,'meaning':'Chấp thuận SoA trong phạm vi đồ án, không phải chứng nhận ISO.'}
        history.append(record);a8_api.save(path,history)
    return record


@router.get('/scope56/controls/{control_id}/sources')
def scope_sources(assessment_id: UUID,control_id: str,user: dict=Depends(require_user)):
    from backend import database
    require_campaign(assessment_id,user)
    control=database.get_control(control_id)
    if not control:raise HTTPException(404,'Không tìm thấy control.')
    evidence,_=database.collect_evidence(control_id,str(assessment_id))
    return {'control_id':control_id,'evidence':evidence,'note':'Nội dung đã trích xuất; cần đối chiếu tài liệu gốc và nguồn xác nhận. Không xác thực chỉ từ hash.'}


class RubricScopeApproval(BaseModel):
    model_config=ConfigDict(str_strip_whitespace=True,extra='forbid')
    rubric_sha256: str=Field(min_length=64,max_length=64)
    note: str=Field(min_length=30,max_length=3000)


@router.post('/scope56/rubric/approval')
def approve_scope_rubric(assessment_id: UUID,req: RubricScopeApproval,user: dict=Depends(require_user)):
    from backend import a8_api
    from datetime import datetime,timezone
    import json
    require_campaign(assessment_id,user)
    if user.get('role')!='admin':raise HTTPException(403,'Chỉ người phụ trách admin xác nhận tiêu chí 56 control.')
    with a8_api.lock:
        report=scope56(assessment_id,user)
        if req.rubric_sha256!=report['rubric_sha256']:raise HTTPException(409,'Tiêu chí đã thay đổi; tải lại và rà soát.')
        path=a8_api.folder(assessment_id)/'settings'/'scope56-rubric-approvals.json'
        history=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
        record={**req.model_dump(),'approved_by':user['user_id'],'approved_at':datetime.now(timezone.utc).isoformat()}
        history.append(record);a8_api.save(path,history)
    return record
