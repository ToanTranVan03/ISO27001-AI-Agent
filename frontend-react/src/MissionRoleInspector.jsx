import { ArrowUpRight, Bot, CheckCircle2, Download, Loader2 } from "lucide-react";
import { ROLES, STATUS_LABELS, TOOL_LABELS, outputOf, roleStatus, sourceForRole, subtasksOf } from "./missionView";
import { linkedRecord } from "./missionLink";

function downloadArtifact(mission,task) {
  const output=outputOf(mission,task);
  if(!output)return;
  const blob=new Blob([JSON.stringify({mission_id:mission.mission_id,artifact_id:task.artifact_id,role:task.role,tool:task.tool,captured_output:output},null,2)],{type:"application/json"});
  const url=URL.createObjectURL(blob);const link=document.createElement("a");link.href=url;link.download=`${mission.mission_id}-${task.tool}.json`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}

function CaseRecord({record,previous,onInspect,onFocusEmployee}) {
  return <article className="mw-case"><b>{record.control_id} · {record.verified?"Đã xác minh":"Cần rà soát"}</b>{previous&&<span>Đã xử lý trước lượt kiểm tra này · liên kết hồ sơ có sẵn</span>}<span>{record.employee_id||""} {record.asset_id?`· ${record.asset_id}`:""}</span><span>{record.model==="policy-fallback"?"Nguồn: Quy tắc dự phòng":`Nguồn: ${record.model||"Hồ sơ đã có"}`}</span><p>{record.agent_rationale||record.summary}</p>{onFocusEmployee&&record.employee_id&&<button onClick={()=>onFocusEmployee(record)}>Xem nhân viên và máy ở văn phòng <ArrowUpRight size={13}/></button>}{onInspect&&<button onClick={()=>onInspect({...record,detected_control:record.control_id})}>Mở hồ sơ sự cố <ArrowUpRight size={13}/></button>}</article>;
}

function Output({task,data,onInspect,onFocusEmployee}) {
  if(!data)return <p className="mw-empty">Chưa có đầu ra được lưu cho phần việc này.</p>;
  if(task.tool==="coordination")return <div><p className="mw-output-text">{data.objective||data.goal}</p>{data.checklist?.length>0&&<ul className="mw-checklist">{data.checklist.map(item=><li key={item}><CheckCircle2 size={13}/>{item}</li>)}</ul>}<p className="mw-caption">Tiêu chí gợi ý của kế hoạch; kết quả phải được công cụ xác minh.</p></div>;
  if(task.tool==="inventory")return <div><div className="mw-output-counts"><b>{data.people?.length||0}<small>hồ sơ nhân sự</small></b><b>{data.assets?.length||0}<small>tài sản</small></b></div><ul className="mw-records">{(data.assets?.length?data.assets:data.people||[]).slice(0,5).map(item=><li key={item.asset_id||item.employee_id}><span>{item.name}</span><code>{item.asset_id||item.employee_id}</code></li>)}</ul><p className="mw-caption">Hiển thị tối đa 5 mục. Tải đầu ra để xem toàn bộ danh mục.</p></div>;
  if(task.tool==="workstations")return <div><div className="mw-output-counts"><b>{data.workstations?.length||0}<small>máy đã đọc</small></b><b>{(data.workstations||[]).filter(item=>item.state?.network_isolated).length}<small>máy cô lập</small></b></div><ul className="mw-records">{(data.workstations||[]).slice(0,5).map(item=><li key={item.employee_id}><code>{item.employee_id}</code><span>{item.state?.screen_state==="locked"?"Màn hình khóa":"Màn hình mở"}{item.state?.usb_connected?" · Có USB":""}</span></li>)}</ul></div>;
  if(task.tool==="security")return <div><div className="mw-output-counts"><b>{data.scan?.findings?.length||0}<small>dấu hiệu mới</small></b><b>{(data.reports||[]).filter(item=>item.verified).length}<small>xác minh trong lượt này</small></b></div>{!data.reports?.length&&<p className="mw-output-text">Không có kết quả ứng phó mới trong lượt này.{data.previously_processed?.length?" Có hồ sơ đã xử lý được liên kết bên dưới.":""}</p>}{data.scan?.findings?.map(item=><div key={item.event_id} className="mw-case"><b>Dấu hiệu: {item.control_id}</b><p>{item.employee_id} · {item.asset_id}</p><span>{item.event_id}</span>{onFocusEmployee&&item.employee_id&&<button onClick={()=>onFocusEmployee(item)}>Đến nhân viên này <ArrowUpRight size={13}/></button>}</div>)}{(data.reports||[]).map(item=><CaseRecord key={item.incident_id} record={linkedRecord(item,data.scan?.findings)} onInspect={onInspect} onFocusEmployee={onFocusEmployee}/>)}{(data.previously_processed||[]).map(item=><CaseRecord key={`prior-${item.event_id}`} record={item} previous onInspect={onInspect} onFocusEmployee={onFocusEmployee}/>)}</div>;
  return <div><p className="mw-output-text">{data.summary}</p><div className="mw-output-counts"><b>{data.processed_count||0}<small>đã xử lý</small></b><b>{data.remaining_count||0}<small>dấu hiệu còn lại</small></b></div>{data.blockers?.length>0?<ul className="mw-blockers">{data.blockers.map(item=><li key={item}>{item}</li>)}</ul>:<p className="mw-caption">Chưa có hạng mục chặn trong ảnh chụp kết quả này. Người phụ trách vẫn cần duyệt hồ sơ.</p>}</div>;
}

