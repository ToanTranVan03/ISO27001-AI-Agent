from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import FileResponse, StreamingResponse, Response, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Literal
import mimetypes
import sys
import os
import json
import threading
from contextlib import asynccontextmanager

# Thêm thư mục gốc vào đường dẫn hệ thống để gọi được code từ agent_core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent_core.simulation import SCENARIOS, ModelUnavailable, build_enterprise, run_simulation
from agent_core.autonomous import AgentStore, agent_events
from agent_core.live import LiveMonitor

import hashlib
import logging
from uuid import uuid4, UUID
from dotenv import load_dotenv
from fastapi import Depends, File, Form, UploadFile
from psycopg import Error as PostgresError
from backend import database, teamwork, enterprise_lab, incident_simulation
from backend.team_api import router as team_router, require_user, require_campaign
from backend import company
from backend.company_monitor import CompanyMonitor
from backend.enterprise_api import router as enterprise_router
from backend.incident_api import router as incident_router
from backend.a8_api import router as a8_router, recover_interrupted
from agent_core.graph_builder import build_iso_agent_graph
from evidence_collectors.document_parser import extract_document_text

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / '.env')
logger = logging.getLogger(__name__)
FRONTEND_PATH = ROOT_DIR / 'frontend' / 'workspace.html'
LEGACY_FRONTEND_PATH = ROOT_DIR / 'frontend' / 'index.html'
ENTERPRISE_PATH = ROOT_DIR / 'frontend' / 'enterprise.html'
REACT_DIST = ROOT_DIR / 'frontend-react' / 'dist'
MAX_UPLOAD_BYTES = 15 * 1024 * 1024

live_monitors = {}
live_lock = threading.Lock()


def resolve_company(user, assessment_id=None):
    if assessment_id is None:
        campaigns = teamwork.list_assessments(user['user_id'])
        if not campaigns:
            raise HTTPException(403, detail='Chưa thuộc đợt đánh giá nào.')
        assessment_id = str(campaigns[0]['assessment_id'])
    require_campaign(assessment_id, user)
    return str(assessment_id)


def get_live_monitor(assessment_id):
    with live_lock:
        if assessment_id not in live_monitors:
            live_monitors[assessment_id] = CompanyMonitor(assessment_id)
        monitor = live_monitors[assessment_id]
        monitor.start()
        return monitor


@asynccontextmanager
async def lifespan(app):
    database.initialize_database()
    teamwork.init_teamwork()
    enterprise_lab.init_enterprise_lab()
    incident_simulation.initialize_incident_simulation()
    recover_interrupted()
    yield
    for monitor in live_monitors.values():
        monitor.stop()
    live_monitors.clear()

# Khởi tạo API Server
app = FastAPI(title="ISO 27001 AI Agent API", version="1.0", lifespan=lifespan)

# Shared evidence workflow used by the authenticated assessment API.
agent_graph = build_iso_agent_graph()
app.include_router(team_router)
app.include_router(enterprise_router)
app.include_router(incident_router)
app.include_router(a8_router)
app.mount('/assets', StaticFiles(directory=REACT_DIST / 'assets', check_dir=False), name='react-assets')

STATIC_DIR = Path(__file__).parent / 'static'
mimetypes.add_type('application/javascript', '.mjs')
app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')


class SimulationRequest(BaseModel):
    scenario_id: str
    mode: Literal['rules', 'ai'] = 'rules'


class AgentRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=1000)
    mode: Literal['ai', 'workflow'] = 'ai'


class BusinessEventRequest(BaseModel):
    person_id: str = Field(min_length=1, max_length=80)
    action: str = Field(min_length=1, max_length=80)


@app.get('/api/live')
def live_state(assessment_id: UUID | None = None, user: dict = Depends(require_user)):
    return get_live_monitor(resolve_company(user, assessment_id)).state()


