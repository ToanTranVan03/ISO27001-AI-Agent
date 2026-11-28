"""Authorized lab APIs, separate from the existing assessment/workflow API."""
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, StrictBool
from backend.team_api import require_user, require_campaign
from backend import enterprise_lab, teamwork
from backend.enterprise_spec import CONTROL_TO_NODE, PRESETS

router = APIRouter(prefix='/api/assessments/{assessment_id}/enterprise', tags=['Enterprise Lab'])


class AssessmentRequestInput(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    title:str=Field(min_length=5,max_length=200)
    objective:str=Field(min_length=10,max_length=2000)
    control_ids:list[str]=Field(min_length=1,max_length=56)
    note:str=Field(min_length=10,max_length=2000)


@router.get('/assessment-requests')
def assessment_requests(assessment_id:UUID,user:dict=Depends(require_user)):
    from backend.remediation_api import membership
    from backend.database import get_connection
    role=membership(assessment_id,user)
    with get_connection() as con,con.cursor() as cur:
        cur.execute('''SELECT request_id,created_by,version,document,created_at FROM enterprise_assessment_requests
            WHERE assessment_id=%s AND (%s OR created_by=%s) ORDER BY created_at DESC''',
            (assessment_id,role!='operator',user['user_id']))
        rows=[dict(request_id=str(r[0]),created_by=str(r[1]),version=r[2],document=r[3],created_at=r[4].isoformat()) for r in cur.fetchall()]
    return dict(requests=rows,can_create=role in ('consultant','business_admin'),
        note='Yêu cầu lưu phạm vi và mục đích; không tự chạy Agent, kết luận đạt hoặc phê duyệt SoA.')


@router.post('/assessment-requests',status_code=201)
def create_assessment_request(assessment_id:UUID,req:AssessmentRequestInput,user:dict=Depends(require_user)):
    from backend.remediation_api import membership
    from backend.database import get_connection
    from psycopg.types.json import Jsonb
    from uuid import uuid4
    from datetime import datetime,timezone
    if membership(assessment_id,user) not in ('consultant','business_admin'):raise HTTPException(403,'Cần tư vấn hoặc quản trị doanh nghiệp lập yêu cầu.')
    scope=scope56(assessment_id,user);controls={c['control_id']:c for c in scope['controls']}
    if len(set(req.control_ids))!=len(req.control_ids) or not set(req.control_ids)<=controls.keys():raise HTTPException(422,'Mã control phải duy nhất và nằm trong phạm vi 56 hiện có.')
    rid=str(uuid4());now=datetime.now(timezone.utc).isoformat()
    doc=dict(**req.model_dump(),status='REQUESTED',rubric_sha256=scope['rubric_sha256'],
        baseline=[dict(control_id=cid,review_token=controls[cid]['review_token'],conclusion=controls[cid]['conclusion']) for cid in req.control_ids],
        history=[dict(event='requested',actor=user['user_id'],at=now,note=req.note)],professional_approval=False)
    with get_connection() as con,con.cursor() as cur:
        cur.execute('INSERT INTO enterprise_assessment_requests(request_id,assessment_id,created_by,document) VALUES(%s,%s,%s,%s)',(rid,assessment_id,user['user_id'],Jsonb(doc)))
    return dict(request_id=rid,version=1,document=doc)


class CancelAssessmentRequest(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    expected_version:int=Field(ge=1)
    note:str=Field(min_length=10,max_length=2000)


@router.post('/assessment-requests/{request_id}/cancel')
def cancel_assessment_request(assessment_id:UUID,request_id:UUID,req:CancelAssessmentRequest,user:dict=Depends(require_user)):
    from backend.remediation_api import membership
    from backend.database import get_connection
    from psycopg.types.json import Jsonb
    from datetime import datetime,timezone
    role=membership(assessment_id,user)
    if role not in ('consultant','business_admin'):raise HTTPException(403,'Vai trò này không hủy yêu cầu đánh giá.')
    with get_connection() as con,con.cursor() as cur:
        cur.execute('SELECT created_by,version,document FROM enterprise_assessment_requests WHERE assessment_id=%s AND request_id=%s FOR UPDATE',(assessment_id,request_id));row=cur.fetchone()
        if not row:raise HTTPException(404,'Không có yêu cầu thuộc đợt này.')
        author,version,doc=row
        if role!='consultant' and str(author)!=str(user['user_id']):raise HTTPException(403,'Chỉ người lập hoặc tư vấn hủy yêu cầu.')
        if version!=req.expected_version:raise HTTPException(409,'Yêu cầu đã đổi; tải lại.')
        if doc['status']=='CANCELLED':return dict(request_id=str(request_id),version=version,document=doc)
        doc['status']='CANCELLED';doc['history'].append(dict(event='cancelled',actor=user['user_id'],note=req.note,at=datetime.now(timezone.utc).isoformat()))
        cur.execute('UPDATE enterprise_assessment_requests SET version=version+1,document=%s WHERE assessment_id=%s AND request_id=%s',(Jsonb(doc),assessment_id,request_id))
    return dict(request_id=str(request_id),version=version+1,document=doc)


class ScenarioInput(BaseModel):
    scenario: str = Field(pattern='^(healthy|partial|gap)$')


class CompanyEvent(BaseModel):
    employee_id: str = Field(pattern=r'^(EMP|HF)-\d{3}$')
    action: str = Field(min_length=1, max_length=80)
    expected_snapshot_hash: str | None = Field(default=None, pattern=r'^[0-9a-f]{64}$')


@router.get('/company')
def company_inventory(assessment_id: UUID, user: dict = Depends(require_user)):
    from backend.company import snapshot
    require_campaign(assessment_id, user)
    from backend.remediation_api import membership
    return dict(snapshot(str(assessment_id)),can_manage_inventory=membership(assessment_id,user) in ('consultant','business_admin'))


class InventoryInput(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    expected_snapshot_hash:str=Field(pattern=r'^[a-f0-9]{64}$')
    name:str=Field(min_length=2,max_length=200)
    department:str=Field(min_length=2,max_length=150)
    job_title:str=Field(default='',max_length=150)
    employee_id:str|None=Field(default=None,pattern=r'^EMP-\d{3}$')
    asset_type:str=Field(default='hardware',pattern=r'^(hardware|software|physical)$')
    active:StrictBool|None=None
    employment_status:str=Field(default='active',pattern=r'^(active|terminated|onboarding)$')
    note:str=Field(min_length=10,max_length=2000)


@router.put('/company/inventory/{kind}/{identifier}')
def save_inventory(assessment_id:UUID,kind:str,identifier:str,req:InventoryInput,user:dict=Depends(require_user)):
    from backend.remediation_api import membership
    from backend.database import get_connection
    from backend.company import snapshot
    from psycopg.types.json import Jsonb
    import re
    role=membership(assessment_id,user)
    if role not in ('consultant','business_admin'):raise HTTPException(403,'Cần tư vấn hoặc quản trị doanh nghiệp quản lý danh mục.')
    if kind not in ('person','account','asset') or not re.fullmatch(r'[A-Za-z0-9_.-]{2,80}',identifier):raise HTTPException(422,'Loại hoặc mã danh mục không hợp lệ.')
    if kind=='person' and not re.fullmatch(r'EMP-\d{3}',identifier):raise HTTPException(422,'Mã nhân viên dùng EMP-001 đến EMP-999.')
    with get_connection() as con,con.cursor() as cur:
        cur.execute('SELECT inventory_mode FROM assessment_campaigns WHERE assessment_id=%s',(assessment_id,))
        if cur.fetchone()[0]!='client':raise HTTPException(409,'Danh mục khai báo dành cho đợt doanh nghiệp; lab giữ luồng mô phỏng cũ.')
        cur.execute('SELECT metadata FROM enterprise_company WHERE assessment_id=%s FOR UPDATE',(assessment_id,));cur.fetchone()
        current=snapshot(str(assessment_id),cur)
        if current['snapshot_hash']!=req.expected_snapshot_hash:raise HTTPException(409,'Danh mục đã đổi; tải snapshot mới trước khi lưu.')
        if kind!='person':
            cur.execute('SELECT 1 FROM enterprise_sim_people WHERE assessment_id=%s AND employee_id=%s',(assessment_id,req.employee_id))
            if not cur.fetchone():raise HTTPException(422,'Chọn nhân viên cùng đợt để liên kết.')
        source={'person':current['people'],'account':current['accounts'],'asset':current['assets']}[kind]
        old=next((r for r in source if r.get('id',r.get('asset_id'))==identifier),None)
        state=dict(origin='user_declared_not_verified')
        if kind=='person':
            if not req.job_title:raise HTTPException(422,'Cần chức danh nhân viên.')
            cur.execute('''INSERT INTO enterprise_sim_people(assessment_id,employee_id,display_name,department,job_title,state,employment_status)
                VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(assessment_id,employee_id) DO UPDATE SET
                display_name=EXCLUDED.display_name,department=EXCLUDED.department,job_title=EXCLUDED.job_title,employment_status=EXCLUDED.employment_status,updated_at=NOW()''',
                (assessment_id,identifier,req.name,req.department,req.job_title,Jsonb(state),req.employment_status))
        elif kind=='account':
            state.update(active=req.active,mfa=None)
            cur.execute('''INSERT INTO enterprise_company_accounts(assessment_id,account_id,employee_id,system_name,state)
                VALUES(%s,%s,%s,%s,%s) ON CONFLICT(assessment_id,account_id) DO UPDATE SET
                employee_id=EXCLUDED.employee_id,system_name=EXCLUDED.system_name,state=EXCLUDED.state,updated_at=NOW()''',
                (assessment_id,identifier,req.employee_id,req.name,Jsonb(state)))
        else:
            cur.execute('''INSERT INTO enterprise_sim_assets(assessment_id,asset_id,asset_type,asset_name,department,state)
                VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(assessment_id,asset_id) DO UPDATE SET
                asset_type=EXCLUDED.asset_type,asset_name=EXCLUDED.asset_name,department=EXCLUDED.department,updated_at=NOW()''',
                (assessment_id,identifier,req.asset_type,req.name,req.department,Jsonb(state)))
            cur.execute("DELETE FROM enterprise_sim_asset_people WHERE assessment_id=%s AND asset_id=%s AND relationship='responsible_employee'",(assessment_id,identifier))
            cur.execute("INSERT INTO enterprise_sim_asset_people VALUES(%s,%s,%s,'responsible_employee') ON CONFLICT DO NOTHING",(assessment_id,identifier,req.employee_id))
        cur.execute("INSERT INTO assessment_events(assessment_id,user_id,event_type,details) VALUES(%s,%s,'client_inventory_saved',%s)",
            (assessment_id,user['user_id'],Jsonb(dict(kind=kind,identifier=identifier,before=old,submitted=req.model_dump(exclude={'expected_snapshot_hash'})))))
        return dict(saved=True,snapshot=dict(snapshot(str(assessment_id),cur),can_manage_inventory=True),note='Khai báo danh mục không tự chứng minh tuân thủ; giữ nguồn/thẩm định riêng.')


@router.post('/company/events')
def company_event(assessment_id: UUID, req: CompanyEvent, user: dict = Depends(require_user)):
    from backend.company import change
    require_campaign(assessment_id, user)
    if req.action == 'retention_approve' and user['role'] != 'admin':
        raise HTTPException(403,detail='Chỉ admin ghi nhận phê duyệt ngoại lệ.')
    try:
        return change(str(assessment_id), req.employee_id, req.action, actor_id=user['user_id'],
                      expected_snapshot_hash=req.expected_snapshot_hash)
    except ValueError as exc:
        raise HTTPException(409, detail=str(exc)) from exc


@router.post('/company/events/preview')
def company_event_preview(assessment_id: UUID, req: CompanyEvent, user: dict = Depends(require_user)):
    from backend.company import preview
    require_campaign(assessment_id, user)
    if req.action == 'retention_approve' and user['role'] != 'admin':
        raise HTTPException(403, detail='Chỉ admin ghi nhận phê duyệt ngoại lệ.')
    try:
        return preview(str(assessment_id), req.employee_id, req.action)
    except ValueError as exc:
        raise HTTPException(409, detail=str(exc)) from exc


@router.get('/company/history')
def company_history(assessment_id: UUID, employee_id: str | None = None,
                    limit: int = Query(default=30, ge=1, le=100), user: dict = Depends(require_user)):
    from backend.company import history
    require_campaign(assessment_id, user)
    try:
        return {'items':history(str(assessment_id), employee_id, limit)}
    except ValueError as exc:
        raise HTTPException(422, detail=str(exc)) from exc


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
            if result.get('evidence_only'):
                executor.submit(execute_agent_job, result['job_id'], str(assessment_id), result['control_id'],True)
            else:
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


class SourceBatchInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    limit: int=Field(default=12,ge=1,le=56)
    force: bool=False


@router.get('/shared-work/batches')
def source_batches(assessment_id: UUID,user: dict=Depends(require_user)):
    from backend import batch_work
    require_campaign(assessment_id,user)
    return {'items':batch_work.recent(str(assessment_id))}


@router.post('/shared-work/batches',status_code=202)
def start_source_batch(assessment_id: UUID,req: SourceBatchInput,user: dict=Depends(require_user)):
    from backend import batch_work
    from backend.team_api import executor,execute_agent_job
    require_campaign(assessment_id,user)
    if user.get('role')!='admin':raise HTTPException(403,'Chỉ admin điều phối lượt đánh giá nhiều control.')
    try:result=batch_work.create(str(assessment_id),user['user_id'],req.limit,req.force)
    except ValueError as exc:raise HTTPException(409,str(exc)) from exc
    if result['action']=='started':
        try:executor.submit(batch_work.process,str(assessment_id),result['batch_id'],execute_agent_job)
        except RuntimeError as exc:
            batch_work.persist(str(assessment_id),result['batch_id'],[],'FAILED','Không khởi tạo được worker.')
            raise HTTPException(503,'Worker không sẵn sàng.') from exc
    return result


@router.post('/shared-work/batches/{batch_id}/stop')
def stop_source_batch(assessment_id: UUID,batch_id: UUID,user: dict=Depends(require_user)):
    from backend import batch_work
    require_campaign(assessment_id,user)
    if user.get('role')!='admin':raise HTTPException(403,'Chỉ admin dừng lượt đánh giá nhiều control.')
    try:return batch_work.stop(str(assessment_id),str(batch_id),user['user_id'])
    except ValueError as exc:raise HTTPException(404,str(exc)) from exc


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


class BatchScopeDecision(ScopeDecision):
    applicable: StrictBool


class DecisionBatchInput(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    assessment_id: UUID
    expected_fingerprint: str=Field(pattern=r'^[a-f0-9]{64}$')
    decisions: list[BatchScopeDecision]=Field(min_length=1,max_length=56)
    note: str=Field(min_length=20,max_length=2000)


def decision_batch_preview(assessment_id,req,user):
    from backend.decision_batch import preview
    require_campaign(assessment_id,user)
    if user.get('role')!='admin':raise HTTPException(403,'Chỉ người phụ trách admin nhập quyết định.')
    if str(assessment_id)!=str(req.assessment_id):raise HTTPException(409,'Gói thuộc đợt khác; không nhập quyết định.')
    scope=scope56(assessment_id,user)
    if scope['soa']['fingerprint']!=req.expected_fingerprint:raise HTTPException(409,'Hồ sơ đã đổi; xuất lại mẫu và xem trước trên phiên bản mới.')
    try:result=preview(scope,[d.model_dump(mode='json') for d in req.decisions])
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
    return {**result,'assessment_id':str(assessment_id),'based_on_fingerprint':req.expected_fingerprint,'note_by_owner':req.note}


@router.post('/scope56/decisions/batch/validate')
def validate_decision_batch(assessment_id: UUID,req: DecisionBatchInput,user=Depends(require_user)):
    from backend import a8_api
    with a8_api.lock:return decision_batch_preview(assessment_id,req,user)


@router.post('/scope56/decisions/batch')
def import_decision_batch(assessment_id: UUID,req: DecisionBatchInput,user=Depends(require_user)):
    import json
    from datetime import datetime,timezone
    from uuid import uuid4
    from backend import a8_api
    with a8_api.lock:
        result=decision_batch_preview(assessment_id,req,user)
        changed=[c['after'] for c in result['changes'] if c['action']!='unchanged']
        batch_id=str(uuid4()) if changed else None
        if changed:
            path=a8_api.folder(assessment_id)/'settings'/'scope56-decisions.json'
            history=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
            now=datetime.now(timezone.utc).isoformat()
            history.extend({**d,'recorded_by':user['user_id'],'recorded_at':now,
                'import_batch_id':batch_id,'import_note':req.note,'based_on_fingerprint':req.expected_fingerprint} for d in changed)
            try:a8_api.save(path,history)
            except OSError as exc:raise HTTPException(503,'Chưa lưu được gói quyết định; tải lại để kiểm tra trước khi thử lại.') from exc
    return dict(applied=len(changed),import_batch_id=batch_id,assessment_id=str(assessment_id),
        note='Đã lưu quyết định/kế hoạch của người phụ trách. Chưa thẩm định hoặc phê duyệt SoA; đọc lại các điều kiện còn thiếu.')


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


@router.post('/scope56/controls/{control_id}/sources/validate')
async def validate_control_source(assessment_id: UUID,control_id: str,
        evidence_type: str=Form(...),origin: str=Form(...),observed_at: str | None=Form(None),
        note: str=Form(''),file: UploadFile=File(...),user: dict=Depends(require_user)):
    from evidence_collectors import source_intake,control_packages
    from evidence_collectors.source_quality import text_quality
    import json
    require_campaign(assessment_id,user)
    raw=await file.read(control_packages.MAX_BYTES+1)
    if len(raw)>control_packages.MAX_BYTES:raise HTTPException(413,'Tệp quá 15MB.')
    try:item=source_intake.prepare(str(assessment_id),control_id,file.filename,raw,evidence_type,origin,observed_at,note)
    except (ValueError,UnicodeError) as exc:raise HTTPException(422,str(exc)) from exc
    return dict(preflight_only=True,original_preserved=False,evidence_saved=False,
        original_sha256=item['sha256_hash'],quality=text_quality(json.loads(item['extracted_text'])['content']),
        warnings=['Chưa lưu nguồn; kiểm tra kỹ thuật không xác nhận nguồn thật hoặc đủ tiêu chí.']+
                 ([] if observed_at else ['Chưa có thời điểm quan sát nguồn.']))


@router.post('/scope56/controls/{control_id}/sources/upload',status_code=201)
async def upload_control_source(assessment_id: UUID,control_id: str,
        evidence_type: str=Form(...),origin: str=Form(...),observed_at: str | None=Form(None),
        note: str=Form(''),file: UploadFile=File(...),user: dict=Depends(require_user)):
    from evidence_collectors import source_intake,control_packages
    require_campaign(assessment_id,user)
    raw=await file.read(control_packages.MAX_BYTES+1)
    if len(raw)>control_packages.MAX_BYTES:raise HTTPException(413,'Tệp quá 15MB.')
    try:
        item=source_intake.prepare(str(assessment_id),control_id,file.filename,raw,evidence_type,origin,observed_at,note)
        source_intake.preserve(str(assessment_id),raw)
        result=control_packages.store(str(assessment_id),control_id,user['user_id'],{'items':[item],'issues':[]})
    except (ValueError,UnicodeError) as exc:raise HTTPException(422,str(exc)) from exc
    except OSError as exc:raise HTTPException(503,'Không lưu được bản gốc. Chưa xác nhận thu nhận nguồn.') from exc
    return {**result,'evidence_id':item['evidence_id'],'original_sha256':item['sha256_hash'],
            'provenance_verified':False,'original_preserved':True}


@router.get('/scope56/controls/{control_id}/sources/{evidence_id}/original')
def download_control_source(assessment_id: UUID,control_id: str,evidence_id: str,user: dict=Depends(require_user)):
    from evidence_collectors.source_intake import retrieve
    require_campaign(assessment_id,user)
    try:path,name=retrieve(str(assessment_id),control_id,evidence_id)
    except (ValueError,OSError) as exc:raise HTTPException(404,'Không có bản gốc hợp lệ trong phạm vi truy cập.') from exc
    return FileResponse(path,filename=name,media_type='application/octet-stream',headers={'X-Content-Type-Options':'nosniff'})


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
    from backend.remediation_api import require_review_role
    require_review_role(assessment_id,user)
    with a8_api.lock:
        report=scope56(assessment_id,user)
        row=next((c for c in report['controls'] if c['control_id']==req.control_id),None)
        if not row:raise HTTPException(404,'Ngoài phạm vi 56 control.')
        if row['workflow_status']=='RUNNING' or req.review_token!=row['review_token']:raise HTTPException(409,'Dữ liệu/đánh giá đã thay đổi; tải lại trước khi xác nhận.')
        available={e['evidence_id'] for e in row['evidence']}
        if not set(req.evidence_ids)<=available:raise HTTPException(422,'Viện dẫn bằng chứng không thuộc control/đợt.')
        if req.conclusion in ('Compliant','Partially Compliant') and not req.evidence_ids:raise HTTPException(422,'Cần viện dẫn bằng chứng để xác nhận kết luận đạt/một phần.')
        from backend.review_criteria import validate,validate_sources,PROTOCOL
        try:
            validate(row['pass_criteria'],[c.model_dump() for c in req.criteria_reviews],req.evidence_ids,req.conclusion)
            validate_sources([c.model_dump() for c in req.criteria_reviews],row['evidence'])
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
        if req.fingerprint!=soa['fingerprint'] or not soa['approval_ready']:raise HTTPException(409,detail={'message':'Chưa đủ quyết định, thẩm định hoặc kế hoạch xử lý hiện hành; hoặc nguồn đã đổi.','pending_controls':soa['pending_controls'],'readiness':soa.get('readiness')})
        path=a8_api.folder(assessment_id)/'settings'/'scope56-approvals.json'
        history=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
        record={**req.model_dump(),'approved_by':user['user_id'],'approved_at':datetime.now(timezone.utc).isoformat(),
                'scope_total':56,'approval_protocol':soa.get('approval_protocol'),'meaning':'Chấp thuận SoA trong phạm vi đồ án, không phải chứng nhận ISO.'}
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