export default function MissionRoleInspector({mission,roleId,selectedTool,onTool,onInspect,onFocusEmployee}) {
  const role=ROLES.find(item=>item.id===roleId)||ROLES[0];
  const tasks=subtasksOf(mission).filter(item=>item.role===role.id);
  const task=tasks.find(item=>item.tool===selectedTool)||tasks.find(item=>item.status==="running")||tasks.at(-1);
  const data=outputOf(mission,task);
  const state=roleStatus(mission,role.id);
  return <aside className="mw-inspector" aria-label={`Công việc của ${role.agent}`} style={{"--role-color":role.color}}>
    <header><div className="mw-role-icon"><Bot size={25}/></div><div><span className="mw-eyebrow">PHÒNG ĐANG XEM</span><h3>{role.agent}</h3><p>{role.job}</p></div><span className={`mw-status is-${state}`}>{state==="running"&&<Loader2 size={12} className="mw-spin"/>}{STATUS_LABELS[state]}</span></header>
    <p className="mw-source">Nguồn: {sourceForRole(mission,role.id)}</p>
    <div className="mw-inspector-body"><h4>Công việc con <span>{tasks.length}</span></h4>{!tasks.length&&<p className="mw-empty">{mission?"Chưa có việc được bàn giao cho vai trò này.":"Giao một mục tiêu để điều phối chia việc."}</p>}
    <ol className="mw-role-jobs">{tasks.map(item=><li key={item.id}><button className={task?.id===item.id?"is-selected":""} onClick={()=>onTool(item.tool)}><span className={`mw-job-dot is-${item.status}`}/><span><b>{item.title||TOOL_LABELS[item.tool]}</b><small>{STATUS_LABELS[item.status]}{item.finished_at?` · ${new Date(item.finished_at).toLocaleTimeString("vi-VN")}`:""}</small></span></button></li>)}</ol>
    {task&&<div className="mw-selected-job"><p className="mw-job-purpose">{task.purpose||task.title}</p>{task.status==="running"&&<p className="mw-running"><Loader2 size={13} className="mw-spin"/>Công cụ đang chạy. Chưa có đầu ra hoàn tất.</p>}{task.error&&<p className="mw-error">{task.error}</p>}<div className="mw-artifact-heading"><h4>Kết quả bàn giao</h4>{data&&<button onClick={()=>downloadArtifact(mission,task)} aria-label={`Tải đầu ra ${task.title}`}><Download size={14}/>Tải</button>}</div><Output task={task} data={data} onInspect={onInspect} onFocusEmployee={onFocusEmployee}/>{data&&<details className="mw-technical"><summary>Dữ liệu kỹ thuật</summary><pre>{JSON.stringify(data,null,2)}</pre></details>}</div>}
    </div>
  </aside>;
}
