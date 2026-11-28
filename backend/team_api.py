"""Shared enterprise assessment HTTP API. All state is persisted in PostgreSQL."""
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import UUID, uuid4
from typing import Literal
from datetime import date

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field, ConfigDict,model_validator
from psycopg import IntegrityError
from psycopg.types.json import Jsonb

from backend import database, teamwork
from evidence_collectors.document_parser import extract_document_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api')
executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix='iso-agent')
MAX_UPLOAD_BYTES = 15 * 1024 * 1024


class LoginRequest(BaseModel):
    username: str
    password: str


class MemberRequest(BaseModel):
    username: str
    display_name: str
    password: str


class ReviewRequest(BaseModel):
    note: str = Field(min_length=5, max_length=1200)


def require_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(401, detail='Vui lòng đăng nhập.')
    user = teamwork.get_user_from_token(authorization[7:])
    if not user:
        raise HTTPException(401, detail='Phiên đăng nhập hết hạn hoặc không hợp lệ.')
    return user


def require_campaign(assessment_id: UUID, user: dict):
    try:
        teamwork.require_member(str(assessment_id),user['user_id'])
    except PermissionError as exc:
        raise HTTPException(403, detail='Bạn không thuộc đợt đánh giá này.') from exc


def safe_uuid(value: str) -> str:
    try: return str(UUID(value))
    except ValueError as exc: raise HTTPException(422, detail='ID không hợp lệ.') from exc


@router.post('/auth/login')
def login(req: LoginRequest):
    session = teamwork.login(req.username,req.password)
    if session is None:
        raise HTTPException(401,detail='Sai tên đăng nhập hoặc mật khẩu.')
    return session


@router.get('/auth/me')
def me(user: dict = Depends(require_user)):
    return user


