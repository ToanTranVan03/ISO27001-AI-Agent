"""Explicit identifiers connecting employee commands, mission tools and incidents."""
from backend.database import get_connection
from backend.incident_catalog import SCENARIO_BY_CONTROL


def identity(target):
    return {key:target.get(key) for key in ("employee_id","asset_id","event_id")} if target else None


def matches(item,target):
    if not target:return True
    return all(not target.get(key) or item.get(key)==target[key] for key in ("employee_id","asset_id","event_id"))


def incident_matches(event,target):
    if not target:return True
    classification=(event or {}).get("ai_classification") or {}
    finding=classification.get("telemetry_finding") or {}
    return matches({"employee_id":finding.get("employee_id") or (event or {}).get("human_context",{}).get("employee_id"),
                    "asset_id":finding.get("asset_id") or (event or {}).get("affected_target",{}).get("asset_id"),
                    "event_id":finding.get("event_id")},target)


def resolve_target(assessment_id,target):
    if not target:return None
    employee_id=target["employee_id"];asset_id=target.get("asset_id") or f"OFFICE-{employee_id}"
    if asset_id!=f"OFFICE-{employee_id}":
        raise ValueError("Máy kiểm tra phải là máy riêng của nhân viên được chọn.")
    with get_connection() as con,con.cursor() as cur:
        cur.execute("""SELECT p.display_name,a.asset_name FROM enterprise_sim_asset_people l
            JOIN enterprise_sim_people p ON p.assessment_id=l.assessment_id AND p.employee_id=l.employee_id
            JOIN enterprise_sim_assets a ON a.assessment_id=l.assessment_id AND a.asset_id=l.asset_id
            WHERE l.assessment_id=%s AND l.employee_id=%s AND l.asset_id=%s LIMIT 1""",(assessment_id,employee_id,asset_id))
        row=cur.fetchone()
        if not row:raise ValueError("Không tìm thấy nhân viên và máy trong đợt đánh giá này.")
        event_id=target.get("event_id")
        if event_id:
            cur.execute("SELECT details FROM enterprise_sim_asset_activity WHERE assessment_id=%s AND asset_id=%s AND event_id=%s",(assessment_id,asset_id,event_id))
            event=cur.fetchone()
            if not event or event[0].get("employee_id")!=employee_id:
                raise ValueError("Sự kiện không thuộc đúng nhân viên và máy được chọn.")
    return {"employee_id":employee_id,"asset_id":asset_id,"event_id":event_id,"employee_name":row[0],"asset_name":row[1]}


def processed_events(assessment_id,target,scope):
    if not target:return []
    with get_connection() as con,con.cursor() as cur:
        cur.execute("""SELECT a.event_id,a.asset_id,a.observed_at,a.summary,i.incident_id,i.control_id,i.status,i.model_name
            FROM enterprise_sim_asset_activity a JOIN enterprise_incidents i
            ON i.assessment_id=a.assessment_id AND i.incident_id::text=a.details->>'triaged_by_incident'
            WHERE a.assessment_id=%s AND a.asset_id=%s AND a.details->>'employee_id'=%s
            AND (%s::text IS NULL OR a.event_id=%s)
            ORDER BY a.observed_at DESC LIMIT 10""",(assessment_id,target["asset_id"],target["employee_id"],target.get("event_id"),target.get("event_id")))
        return [{"event_id":row[0],"asset_id":row[1],"employee_id":target["employee_id"],"observed_at":row[2].isoformat(),"summary":row[3],
                 "incident_id":str(row[4]),"control_id":row[5],"verified":row[6]=="RESOLVED","model":row[7],"source":"previously_processed"}
                for row in cur.fetchall() if scope=="all" or SCENARIO_BY_CONTROL.get(row[5],{}).get("domain")==scope][:5]
