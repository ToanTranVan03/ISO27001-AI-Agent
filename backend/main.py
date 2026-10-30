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

# Thêm thư mục gốc vào đường dẫn hệ thống để gọi được code từ agent_core
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

# Cấu trúc dữ liệu yêu cầu từ Frontend gửi lên
class EvaluationRequest(BaseModel):
    control_id: str

@app.get("/")
async def root():
    return {"message": "Hệ thống AI Agent ISO 27001 Backend đang hoạt động!"}

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

    # 2. Chuẩn bị State ban đầu để đưa vào LangGraph
    initial_state = {
        "control_id": case["control_id"],
        "control_name": case["name"],
        "objective": case["objective"],
        "collected_evidences": [],
        "deterministic_rule": {},
        "compliance_status": "UNKNOWN",
        "confidence": 0.0,
        "rationale": "",
        "audit_trail": []
    }

    # 3. Kích hoạt Agent chạy luồng Đồ thị
    try:
        final_state = agent_graph.invoke(initial_state)
        # 4. Trả kết quả JSON sạch sẽ về cho Web/Frontend
        return {
            "control_id": final_state["control_id"],
            "status": final_state["compliance_status"],
            "confidence": final_state["confidence"],
            "rationale": final_state["rationale"],
            "audit_trail": final_state["audit_trail"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