@app.get('/api/live/report')
def live_report(assessment_id: UUID | None = None, user: dict = Depends(require_user)):
    state = get_live_monitor(resolve_company(user, assessment_id)).state()
    return Response(json.dumps(state, ensure_ascii=False, indent=2), media_type='application/json',
                    headers={'Content-Disposition': f'attachment; filename="hivefive-evidence-r{state["revision"]}.json"'})


@app.get('/api/research')
def research_results():
    path = Path(__file__).resolve().parent.parent / 'docs' / 'research-results.json'
    if not path.exists():
        raise HTTPException(status_code=404, detail='Chưa chạy thực nghiệm.')
    return FileResponse(path, media_type='application/json')


@app.post('/api/live/events')
def business_event(req: BusinessEventRequest, assessment_id: UUID | None = None, user: dict = Depends(require_user)):
    aid = resolve_company(user, assessment_id)
    if req.action == 'retention_approve' and user['role'] != 'admin':
        raise HTTPException(403,detail='Chỉ admin ghi nhận phê duyệt ngoại lệ.')
    try:
        return get_live_monitor(aid).change(req.person_id, req.action, actor_id=user['user_id'])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post('/api/agent/run')
def run_agent(req: AgentRequest, assessment_id: UUID | None = None, user: dict = Depends(require_user)):
    aid = resolve_company(user, assessment_id)
    data = company.snapshot(aid)
    store = get_live_monitor(aid).store
    if not req.goal.strip():
        raise HTTPException(status_code=422, detail='Hãy nhập mục tiêu kiểm tra.')
    def stream():
        for event in agent_events(req.goal.strip(), req.mode, store, snapshot=(data, f"company:{aid}", data["snapshot_hash"])):
            yield json.dumps(event, ensure_ascii=False) + '\n'
    return StreamingResponse(stream(), media_type='application/x-ndjson', headers={'Cache-Control': 'no-store'})


@app.get('/api/agent/history')
def agent_history(assessment_id: UUID | None = None, user: dict = Depends(require_user)):
    return get_live_monitor(resolve_company(user, assessment_id)).store.history()


@app.get('/api/agent/latest')
def agent_latest(assessment_id: UUID | None = None, user: dict = Depends(require_user)):
    return get_live_monitor(resolve_company(user, assessment_id)).store.latest()


@app.get('/simulation', include_in_schema=False)
def simulation_page():
    return RedirectResponse(url='/',status_code=307)


@app.get('/api/simulation')
def simulation_catalog(assessment_id: UUID | None = None, user: dict = Depends(require_user)):
    scenarios = [{**s, 'name':'Hiện trạng doanh nghiệp', 'description':'Đọc dữ liệu dùng chung; không đặt lại hồ sơ.'} if s['id']=='baseline' else s for s in SCENARIOS]
    return {'enterprise': company.snapshot(resolve_company(user, assessment_id)), 'scenarios': scenarios}


@app.post('/api/simulation/run')
def simulate(req: SimulationRequest, assessment_id: UUID | None = None, user: dict = Depends(require_user)):
    aid = resolve_company(user, assessment_id)
    try:
        return run_simulation(req.scenario_id, req.mode, company.apply_scenario(aid, req.scenario_id, actor_id=user['user_id']), apply_selected=False)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ModelUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

# Cấu trúc dữ liệu yêu cầu từ Frontend gửi lên
class EvaluationRequest(BaseModel):
    control_id: str = Field(min_length=1, max_length=20)




def react_frontend():
    index = REACT_DIST / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=503, detail="React chưa build. Chạy npm run build trong frontend-react.")
    return FileResponse(index)


@app.get("/", include_in_schema=False)
def home():
    return react_frontend()


@app.get("/spacebase", include_in_schema=False)
def spacebase_page():
    return react_frontend()


@app.get("/workspace", include_in_schema=False)
def workspace_page():
    return FileResponse(FRONTEND_PATH)


@app.get("/enterprise")
async def enterprise_page():
    return FileResponse(ENTERPRISE_PATH)


