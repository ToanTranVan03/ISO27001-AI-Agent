"""Authenticated compliance assessment API: 56 controls and the A.8 study."""
import hashlib
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4, UUID
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from psycopg import Error as PostgresError
from backend import database, teamwork, enterprise_lab, company_storage
from backend.team_api import router as team_router, require_user, require_campaign
from backend.enterprise_api import router as enterprise_router
from backend.a8_api import router as a8_router, recover_interrupted
from agent_core.graph_builder import build_iso_agent_graph
from evidence_collectors.document_parser import extract_document_text

ROOT_DIR=Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR/'.env')
logger=logging.getLogger(__name__)
REACT_DIST=ROOT_DIR/'frontend-react'/'dist'
MAX_UPLOAD_BYTES=15*1024*1024

def resolve_company(user, assessment_id=None):
    if assessment_id is None:
        campaigns = teamwork.list_assessments(user['user_id'])
        if not campaigns:
            raise HTTPException(403, detail='Chưa thuộc đợt đánh giá nào.')
        assessment_id = str(campaigns[0]['assessment_id'])
    require_campaign(assessment_id, user)
    return str(assessment_id)


@asynccontextmanager
async def lifespan(app):
    database.initialize_database()
    teamwork.init_teamwork()
    enterprise_lab.init_enterprise_lab()
    company_storage.initialize_company_inventory()
    recover_interrupted()
    yield

app=FastAPI(title='ISO 27001 AI Agent API',version='1.0',lifespan=lifespan)
agent_graph=build_iso_agent_graph()
app.include_router(team_router)
app.include_router(enterprise_router)
app.include_router(a8_router)
app.mount('/assets',StaticFiles(directory=REACT_DIST/'assets',check_dir=False),name='react-assets')

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


@app.get('/workspace', include_in_schema=False)
@app.get('/enterprise', include_in_schema=False)
@app.get('/legacy', include_in_schema=False)
@app.get('/simulation', include_in_schema=False)
def retired_page():
    return RedirectResponse(url='/',status_code=307)


@app.get('/favicon.svg', include_in_schema=False)
def favicon():
    return FileResponse(ROOT_DIR/'frontend-react'/'public'/'favicon.svg',media_type='image/svg+xml')


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
    except database.EvaluationBusy as exc:
        raise HTTPException(status_code=409,detail=str(exc)) from exc
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
def evaluate_control(req: EvaluationRequest, user: dict = Depends(require_user), assessment_id: UUID | None = None):
    aid = resolve_company(user, assessment_id)
    try:
        control = database.get_control(req.control_id)
    except (PostgresError, RuntimeError) as exc:
        logger.exception("Could not load control for evaluation.")
        raise HTTPException(status_code=503, detail="Database is unavailable.") from exc

    if control is None:
        raise HTTPException(status_code=404, detail="Control not found.")

    # Legacy synchronous endpoint must share the same claim as the primary API.
    try:
        job=teamwork.claim_job(aid,req.control_id,user['user_id'])
    except ValueError as exc:
        raise HTTPException(409,'Control đang chạy hoặc không thuộc đợt đánh giá.') from exc
    except PostgresError as exc:
        raise HTTPException(503,'Database is unavailable.') from exc
    completed=False

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
        teamwork.finish_job(job['job_id'],result)
        completed=True
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
    finally:
        if not completed:
            try:teamwork.finish_job(job['job_id'],None,'Lượt đánh giá đồng bộ thất bại; xem log API.')
            except Exception:logger.exception('Could not release failed synchronous evaluation %s',job['job_id'])
