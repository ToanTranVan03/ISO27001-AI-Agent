import hashlib
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4
from fastapi.staticfiles import StaticFiles

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from psycopg import Error as PostgresError

from agent_core.graph_builder import build_iso_agent_graph
from backend import database, teamwork, enterprise_lab, auto_audit
from backend.team_api import router as team_router, require_user
from backend.enterprise_api import router as enterprise_router
from evidence_collectors.document_parser import extract_document_text

logger = logging.getLogger(__name__)
ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_PATH = ROOT_DIR / "frontend" / "workspace.html"
LEGACY_FRONTEND_PATH = ROOT_DIR / "frontend" / "index.html"
ENTERPRISE_PATH = ROOT_DIR / "frontend" / "enterprise.html"
MAX_UPLOAD_BYTES = 15 * 1024 * 1024


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.initialize_database()
    teamwork.init_teamwork()
    enterprise_lab.init_enterprise_lab()
    auto_audit.initialize_auto_audit()
    yield


app = FastAPI(
    title="ISO 27001 AI Agent API",
    version="1.0",
    lifespan=lifespan,
)

# React is the primary frontend; FastAPI still owns the protected API.
REACT_DIST = ROOT_DIR / "frontend-react" / "dist"
ASSETS_DIR = REACT_DIST / "assets"
if ASSETS_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="react-assets")

agent_graph = build_iso_agent_graph()
app.include_router(team_router)
app.include_router(enterprise_router)
app.include_router(auto_audit.router)


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
async def evaluate_control(req: EvaluationRequest, user: dict = Depends(require_user)):
    try:
        control = database.get_control(req.control_id)
    except (PostgresError, RuntimeError) as exc:
        logger.exception("Could not load control for evaluation.")
        raise HTTPException(status_code=503, detail="Database is unavailable.") from exc

    if control is None:
        raise HTTPException(status_code=404, detail="Control not found.")

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
        database.save_evaluation(result)
        return result
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