class AccountProfileInput(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    display_name: str=Field(min_length=1,max_length=100)
    email: str=Field(default='',max_length=254)
    organization: str=Field(default='',max_length=150)
    position: str=Field(default='',max_length=150)


@router.get('/auth/profile')
def account_profile(user: dict=Depends(require_user)):
    try:return teamwork.account_profile(user['user_id'])
    except ValueError as exc:raise HTTPException(404,str(exc)) from exc


@router.put('/auth/profile')
def update_profile(req: AccountProfileInput,user: dict=Depends(require_user)):
    try:return teamwork.update_account_profile(user['user_id'],**req.model_dump())
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc


@router.post('/auth/logout')
def logout(authorization: str = Header(...), user: dict = Depends(require_user)):
    teamwork.logout(authorization[7:])
    return {'ok':True}


@router.post('/team/users',status_code=201)
def add_user(req: MemberRequest, user: dict = Depends(require_user)):
    try:
        return teamwork.create_user(user,req.username,req.display_name,req.password)
    except PermissionError as exc:
        raise HTTPException(403,detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422,detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(409,detail='Tên đăng nhập đã tồn tại.') from exc


@router.get('/assessments')
def assessments(user: dict = Depends(require_user)):
    return teamwork.list_assessments(user['user_id'])


class ClientInput(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    name:str=Field(min_length=2,max_length=200)
    sector:str=Field(min_length=2,max_length=300)
    contact:str=Field(min_length=2,max_length=1000)
    locations:str=Field(default='',max_length=2000)
    expected_version:int=Field(default=0,ge=0)
    data_classification:Literal['user_supplied','synthetic_development']='user_supplied'


class CampaignInput(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    name:str=Field(min_length=3,max_length=200)
    isms_scope:str=Field(min_length=10,max_length=4000)
    period_start:date|None=None
    period_end:date|None=None
    assessment_kind:Literal['initial','monthly','quarterly','annual','ad_hoc','reassessment']='ad_hoc'
    @model_validator(mode='after')
    def validate_period(self):
        if (self.period_start is None)!=(self.period_end is None):raise ValueError('Cần cả ngày bắt đầu/kết thúc kỳ hoặc để trống cả hai.')
        if self.period_start and self.period_end<self.period_start:raise ValueError('Ngày kết thúc trước bắt đầu kỳ.')
        return self


def require_admin(user):
    if user['role']!='admin':raise HTTPException(403,'Chỉ quản trị hệ thống quản lý khách hàng và thành viên.')


def require_client(cur,cid,user):
    cur.execute('''SELECT c.name,c.profile,c.version FROM consulting_clients c
        WHERE c.client_id=%s AND EXISTS(SELECT 1 FROM consulting_campaigns cc
        JOIN assessment_members m ON m.assessment_id=cc.assessment_id
        WHERE cc.client_id=c.client_id AND m.user_id=%s)''',(cid,user['user_id']))
    row=cur.fetchone()
    if not row:raise HTTPException(403,'Bạn không thuộc doanh nghiệp này.')
    return row


@router.get('/clients')
def clients(user:dict=Depends(require_user)):
    with database.get_connection() as con,con.cursor() as cur:
        cur.execute('''SELECT c.client_id,c.name,c.profile,c.version,cc.assessment_id,a.name,a.period_metadata
            FROM consulting_clients c JOIN consulting_campaigns cc ON cc.client_id=c.client_id
            JOIN assessment_campaigns a ON a.assessment_id=cc.assessment_id
            JOIN assessment_members m ON m.assessment_id=a.assessment_id
            WHERE m.user_id=%s ORDER BY c.name,a.created_at''',(user['user_id'],))
        rows={}
        for cid,name,profile,version,aid,title,period in cur.fetchall():
            item=rows.setdefault(str(cid),dict(client_id=str(cid),name=name,profile=profile,version=version,campaigns=[]))
            item['campaigns'].append(dict(assessment_id=str(aid),name=title,period=period))
    return dict(clients=list(rows.values()),can_manage=user['role']=='admin',note='Chỉ đợt được cấp quyền; doanh nghiệp mới bắt đầu rỗng, không tự nạp preset.')


@router.get('/clients/{client_id}/timeline')
def client_timeline(client_id:UUID,user:dict=Depends(require_user)):
    """Compare visible saved periods only; never infer missing periods or approvals."""
    with database.get_connection() as con,con.cursor() as cur:
        require_client(cur,client_id,user)
        cur.execute('''SELECT a.assessment_id,a.name,a.created_at,a.period_metadata FROM consulting_campaigns c
            JOIN assessment_campaigns a ON a.assessment_id=c.assessment_id
            JOIN assessment_members m ON m.assessment_id=a.assessment_id
            WHERE c.client_id=%s AND m.user_id=%s ORDER BY COALESCE(a.period_metadata->>'period_start',a.created_at::date::text),a.created_at,a.assessment_id''',(client_id,user['user_id']))
        periods=cur.fetchall()
    from backend.enterprise_api import scope56
    from backend.enterprise_comparison import summarize_periods
    rows=[]
    for aid,name,created,metadata in periods:
        scope=scope56(aid,user)
        rows.append(dict(assessment_id=str(aid),name=name,created_at=created.isoformat(),controls=scope['controls'],period=metadata))
    result=summarize_periods(str(client_id),rows)
    with database.get_connection() as con,con.cursor() as cur:
        cur.execute('''SELECT s.snapshot_id,s.assessment_id,s.created_at,s.source_sha256,s.document FROM enterprise_period_snapshots s
            JOIN consulting_campaigns c ON c.assessment_id=s.assessment_id
            JOIN assessment_members m ON m.assessment_id=s.assessment_id WHERE c.client_id=%s AND m.user_id=%s
            ORDER BY s.created_at,s.snapshot_id''',(client_id,user['user_id']))
        result['sealed_snapshots']=[dict(snapshot_id=str(sid),assessment_id=str(aid),sealed_at=at.isoformat(),source_sha256=sha,summary=doc['summary']) for sid,aid,at,sha,doc in cur.fetchall()]
    return result


class SealPeriodInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    expected_sha256:str=Field(pattern=r'^[a-f0-9]{64}$')


@router.post('/clients/{client_id}/periods/{assessment_id}/seal',status_code=201)
def seal_client_period(client_id:UUID,assessment_id:UUID,req:SealPeriodInput,user:dict=Depends(require_user)):
    require_campaign(assessment_id,user)
    from backend.remediation_api import membership
    if membership(assessment_id,user) not in ('consultant','business_admin'):raise HTTPException(403,'Cần tư vấn hoặc quản trị doanh nghiệp chốt bản lưu kỳ.')
    with database.get_connection() as con,con.cursor() as cur:
        require_client(cur,client_id,user)
        cur.execute('SELECT 1 FROM consulting_campaigns WHERE client_id=%s AND assessment_id=%s',(client_id,assessment_id))
        if not cur.fetchone():raise HTTPException(403,'Kỳ không thuộc doanh nghiệp.')
    from backend.enterprise_api import scope56
    from backend.enterprise_comparison import summarize_periods,period_fingerprint
    scope=scope56(assessment_id,user)
    fingerprint=period_fingerprint(scope['controls'])
    if fingerprint!=req.expected_sha256:raise HTTPException(409,'Dữ liệu đã đổi; tải lại trước khi chốt kỳ.')
    summary=summarize_periods(str(client_id),[dict(assessment_id=str(assessment_id),name='Sealed period',created_at='',controls=scope['controls'])])['periods'][0]
    snapshot_id=str(uuid4())
    document=dict(scope=scope,summary=summary,professional_approval=False,note='Bản lưu kết quả hiện có; không tự khóa nguồn, duyệt SoA hoặc xác nhận chuyên môn.')
    with database.get_connection() as con,con.cursor() as cur:
        cur.execute('''INSERT INTO enterprise_period_snapshots(snapshot_id,assessment_id,created_by,source_sha256,document)
            VALUES(%s,%s,%s,%s,%s) ON CONFLICT(assessment_id,source_sha256) DO NOTHING''',
            (snapshot_id,assessment_id,user['user_id'],fingerprint,Jsonb(document)))
        cur.execute('SELECT snapshot_id FROM enterprise_period_snapshots WHERE assessment_id=%s AND source_sha256=%s',(assessment_id,fingerprint))
        snapshot_id=str(cur.fetchone()[0])
    return dict(snapshot_id=snapshot_id,assessment_id=str(assessment_id),summary=summary,professional_approval=False)


def create_client_campaign(cur,cid,profile,req,user):
    aid=str(uuid4())
    cur.execute("INSERT INTO assessment_campaigns(assessment_id,name,inventory_mode,period_metadata) VALUES(%s,%s,'client',%s)",(aid,req.name,Jsonb(req.model_dump(mode='json',include={'period_start','period_end','assessment_kind'}))))
    cur.execute('INSERT INTO consulting_campaigns VALUES(%s,%s)',(aid,cid))
    cur.execute('INSERT INTO assessment_members VALUES(%s,%s)',(aid,user['user_id']))
    cur.execute('INSERT INTO control_progress(assessment_id,control_id) SELECT %s,control_id FROM controls',(aid,))
    from datetime import datetime
    from zoneinfo import ZoneInfo
    metadata=dict(name=profile['name'],synthetic=False,synthetic_dataset=profile.get('data_classification')=='synthetic_development',origin=profile.get('data_classification','user_supplied')+'_not_verified',assessment_date=datetime.now(ZoneInfo('Asia/Bangkok')).date().isoformat(),policies={})
    cur.execute('INSERT INTO enterprise_company(assessment_id,metadata) VALUES(%s,%s)',(aid,Jsonb(metadata)))
    from backend.remediation import now
    context=dict(name=profile['name'],sector=profile['sector'],isms_scope=req.isms_scope,contact=profile['contact'],locations=profile.get('locations',''),departments='',assets_systems='',obligations='',risks='',history=[dict(at=now(),actor=user['user_id'],command='client_campaign_created',note='Phạm vi do người dùng khai, chưa xác nhận chuyên môn.')])
    cur.execute("INSERT INTO remediation_records VALUES(%s,%s,'context',1,%s)",(aid,aid,Jsonb(context)))
    cur.execute("INSERT INTO assessment_events(assessment_id,user_id,event_type,details) VALUES(%s,%s,'client_campaign_created',%s)",(aid,user['user_id'],Jsonb(dict(client_id=str(cid),scope=req.isms_scope))))
    return dict(assessment_id=aid,name=req.name)


class ClientCreate(ClientInput):
    campaign:CampaignInput


@router.post('/clients',status_code=201)
def create_client(req:ClientCreate,user:dict=Depends(require_user)):
    require_admin(user)
    if req.expected_version!=0:raise HTTPException(422,'Tạo mới bắt đầu ở phiên bản 0.')
    cid=str(uuid4());profile=req.model_dump(exclude={'campaign','expected_version'})
    with database.get_connection() as con,con.cursor() as cur:
        cur.execute('INSERT INTO consulting_clients(client_id,name,profile,created_by) VALUES(%s,%s,%s,%s)',(cid,req.name,Jsonb(profile),user['user_id']))
        campaign=create_client_campaign(cur,cid,profile,req.campaign,user)
    return dict(client_id=cid,version=1,campaign=campaign)


@router.put('/clients/{client_id}')
def edit_client(client_id:UUID,req:ClientInput,user:dict=Depends(require_user)):
    require_admin(user)
    with database.get_connection() as con,con.cursor() as cur:
        require_client(cur,client_id,user)
        cur.execute('SELECT profile,version FROM consulting_clients WHERE client_id=%s FOR UPDATE',(client_id,));old,version=cur.fetchone()
        if version!=req.expected_version:raise HTTPException(409,'Hồ sơ đã đổi; tải lại.')
        if old.get('data_classification')=='synthetic_development' and req.data_classification!='synthetic_development':
            raise HTTPException(422,'Không đổi dữ liệu mô phỏng thành hồ sơ thật.')
        profile=req.model_dump(exclude={'expected_version'})
        from backend.remediation import now
        profile['history']=old.get('history',[])+[dict(at=now(),before={k:v for k,v in old.items() if k!='history'},actor=user['user_id'])]
        cur.execute('UPDATE consulting_clients SET name=%s,profile=%s,version=version+1 WHERE client_id=%s',(req.name,Jsonb(profile),client_id))
    return dict(client_id=str(client_id),version=version+1,note='Phạm vi từng đợt giữ riêng, không tự thay baseline đang đánh giá.')


class DemoDatasetInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    sizes:list[int]=Field(default=[30,100,500],min_length=1,max_length=3)
    months:int=Field(default=6,ge=1,le=24)
    seed:int=Field(default=27001,ge=0,le=2147483647)


@router.post('/demo-dataset/download')
def download_demo_dataset(req:DemoDatasetInput,user:dict=Depends(require_user)):
    require_admin(user)
    if any(n<1 or n>500 for n in req.sizes) or sum(req.sizes)*req.months>20000:
        raise HTTPException(422,'Gói web tối đa 3 doanh nghiệp, 500 người/doanh nghiệp và 20000 dòng người–kỳ; gói lớn dùng CLI.')
    from tempfile import TemporaryDirectory
    from io import BytesIO
    from zipfile import ZipFile,ZIP_DEFLATED
    from fastapi.responses import Response
    from generate_enterprise_dataset import generate
    with TemporaryDirectory(prefix='iso-synthetic-') as temp:
        root=Path(temp)/'dataset';generate(root,tuple(req.sizes),req.months,req.seed)
        out=BytesIO()
        with ZipFile(out,'w',ZIP_DEFLATED) as archive:
            for file in sorted(root.rglob('*')):
                if file.is_file():archive.write(file,file.relative_to(root).as_posix())
    return Response(out.getvalue(),media_type='application/zip',headers={'Content-Disposition':'attachment; filename="synthetic-development-dataset.zip"','Cache-Control':'no-store'})


@router.post('/clients/{client_id}/campaigns',status_code=201)
def add_client_campaign(client_id:UUID,req:CampaignInput,user:dict=Depends(require_user)):
    require_admin(user)
    with database.get_connection() as con,con.cursor() as cur:
        _,profile,_=require_client(cur,client_id,user)
        return create_client_campaign(cur,client_id,profile,req,user)


class ClientMemberInput(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    username:str=Field(pattern=r'^[A-Za-z0-9_.-]{3,40}$')
    display_name:str=Field(min_length=1,max_length=100)
    password:str=Field(default='',max_length=200)
    role:str=Field(pattern=r'^(consultant|verifier|business_admin|operator)$')


@router.post('/clients/{client_id}/campaigns/{assessment_id}/members',status_code=201)
def add_client_member(client_id:UUID,assessment_id:UUID,req:ClientMemberInput,user:dict=Depends(require_user)):
    require_admin(user);require_campaign(assessment_id,user)
    with database.get_connection() as con,con.cursor() as cur:
        require_client(cur,client_id,user)
        cur.execute('SELECT 1 FROM consulting_campaigns WHERE client_id=%s AND assessment_id=%s',(client_id,assessment_id))
        if not cur.fetchone():raise HTTPException(403,'Đợt không thuộc doanh nghiệp.')
        cur.execute('SELECT user_id FROM team_users WHERE username=%s',(req.username,));row=cur.fetchone()
        if row:
            if req.password:raise HTTPException(422,'Tài khoản đã có: để trống mật khẩu; không đổi mật khẩu tại đây.')
            uid=str(row[0])
        else:
            try:encoded=teamwork.hash_password(req.password)
            except ValueError as exc:raise HTTPException(422,str(exc)) from exc
            uid=str(uuid4())
            cur.execute("INSERT INTO team_users(user_id,username,password_hash,display_name,role) VALUES(%s,%s,%s,%s,'assessor')",(uid,req.username,encoded,req.display_name))
        cur.execute('INSERT INTO assessment_members VALUES(%s,%s) ON CONFLICT DO NOTHING',(assessment_id,uid))
        cur.execute('INSERT INTO remediation_roles VALUES(%s,%s,%s) ON CONFLICT(assessment_id,user_id) DO UPDATE SET role=EXCLUDED.role',(assessment_id,uid,req.role))
        cur.execute("INSERT INTO assessment_events(assessment_id,user_id,event_type,details) VALUES(%s,%s,'client_member_assigned',%s)",(assessment_id,user['user_id'],Jsonb(dict(user_id=uid,role=req.role))))
    return dict(user_id=uid,assessment_id=str(assessment_id),role=req.role)


@router.get('/assessments/{assessment_id}/progress')
def progress(assessment_id: UUID, user: dict = Depends(require_user)):
    require_campaign(assessment_id,user)
    data = teamwork.progress_board(str(assessment_id))
    from backend.company_evidence import fresh_progress
    data = fresh_progress(str(assessment_id),data)
    return {'assessment_id':str(assessment_id),'controls':data,
            'summary':{'total':len(data),
                       'completed':sum(x['workflow_status']=='COMPLETED' for x in data),
                       'running':sum(x['workflow_status']=='RUNNING' for x in data),
                       'waiting_evidence':sum(x['workflow_status']=='WAITING_EVIDENCE' for x in data)}}


def execute_agent_job(job_id: str, assessment_id: str, control_id: str, evidence_only: bool = False) -> None:
    """Prototype in-process worker. Persistent lock/job survives browser refresh.

    API process restart marks interrupted jobs FAILED and unlocks controls.
    Production should replace this with an external queue/worker.
    """
    try:
        # Lazy import so the endpoints can also be tested without model execution.
        from agent_core.graph_builder import build_iso_agent_graph
        if not evidence_only:
            evidence_only=teamwork.inventory_mode(assessment_id)=='client'
        control = database.get_control(control_id)
        if not control:
            raise ValueError('Control not found')
        initial = {
            'assessment_id':assessment_id,
            'source_mode':'user_evidence_only' if evidence_only else 'shared_lab',
            'control_id':control['control_id'],
            'control_name':control['name'],
            'objective':control['objective'],
            'collected_evidences':[], 'deterministic_rule':{},
            'compliance_status':'UNKNOWN','confidence':0.0,
            'rationale':'','audit_trail':[], 'validated_evidence_ids':[]
        }
        result_state = build_iso_agent_graph().invoke(initial)
        result = {
            'status':result_state['compliance_status'],
            'confidence':result_state['confidence'],
            'rationale':result_state['rationale'],
            'evidence_ids':result_state.get('validated_evidence_ids',[]),
            'audit_trail':result_state['audit_trail'],
        }
        teamwork.finish_job(job_id,result)
    except Exception as exc:
        logger.exception('Agent job %s failed',job_id)
        try:
            from pydantic import ValidationError
            from agent_core.model_input import InputBudgetExceeded
            message=str(exc) if isinstance(exc,InputBudgetExceeded) else 'Phản hồi model không đúng JSON/schema; chưa lưu kết luận. Xem log API.' if isinstance(exc,ValidationError) else 'Không thể chạy Agent. Kiểm tra Ollama hoặc log API.'
            teamwork.finish_job(job_id,None,message)
        except Exception:
            logger.exception('Could not persist failed job %s',job_id)


@router.post('/assessments/{assessment_id}/controls/{control_id}/run',status_code=202)
def start_agent(assessment_id: UUID, control_id: str, user: dict = Depends(require_user), evidence_only: bool = False):
    require_campaign(assessment_id,user)
    if database.get_control(control_id) is None:
        raise HTTPException(404,detail='Không tìm thấy control.')
    try:
        job = teamwork.claim_job(str(assessment_id),control_id,user['user_id'])
    except ValueError as exc:
        raise HTTPException(409,detail='Control đang chạy bởi thành viên khác hoặc không tồn tại.') from exc
    try:
        if evidence_only:executor.submit(execute_agent_job,job['job_id'],str(assessment_id),control_id,True)
        else:executor.submit(execute_agent_job,job['job_id'],str(assessment_id),control_id)
    except RuntimeError as exc:
        teamwork.finish_job(job['job_id'],None,'Không thể khởi tạo worker.')
        raise HTTPException(503,detail='Worker không khả dụng.') from exc
    return job


@router.get('/jobs/{job_id}')
def job(job_id: UUID, user: dict = Depends(require_user)):
    data = teamwork.get_job(str(job_id))
    if not data:raise HTTPException(404,detail='Không tìm thấy tác vụ.')
    require_campaign(UUID(data['assessment_id']),user)
    return data


@router.get('/assessments/{assessment_id}/controls/{control_id}/history')
def history(assessment_id: UUID, control_id: str, user: dict = Depends(require_user)):
    require_campaign(assessment_id,user)
    return teamwork.list_history(str(assessment_id),control_id)


@router.post('/assessments/{assessment_id}/controls/{control_id}/evidence',status_code=201)
async def upload_evidence(assessment_id: UUID, control_id: str,
                          evidence_type: str = Form(...),file: UploadFile = File(...),
                          user: dict = Depends(require_user)):
    require_campaign(assessment_id,user)
    control = database.get_control(control_id)
    if not control:
        raise HTTPException(404,detail='Không tìm thấy control.')
    if evidence_type not in control['expected_evidence_types']:
        raise HTTPException(422,detail='Loại bằng chứng không hợp lệ cho control.')
    name = Path(file.filename or '').name
    if Path(name).suffix.lower() not in {'.pdf','.docx'}:
        raise HTTPException(415,detail='Chỉ hỗ trợ PDF hoặc DOCX.')
    body = await file.read(MAX_UPLOAD_BYTES+1)
    if len(body)>MAX_UPLOAD_BYTES:
        raise HTTPException(413,detail='Tệp quá 15MB.')
    try:
        extracted = extract_document_text(name,body)
    except ValueError as exc:
        raise HTTPException(422,detail=str(exc)) from exc
    evidence_id=str(uuid4())
    try:
        teamwork.store_campaign_evidence(str(assessment_id),control_id,user['user_id'],
                                         evidence_id,evidence_type,name,extracted,
                                         hashlib.sha256(body).hexdigest())
    except ValueError as exc:
        raise HTTPException(409,detail=str(exc)) from exc
    return {'evidence_id':evidence_id,'control_id':control_id,'source':name,
            'sha256_hash':hashlib.sha256(body).hexdigest(),'characters':len(extracted)}


@router.post('/assessments/{assessment_id}/controls/{control_id}/review')
def approve_review(assessment_id: UUID,control_id: str,req: ReviewRequest,
                   user: dict=Depends(require_user)):
    require_campaign(assessment_id,user)
    if user['role']!='admin':
        raise HTTPException(403,detail='Chỉ admin được xác nhận kết quả cần review.')
    try:
        teamwork.review(str(assessment_id),control_id,user['user_id'],req.note)
    except ValueError as exc:
        raise HTTPException(409,detail=str(exc)) from exc
    return {'ok':True}
