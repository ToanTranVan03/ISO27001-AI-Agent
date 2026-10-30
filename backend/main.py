from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import FileResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Literal
import mimetypes
import sys
import os
import json
import threading
from contextlib import asynccontextmanager

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent_core.simulation import SCENARIOS, ModelUnavailable, build_enterprise, run_simulation
from agent_core.autonomous import AgentStore, agent_events
from agent_core.live import LiveMonitor

live_monitor = None
live_lock = threading.Lock()


def get_live_monitor():
    global live_monitor
    with live_lock:
        if live_monitor is None:
            live_monitor = LiveMonitor()
        live_monitor.start()
        return live_monitor


@asynccontextmanager
async def lifespan(app):
    get_live_monitor()
    yield
    if live_monitor:
        live_monitor.stop()

# Khởi tạo API Server
app = FastAPI(title="ISO 27001 AI Agent API", version="1.0", lifespan=lifespan)

# Load legacy model/benchmark dependencies only when the legacy API is called.
agent_graph = None

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
def live_state():
    return get_live_monitor().state()


@app.get('/api/live/report')
def live_report():
    state = get_live_monitor().state()
    return Response(json.dumps(state, ensure_ascii=False, indent=2), media_type='application/json',
                    headers={'Content-Disposition': f'attachment; filename="hivefive-evidence-r{state["revision"]}.json"'})


@app.get('/api/research')
def research_results():
    path = Path(__file__).resolve().parent.parent / 'docs' / 'research-results.json'
    if not path.exists():
        raise HTTPException(status_code=404, detail='Chưa chạy thực nghiệm.')
    return FileResponse(path, media_type='application/json')


@app.post('/api/live/events')
def business_event(req: BusinessEventRequest):
    try:
        return get_live_monitor().change(req.person_id, req.action)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post('/api/agent/run')
def run_agent(req: AgentRequest):
    if not req.goal.strip():
        raise HTTPException(status_code=422, detail='Hãy nhập mục tiêu kiểm tra.')
    def stream():
        for event in agent_events(req.goal.strip(), req.mode):
            yield json.dumps(event, ensure_ascii=False) + '\n'
    return StreamingResponse(stream(), media_type='application/x-ndjson', headers={'Cache-Control': 'no-store'})


@app.get('/api/agent/history')
def agent_history():
    return AgentStore().history()


@app.get('/api/agent/latest')
def agent_latest():
    return AgentStore().latest()


@app.get('/simulation', include_in_schema=False)
def simulation_page():
    return FileResponse(STATIC_DIR / 'index.html')


@app.get('/api/simulation')
def simulation_catalog():
    return {'enterprise': build_enterprise(), 'scenarios': SCENARIOS}


@app.post('/api/simulation/run')
def simulate(req: SimulationRequest):
    try:
        return run_simulation(req.scenario_id, req.mode)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ModelUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

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
):
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
            sha256_hash=digest,
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
def evaluate_control(req: EvaluationRequest):
    global agent_graph
    from agent_core.graph_builder import build_iso_agent_graph
    from agent_core.enterprise_eval_and_charts import ENTERPRISE_TEST_CASES

    if agent_graph is None:
        agent_graph = build_iso_agent_graph()
    # 1. Tìm thông tin control trong dữ liệu giả lập Tuần 1
    case = next((c for c in ENTERPRISE_TEST_CASES if c["control_id"] == req.control_id), None)
    
    if not case:
        raise HTTPException(status_code=404, detail="Không tìm thấy mã Control này trong hệ thống.")

    initial_state = {
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
