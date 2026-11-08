"""Authorized lab APIs, separate from the existing assessment/workflow API."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
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
