"""Authenticated API for the synthetic 56-control incident-response lab."""

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from queue import Empty, Queue
from threading import Event, Lock, Thread
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend import incident_simulation
from backend.incident_catalog import SCENARIO_BY_CONTROL
from backend.team_api import require_campaign, require_user


router = APIRouter(
    prefix="/api/assessments/{assessment_id}/enterprise",
    tags=["Synthetic Incident Response"],
)
logger = logging.getLogger(__name__)
simulation_workers = ThreadPoolExecutor(max_workers=2, thread_name_prefix="incident-lab")
monitor_registry: dict[str, dict] = {}
monitor_registry_lock = Lock()
assessment_scan_locks: dict[str, Lock] = {}


def _scan_lock(assessment_id: str) -> Lock:
    with monitor_registry_lock:
        return assessment_scan_locks.setdefault(assessment_id, Lock())


def _process_monitor_findings(assessment_id: str, user_id: str, scan: dict, emit=None) -> list[dict]:
    reports = []
    for finding in scan["findings"]:
        scenario = incident_simulation.SCENARIO_BY_CONTROL[finding["control_id"]]
        issue = (
            f"Quét tự động phát hiện {finding['summary']} "
            f"Tài sản {finding['asset_name']} ({finding['asset_id']}), "
            f"nhân sự phụ trách {finding.get('employee_id') or 'chưa xác định'}; "
            f"thời điểm {finding['observed_at']}."
        )
        classification = {
            "control_id": scenario["control_id"], "severity": scenario["severity"],
            "confidence": 0.96, "needs_more_info": False,
            "rationale": f"Telemetry endpoint ghi nhận {finding['event_type']}; Agent đối chiếu mục tiêu kiểm soát {scenario['control_id']}.",
            "reported_at": (datetime.fromisoformat(finding["observed_at"])-timedelta(seconds=1)).isoformat(), "model": "enterprise-telemetry-agent",
            "original_issue": issue, "domain": scenario["domain"],
            "domain_label": scenario["domain_label"],
            "matched_control": {"control_id": scenario["control_id"], "name": scenario["control_name"], "objective": scenario["objective"]},
            "simulation_target": scenario["target"], "human_context": scenario["human_context"],
            "telemetry_finding": finding, "is_synthetic": True,
        }
        if emit:
            emit({"type": "finding_detected", "text": finding["summary"], "finding": finding})
        report = incident_simulation.run_incident(
            assessment_id, scenario["control_id"], user_id,
            on_progress=emit, reported_issue=issue, classification=classification,
        )
        incident_simulation.mark_activity_triaged(
            assessment_id, finding["asset_id"], finding["event_id"], report["incident_id"]
        )
        reports.append(report)
    return reports


def _automatic_monitor_worker(assessment_id: str, user_id: str, stop_event: Event, state: dict) -> None:
    try:
        while not stop_event.is_set():
            with _scan_lock(assessment_id):
                scan = incident_simulation.scan_enterprise_activity(assessment_id)
                state["last_scan_at"] = scan["scanned_at"]
                state["checked_assets"] = scan["checked_assets"]
                state["last_error"] = None
                if scan["findings"]:
                    state["state"] = "processing"
                    reports = _process_monitor_findings(assessment_id, user_id, scan)
                    if reports:
                        state["last_detection"] = {
                            "at": datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).isoformat(),
                            "findings": scan["findings"],
                            "incident_ids": [report["incident_id"] for report in reports],
                            "control_ids": [report["control_id"] for report in reports],
                            "verified": all(report["verified"] for report in reports),
                        }
                state["state"] = "monitoring"
            stop_event.wait(5)
    except Exception as exc:
        logger.exception("Automatic endpoint monitor failed for assessment %s", assessment_id)
        state["last_error"] = type(exc).__name__
        state["state"] = "error"
    finally:
        state["active"] = False
        if state["state"] != "error":
            state["state"] = "stopped"


class IncidentIssueRequest(BaseModel):
    issue: str = Field(min_length=12, max_length=2000)


class IncidentChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class SimulatedEmployeeActivityRequest(BaseModel):
    activity_type: Literal["unapproved_usb_inserted", "unapproved_software_installed"]


@router.get("/scenarios")
def scenarios(assessment_id: UUID, user: dict = Depends(require_user)):
    require_campaign(assessment_id, user)
    items = incident_simulation.list_scenarios(str(assessment_id))
    return {
        "company": "Công ty Việt Tín Logistics (doanh nghiệp giả lập)",
        "is_synthetic": True,
        "domains": ["people", "hardware", "software"],
        "control_count": len(items),
        "scenarios": items,
    }


@router.get("/people")
def people(assessment_id: UUID, user: dict = Depends(require_user)):
    """Synthetic staff directory and their relationships to lab devices/apps."""
    require_campaign(assessment_id, user)
    items = incident_simulation.list_people(str(assessment_id))
    return {
        "is_synthetic": True,
        "employee_count": len(items),
        "linked_asset_count": sum(len(item["linked_assets"]) for item in items),
        "employees": items,
    }


@router.get("/incidents")
def incidents(
    assessment_id: UUID,
    limit: int = Query(default=50, ge=1, le=200),
    user: dict = Depends(require_user),
):
    require_campaign(assessment_id, user)
    return incident_simulation.list_incidents(str(assessment_id), limit)


@router.get("/metrics")
def evaluation_metrics(assessment_id: UUID, user: dict = Depends(require_user)):
    """Outcome and scenario-coverage metrics for the academic experiment."""
    require_campaign(assessment_id, user)
    return incident_simulation.get_evaluation_metrics(str(assessment_id))


@router.get("/system-readiness")
def system_readiness(assessment_id: UUID, user: dict = Depends(require_user)):
    """Report whether the authenticated enterprise lab and optional model are ready."""
    require_campaign(assessment_id, user)
    try:
        return incident_simulation.get_system_readiness(str(assessment_id))
    except Exception as exc:
        logger.exception("Enterprise lab readiness check failed")
        raise HTTPException(status_code=503, detail="Không kiểm tra được trạng thái lab.") from exc