@app.get("/legacy")
async def legacy_page():
    return FileResponse(LEGACY_FRONTEND_PATH)


@app.get("/api/controls")
async def get_controls(user: dict = Depends(require_user)):
    try:
        return database.list_controls()
    except (PostgresError, RuntimeError) as exc:
        logger.exception("Could not list ISO controls.")
        raise HTTPException(status_code=503, detail="Database is unavailable.") from exc


@app.post("/api/evidence", status_code=201)
async def upload_evidence(
    control_id: str = Form(...),
    evidence_type: str = Form(...),
    file: UploadFile = File(...),
    user: dict = Depends(require_user),
    assessment_id: UUID | None = None,
):
    aid = resolve_company(user, assessment_id)
    try:
        control = database.get_control(control_id)
    except (PostgresError, RuntimeError) as exc:
        logger.exception("Could not load control for evidence upload.")
        raise HTTPException(status_code=503, detail="Database is unavailable.") from exc

    if control is None:
        raise HTTPException(status_code=404, detail="Control not found.")
    if evidence_type not in control["expected_evidence_types"]:
        raise HTTPException(
            status_code=422,
            detail="Evidence type is not allowed for this control.",
        )

    filename = Path(file.filename or "").name
    if Path(filename).suffix.lower() not in {".pdf", ".docx"}:
        raise HTTPException(
            status_code=415,
            detail="Only PDF and DOCX files are supported.",
        )

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Maximum file size is 15 MB.")

    try:
        extracted_text = extract_document_text(filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    digest = hashlib.sha256(content).hexdigest()
    try:
        database.save_evidence(
            evidence_id=str(uuid4()),
            control_id=control_id,
            evidence_type=evidence_type,
            source=filename,
            extracted_text=extracted_text,
            sha256_hash=digest, assessment_id=aid, uploaded_by=user["user_id"],
        )
    except (PostgresError, RuntimeError) as exc:
        logger.exception("Could not save uploaded evidence.")
        raise HTTPException(
            status_code=503,
            detail="Could not save evidence to database.",
        ) from exc

    return {
        "control_id": control_id,
        "evidence_type": evidence_type,
        "source": filename,
        "sha256_hash": digest,
        "extracted_characters": len(extracted_text),
    }


@app.post("/api/evaluate")
async def evaluate_control(req: EvaluationRequest, user: dict = Depends(require_user), assessment_id: UUID | None = None):
    aid = resolve_company(user, assessment_id)
    try:
        control = database.get_control(req.control_id)
    except (PostgresError, RuntimeError) as exc:
        logger.exception("Could not load control for evaluation.")
        raise HTTPException(status_code=503, detail="Database is unavailable.") from exc

    if control is None:
        raise HTTPException(status_code=404, detail="Control not found.")

    initial_state = {
        "assessment_id": aid,
        "control_id": control["control_id"],
        "control_name": control["name"],
        "objective": control["objective"],
        "collected_evidences": [],
        "deterministic_rule": {},
        "compliance_status": "UNKNOWN",
        "confidence": 0.0,
        "rationale": "",
        "audit_trail": [],
    }

    try:
        final_state = agent_graph.invoke(initial_state)
        result = {
            "control_id": final_state["control_id"],
            "status": final_state["compliance_status"],
            "confidence": final_state["confidence"],
            "rationale": final_state["rationale"],
            "evidence_ids": final_state.get("validated_evidence_ids", []),
            "audit_trail": final_state["audit_trail"],
        }
        result.update(assessment_id=aid, evaluated_by=user["user_id"])
        database.save_evaluation(result)
        return result
    except database.EvaluationBusy as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except PostgresError as exc:
        logger.exception("Could not persist evaluation.")
        raise HTTPException(
            status_code=503,
            detail="Could not save evaluation.",
        ) from exc
    except Exception as exc:
        logger.exception("ISO control evaluation failed.")
        raise HTTPException(
            status_code=502,
            detail="Evaluation failed. Check the API logs and verify Ollama is available.",
        ) from exc
