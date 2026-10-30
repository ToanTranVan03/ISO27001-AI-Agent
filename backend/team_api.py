"""Shared enterprise assessment HTTP API. All state is persisted in PostgreSQL."""
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field
from psycopg import IntegrityError

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


@router.get('/assessments/{assessment_id}/progress')
def progress(assessment_id: UUID, user: dict = Depends(require_user)):
    require_campaign(assessment_id,user)
    data = teamwork.progress_board(str(assessment_id))
    return {'assessment_id':str(assessment_id),'controls':data,
            'summary':{'total':len(data),
                       'completed':sum(x['workflow_status']=='COMPLETED' for x in data),
                       'running':sum(x['workflow_status']=='RUNNING' for x in data),
                       'waiting_evidence':sum(x['workflow_status']=='WAITING_EVIDENCE' for x in data)}}


def execute_agent_job(job_id: str, assessment_id: str, control_id: str) -> None:
    """Prototype in-process worker. Persistent lock/job survives browser refresh.

    API process restart marks interrupted jobs FAILED and unlocks controls.
    Production should replace this with an external queue/worker.
    """
    try:
        # Lazy import so the endpoints can also be tested without model execution.
        from agent_core.graph_builder import build_iso_agent_graph
        control = database.get_control(control_id)
        if not control:
            raise ValueError('Control not found')
        initial = {
            'assessment_id':assessment_id,
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
    except Exception:
        logger.exception('Agent job %s failed',job_id)
        try:
            teamwork.finish_job(job_id,None,'Không thể chạy Agent. Kiểm tra Ollama hoặc log API.')
        except Exception:
            logger.exception('Could not persist failed job %s',job_id)


@router.post('/assessments/{assessment_id}/controls/{control_id}/run',status_code=202)
def start_agent(assessment_id: UUID, control_id: str, user: dict = Depends(require_user)):
    require_campaign(assessment_id,user)
    if database.get_control(control_id) is None:
        raise HTTPException(404,detail='Không tìm thấy control.')
    try:
        job = teamwork.claim_job(str(assessment_id),control_id,user['user_id'])
    except ValueError as exc:
        raise HTTPException(409,detail='Control đang chạy bởi thành viên khác hoặc không tồn tại.') from exc
    try:
        executor.submit(execute_agent_job,job['job_id'],str(assessment_id),control_id)
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