@router.post("/issues/simulate/stream")
def simulate_described_issue(
    assessment_id: UUID,
    body: IncidentIssueRequest,
    user: dict = Depends(require_user),
):
    """Let the Agent classify a free-text incident before choosing the response path."""
    require_campaign(assessment_id, user)
    issue = " ".join(body.issue.strip().split())
    if len(issue) < 12:
        raise HTTPException(status_code=422, detail="Mô tả sự cố cần ít nhất 12 ký tự.")

    events: Queue[dict] = Queue()

    def run():
        try:
            classification = incident_simulation.classify_issue(issue, on_progress=events.put)
            if classification["needs_more_info"] or not classification["control_id"]:
                return
            result = incident_simulation.run_incident(
                str(assessment_id), classification["control_id"], user["user_id"],
                on_progress=events.put, reported_issue=issue, classification=classification,
            )
            events.put({"type": "result", "result": result})
        except Exception:
            logger.exception("Incident analysis/response failed")
            events.put({"type": "error", "text": "Agent không hoàn tất được phân tích. Kiểm tra log máy chủ."})

    future = simulation_workers.submit(run)

    def event_stream():
        yield "retry: 1500\n\n"
        while True:
            try:
                event = events.get(timeout=15)
            except Empty:
                if future.done():
                    break
                yield ": agent-working\n\n"
                continue
            yield "data: " + json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n\n"
            if event["type"] in {"result", "error", "needs_more_info"}:
                break

    return StreamingResponse(
        event_stream(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/monitor/scan/stream")
def scan_enterprise_devices(
    assessment_id: UUID,
    user: dict = Depends(require_user),
):
    """Proactively scan recent synthetic endpoint events without a user-authored incident."""
    require_campaign(assessment_id, user)
    events: Queue[dict] = Queue()

    def run():
        try:
            with _scan_lock(str(assessment_id)):
                scan = incident_simulation.scan_enterprise_activity(str(assessment_id))
                events.put({"type": "scan_started", "text": f"Agent đang quét nhật ký của {scan['checked_assets']} thiết bị/phần mềm doanh nghiệp.", "scan": {k:v for k,v in scan.items() if k != "findings"}})
                reports = _process_monitor_findings(str(assessment_id), user["user_id"], scan, events.put)
            summary = (
                f"Đã quét {scan['checked_assets']} thiết bị/phần mềm. Không có dấu hiệu mới đang chờ xử lý."
                + (f" {len(scan.get('recently_processed', []))} tín hiệu trong 10 phút gần đây đã được Agent xử lý trước đó; xem lịch sử để mở hồ sơ, hệ thống không chạy trùng."
                   if scan.get("recently_processed") else " Không phát hiện dấu hiệu cần xử lý trong nhật ký giả lập hiện có.")
                if not reports else
                f"Đã quét {scan['checked_assets']} thiết bị/phần mềm và phát hiện {len(reports)} dấu hiệu cần xử lý. " + " ".join(
                    f"{item['control_id']} ({item['classification']['matched_control']['name']}): {item['event']}. {item['agent_rationale']}"
                    for item in reports
                )
            )
            if reports:
                primary = reports[0]
                combined = {**primary, "scan_summary": summary, "scan_findings": scan["findings"],
                            "scan_results": reports,
                            "actions": [action for report in reports for action in report["actions"]],
                            "verified": all(report["verified"] for report in reports)}
            else:
                combined = {"scan_only": True, "scan_summary": summary, "scan_findings": [],
                            "checked_assets": scan["checked_assets"], "verified": True,
                            "previously_processed": scan.get("recently_processed", []),
                            "actions": [], "is_synthetic": True, "status": "NO_FINDINGS"}
            events.put({"type": "result", "result": combined})
        except Exception:
            logger.exception("Proactive enterprise endpoint scan failed")
            events.put({"type": "error", "text": "Agent không hoàn tất được quét thiết bị. Kiểm tra log máy chủ."})

    future = simulation_workers.submit(run)

    def event_stream():
        yield "retry: 1500\n\n"
        while True:
            try:
                event = events.get(timeout=15)
            except Empty:
                if future.done():
                    break
                yield ": agent-working\n\n"
                continue
            yield "data: " + json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n\n"
            if event["type"] in {"result", "error"}:
                break

    return StreamingResponse(
        event_stream(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/monitor/simulate-activity")
def simulate_employee_endpoint_activity(
    assessment_id: UUID,
    body: SimulatedEmployeeActivityRequest,
    user: dict = Depends(require_user),
):
    """Create a safe, fixed synthetic event so the monitor has something to discover."""
    require_campaign(assessment_id, user)
    try:
        return incident_simulation.simulate_employee_activity(str(assessment_id), body.activity_type)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/monitor/drill/next")
def generate_next_coverage_drill(assessment_id: UUID, user: dict = Depends(require_user)):
    """Generate the least-tested control scenario automatically, with no control picker."""
    require_campaign(assessment_id, user)
    try:
        return incident_simulation.generate_next_control_drill(str(assessment_id))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/monitor/auto/start")
def start_automatic_monitor(assessment_id: UUID, user: dict = Depends(require_user)):
    require_campaign(assessment_id, user)
    key = str(assessment_id)
    with monitor_registry_lock:
        existing = monitor_registry.get(key)
        if existing and existing["thread"].is_alive() and existing["state"].get("active"):
            return dict(existing["state"])
        stop_event = Event()
        state = {
            "assessment_id": key, "active": True, "state": "starting",
            "interval_seconds": 5, "started_at": datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).isoformat(),
            "last_scan_at": None, "last_detection": None, "last_error": None,
        }
        thread = Thread(
            target=_automatic_monitor_worker,
            args=(key, user["user_id"], stop_event, state),
            name=f"enterprise-monitor-{key[:8]}", daemon=True,
        )
        monitor_registry[key] = {"thread": thread, "stop_event": stop_event, "state": state}
        thread.start()
    return dict(state)


@router.post("/monitor/auto/stop")
def stop_automatic_monitor(assessment_id: UUID, user: dict = Depends(require_user)):
    require_campaign(assessment_id, user)
    key = str(assessment_id)
    with monitor_registry_lock:
        existing = monitor_registry.get(key)
        if not existing:
            return {"assessment_id": key, "active": False, "state": "stopped"}
        existing["stop_event"].set()
        existing["state"]["state"] = "stopping"
        return dict(existing["state"])


@router.get("/monitor/auto/status")
def automatic_monitor_status(assessment_id: UUID, user: dict = Depends(require_user)):
    require_campaign(assessment_id, user)
    key = str(assessment_id)
    with monitor_registry_lock:
        existing = monitor_registry.get(key)
        if not existing:
            return {"assessment_id": key, "active": False, "state": "stopped"}
        state = dict(existing["state"])
        state["active"] = bool(state.get("active") and existing["thread"].is_alive())
        return state


@router.post("/incidents/{incident_id}/chat/stream")
def chat_about_saved_incident(
    assessment_id: UUID,
    incident_id: UUID,
    body: IncidentChatRequest,
    user: dict = Depends(require_user),
):
    require_campaign(assessment_id, user)
    if incident_simulation.get_incident(str(assessment_id), str(incident_id)) is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ sự cố.")
    events: Queue[dict] = Queue()

    def run():
        try:
            answer = incident_simulation.chat_about_incident(
                str(assessment_id), str(incident_id), body.message
            )
            events.put({"type": "chat_response", **answer})
        except ValueError as exc:
            events.put({"type": "error", "text": str(exc)})
        except Exception:
            logger.exception("Incident follow-up chat failed for %s", incident_id)
            events.put({"type": "error", "text": "AI không trả lời được câu hỏi này."})

    future = simulation_workers.submit(run)

    def event_stream():
        yield "retry: 1500\n\n"
        while True:
            try:
                event = events.get(timeout=15)
            except Empty:
                if future.done():
                    break
                yield ": agent-working\n\n"
                continue
            yield "data: " + json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n\n"
            if event["type"] in {"chat_response", "error"}:
                break

    return StreamingResponse(
        event_stream(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/incidents/{incident_id}/chat")
def saved_incident_chat(
    assessment_id: UUID,
    incident_id: UUID,
    user: dict = Depends(require_user),
):
    require_campaign(assessment_id, user)
    if incident_simulation.get_incident(str(assessment_id), str(incident_id)) is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ sự cố.")
    return incident_simulation.list_incident_chat(str(incident_id))


@router.post("/controls/{control_id}/simulate", status_code=201)
def simulate_incident(
    assessment_id: UUID,
    control_id: str,
    user: dict = Depends(require_user),
):
    require_campaign(assessment_id, user)
    try:
        return incident_simulation.run_incident(
            str(assessment_id), control_id, user["user_id"]
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/controls/{control_id}/simulate/stream")
def simulate_incident_stream(
    assessment_id: UUID,
    control_id: str,
    user: dict = Depends(require_user),
):
    require_campaign(assessment_id, user)
    if control_id not in SCENARIO_BY_CONTROL:
        raise HTTPException(status_code=404, detail="Không có kịch bản cho kiểm soát này.")

    events: Queue[dict] = Queue()

    def run():
        try:
            result = incident_simulation.run_incident(
                str(assessment_id), control_id, user["user_id"], on_progress=events.put
            )
            events.put({"type": "result", "result": result})
        except Exception:
            logger.exception("Incident simulation failed for %s", control_id)
            events.put({"type": "error", "text": "Agent không hoàn tất được tình huống. Kiểm tra log máy chủ."})

    future = simulation_workers.submit(run)

    def event_stream():
        yield "retry: 1500\n\n"
        while True:
            try:
                event = events.get(timeout=15)
            except Empty:
                if future.done():
                    break
                yield ": agent-working\n\n"
                continue
            yield "data: " + json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n\n"
            if event["type"] in {"result", "error"}:
                break

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
