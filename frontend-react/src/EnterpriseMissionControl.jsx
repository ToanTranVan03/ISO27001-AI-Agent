import { useEffect, useRef, useState } from "react";
import { ArrowRight, Bot, Building2, FileDown, Loader2, Send, User } from "lucide-react";
import AgentOfficeScene from "./AgentOfficeScene";
import MissionRoleInspector from "./MissionRoleInspector";
import { ROLES, STATUS_LABELS, activeRole, messagesOf, subtasksOf } from "./missionView";
import "./mission-workspace.css";
import { missionLiveFocus } from "./missionLink";

const SCOPES={all:"Toàn bộ dữ liệu lab",people:"Con người",hardware:"Phần cứng",software:"Phần mềm"};

export function MissionConversation({mission,onOpen}) {
  const messages=messagesOf(mission);const feed=useRef(null);
  useEffect(()=>{if(feed.current)feed.current.scrollTop=feed.current.scrollHeight;},[mission?.mission_id,messages.length]);
  return <section className="mw-feed" aria-label="Phản hồi công việc của các Agent">
    <div className="mw-feed-head"><h3>Trao đổi và bàn giao</h3><span>Phản hồi được ghi từ sự kiện thực thi</span></div>
    {!mission?<p className="mw-empty">Khi nhận việc, từng vai trò sẽ phản hồi tại đây. Chưa có nhiệm vụ thì không tạo lời hoàn thành.</p>:<div className="mw-feed-list" ref={feed} role="log" aria-live="polite" aria-relevant="additions">
      <article className="mw-message is-user"><div className="mw-message-avatar"><User size={15}/></div><div><b>Bạn → {ROLES.find(role=>role.id===mission.requested_role)?.agent||"Agent điều phối"}</b><time>{new Date(mission.created_at).toLocaleTimeString("vi-VN")}</time><p>{mission.goal}</p></div></article>
      {messages.map(message=>{const role=ROLES.find(item=>item.id===message.role)||ROLES[0];return <article key={message.id} className="mw-message" style={{"--role-color":role.color}}><div className="mw-message-avatar"><Bot size={16}/></div><div><b>{role.agent}</b><time>{new Date(message.at).toLocaleTimeString("vi-VN")}</time><p>{message.text}</p><small>{message.source==="legacy_trace"?"Sự kiện từ hồ sơ cũ":"Ghi nhận từ hệ thống thực thi"}</small>{message.artifact_id&&<button onClick={()=>onOpen(message.role,message.tool)}>Mở kết quả bàn giao <ArrowRight size={12}/></button>}</div></article>;})}
      {!messages.length&&<p className="mw-empty">Hồ sơ này chưa lưu phản hồi theo vai trò. Xem đầu ra hoặc nhật ký kỹ thuật.</p>}
    </div>}
  </section>;
}

export function MissionWorkView({mission,focused="coordination",selectedTool,onFocus,onTool,onInspect,onFocusEmployee}) {
  return <><div className="mw-live-layout"><AgentOfficeScene mission={mission} focused={focused} onFocus={onFocus}/><MissionRoleInspector mission={mission} roleId={focused} selectedTool={selectedTool} onTool={onTool} onInspect={onInspect} onFocusEmployee={onFocusEmployee}/></div><MissionConversation mission={mission} onOpen={(role,tool)=>{onFocus(role);onTool(tool);}}/></>;
}

export default function EnterpriseMissionControl({base,request,onInspect,officeTarget,draftRequest,onMissionChange,onFocusEmployee,officeLiveFocus}) {
  const [goal,setGoal]=useState("Kiểm tra các dấu hiệu vi phạm và lập hồ sơ bàn giao ISO");
  const [scope,setScope]=useState("all");
  const [requestedRole,setRequestedRole]=useState("coordination");
  const [mode,setMode]=useState("agent");
  const [allowFallback,setAllowFallback]=useState(false);
  const [modelStatus,setModelStatus]=useState(null);
  const [missions,setMissions]=useState([]);
  const [selected,setSelected]=useState("");
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState("");
  const [syncError,setSyncError]=useState("");
  const [note,setNote]=useState("");
  const [focused,setFocused]=useState("coordination");
  const [selectedTool,setSelectedTool]=useState(null);
  const [follow,setFollow]=useState(true);
  const [useEmployee,setUseEmployee]=useState(true);
  const [eventSelection,setEventSelection]=useState(null);
  const pending=useRef(null),sending=useRef(false),mutation=useRef(0);
  const current=missions.find(item=>item.mission_id===selected)||missions[0];
  const active=missions.some(item=>["queued","running"].includes(item.status));
  const activeMission=missions.find(item=>["queued","running"].includes(item.status))||null;
  const live=officeLiveFocus||missionLiveFocus(activeMission,null);
  const target=useEmployee&&officeTarget?{employee_id:officeTarget.employee_id,asset_id:officeTarget.asset_id,...(eventSelection?.employee_id===officeTarget.employee_id&&eventSelection.event_id?{event_id:eventSelection.event_id}:{})}:null;
  const receiver=ROLES.find(role=>role.id===requestedRole);
  const blockers=current?.tasks.find(task=>task.id==="report")?.output?.blockers||[];
  const visibleRole=follow?(activeRole(current)||(["awaiting_review","approved","revision_requested"].includes(current?.status)?"report":current?.requested_role||focused)):focused;
  const jobs=subtasksOf(current);const done=jobs.filter(task=>task.status==="completed").length;
  function focus(role){setFocused(role);setSelectedTool(null);setFollow(false);}
  useEffect(()=>{onMissionChange?.({selected:current||null,active:activeMission});},[current,activeMission,onMissionChange]);
  useEffect(()=>{
    if(!draftRequest)return;
    setUseEmployee(true);setRequestedRole("security");setScope("all");setEventSelection(draftRequest.target);
    setGoal("Kiểm tra trạng thái máy, dấu hiệu vi phạm và hồ sơ liên quan của nhân viên đang chọn");
    setFocused("security");setFollow(false);
  },[draftRequest]);

  useEffect(()=>{
    let cancelled=false,timer;
    async function check(){
      try {const data=await request(`${base}/system-readiness`);if(!cancelled)setModelStatus(data.ollama);}
      catch {if(!cancelled)setModelStatus({status:"unknown"});}
      finally {if(!cancelled)timer=setTimeout(check,15000);}
    }
    check();return ()=>{cancelled=true;clearTimeout(timer);};
  },[base,request]);
  useEffect(()=>{
    let cancelled=false,timer;
    async function poll(){
      const version=mutation.current;
      try {const data=await request(`${base}/missions`);if(!cancelled&&version===mutation.current){setMissions(data);setSyncError("");}}
      catch(err){if(!cancelled)setSyncError(err.message);}
      finally {if(!cancelled)timer=setTimeout(poll,2500);}
    }
    poll();return ()=>{cancelled=true;clearTimeout(timer);};
  },[base,request]);

  async function create(event,previous){
    event.preventDefault();if(sending.current||active)return;
    sending.current=true;mutation.current++;setBusy(true);setError("");
    const payload=previous?{goal:previous.goal,scope:previous.scope,mode:previous.mode||"workflow",allow_fallback:previous.allow_fallback||false,requested_role:previous.requested_role||"coordination",target:previous.target?{employee_id:previous.target.employee_id,asset_id:previous.target.asset_id,event_id:previous.target.event_id}:null}:{goal:goal.trim(),scope,mode,allow_fallback:allowFallback,requested_role:requestedRole,target};
    const key=JSON.stringify(payload);
    if(pending.current?.key!==key)pending.current={key,request_id:crypto.randomUUID()};
    try{
      const doc=await request(`${base}/missions`,{method:"POST",body:JSON.stringify({...payload,request_id:pending.current.request_id})});
      setMissions(items=>[doc,...items.filter(item=>item.mission_id!==doc.mission_id)]);setSelected(doc.mission_id);setNote("");setSelectedTool(null);setFollow(true);pending.current=null;
    }catch(err){setError(err.message);}
    finally{sending.current=false;setBusy(false);mutation.current++;}
  }
  async function review(decision){
    if(sending.current||!current)return;
    sending.current=true;mutation.current++;setBusy(true);setError("");
    try{
      const doc=await request(`${base}/missions/${current.mission_id}/review`,{method:"POST",body:JSON.stringify({decision,note:note.trim(),artifact_hash:current.artifact_hash})});
      setMissions(items=>items.map(item=>item.mission_id===doc.mission_id?doc:item));
    }catch(err){setError(err.message);}
    finally{sending.current=false;setBusy(false);mutation.current++;}
  }
  function download(){
    const url=URL.createObjectURL(new Blob([JSON.stringify(current,null,2)],{type:"application/json"}));
    const link=document.createElement("a");link.href=url;link.download=`mission-${current.mission_id}.json`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  return <section className="mw-workspace" aria-label="Văn phòng làm việc của các Agent">
    <header className="mw-head"><div><div className="mw-eyebrow"><Building2 size={15}/> VIỆT TÍN · AGENT WORKSPACE</div><h2>Giao một mục tiêu. Theo dõi từng vai trò làm việc.</h2><p>Chọn Agent nhận yêu cầu, theo dõi công việc con và mở kết quả của từng phòng ngay trong văn phòng.</p></div><span className="mw-head-tag">DOANH NGHIỆP GIẢ LẬP</span></header>
    <form onSubmit={create} className="mw-assign">
      <p className="mw-field" style={{marginBottom:8}}>Giao yêu cầu cho</p><div className="mw-role-choices">{ROLES.map(role=><button key={role.id} type="button" className={`mw-role-choice ${requestedRole===role.id?"is-selected":""}`} style={{"--role-color":role.color}} aria-pressed={requestedRole===role.id} disabled={busy} onClick={()=>{setRequestedRole(role.id);focus(role.id);}}><Bot size={21}/><span><b>{role.agent}</b><small>{role.job}</small></span></button>)}</div>
      <div className="mw-form-grid"><label className="mw-field">Yêu cầu gửi tới {receiver.agent}<input value={goal} onChange={e=>setGoal(e.target.value)} minLength={8} maxLength={600} disabled={busy} required/></label><label className="mw-field">Phạm vi<select value={scope} onChange={e=>setScope(e.target.value)} disabled={busy}>{Object.entries(SCOPES).map(([id,label])=><option key={id} value={id}>{label}</option>)}</select></label><button disabled={busy||active||goal.trim().length<8||!!syncError} className="mw-primary">{busy?<Loader2 size={15} className="mw-spin"/>:<Send size={15}/>}Giao nhiệm vụ</button></div>
      <div className="mw-presets"><span>Gợi ý cho vai trò này:</span><button type="button" disabled={busy} onClick={()=>{setGoal(receiver.preset);setScope(receiver.scope);}}>Điền yêu cầu mẫu</button></div>
      <div className="mw-target"><label><input type="checkbox" checked={useEmployee&&!!officeTarget} disabled={!officeTarget||busy} onChange={event=>{setUseEmployee(event.target.checked);setEventSelection(null);}}/>Kiểm tra nhân viên đang chọn ở văn phòng</label>{target?<div><b>{officeTarget.employee_name||target.employee_id}</b><code>{target.employee_id} · {target.asset_id}</code>{target.event_id&&<small>Sự kiện: {target.event_id}</small>}</div>:<p>Phạm vi toàn doanh nghiệp theo loại dữ liệu đã chọn. Chọn nhân viên bên dưới để kiểm tra riêng.</p>}</div>
      <div className="mw-options"><label>Điều phối<select value={mode} onChange={e=>setMode(e.target.value)} disabled={busy}><option value="agent">AI lập kế hoạch</option><option value="workflow">Quy trình cố định</option></select></label>{mode==="agent"&&<label><input type="checkbox" checked={allowFallback} onChange={e=>setAllowFallback(e.target.checked)} disabled={busy}/>Cho phép quy trình dự phòng nếu lập kế hoạch lỗi</label>}<span className="mw-ready">{!modelStatus?"Đang kiểm tra mô hình…":modelStatus.status==="ready"?`Ollama sẵn sàng · ${modelStatus.configured_model}`:"Mô hình chưa sẵn sàng"}</span></div>
      <p className="mw-caption">Vai trò được chọn tiếp nhận yêu cầu; Điều phối vẫn chia đủ các bước kiểm tra và bàn giao cho các phòng liên quan.</p>
    </form>
    <div className="mw-topbar"><div><strong>{current?`${STATUS_LABELS[current.status]} · ${done}/${jobs.length} công việc có kết quả`:"Chưa có nhiệm vụ"}</strong><small>{current?current.goal:"Bắt đầu bằng một yêu cầu ở phía trên."}</small></div><div className="mw-options" style={{marginTop:0}}><label><input type="checkbox" checked={follow} onChange={event=>setFollow(event.target.checked)}/>Theo dõi Agent đang làm</label>{missions.length>0&&<select aria-label="Lịch sử nhiệm vụ" value={current?.mission_id||""} onChange={event=>{setSelected(event.target.value);setNote("");setSelectedTool(null);setFollow(true);setError("");}}>{missions.map(item=><option key={item.mission_id} value={item.mission_id}>{item.goal.slice(0,40)} · {STATUS_LABELS[item.status]}</option>)}</select>}</div></div>
    {current?.target&&<div className="mw-link-banner"><span>Nhiệm vụ đang xem: <b>{current.target.employee_id}</b> · {current.target.asset_id}{current.target.event_id?` · ${current.target.event_id}`:""}</span><button onClick={()=>onFocusEmployee?.(current.target)}>Về nhân viên này <ArrowRight size={13}/></button></div>}
    {live&&<div className="mw-link-banner is-live" role="status"><span>{live.text}</span><button onClick={()=>onFocusEmployee?.(live)}>Theo dõi tại văn phòng <ArrowRight size={13}/></button></div>}
    <MissionWorkView mission={current} focused={visibleRole} selectedTool={selectedTool} onFocus={focus} onTool={setSelectedTool} onInspect={onInspect} onFocusEmployee={onFocusEmployee}/>
    <div className="mw-bottom">
      {blockers.length>0&&<div className="mw-error"><b>Hồ sơ còn hạng mục cần xử lý</b><ul className="mw-blockers">{blockers.map(item=><li key={item}>{item}</li>)}</ul></div>}
      {current?.status==="awaiting_review"&&<div className="mw-review"><h3>Hồ sơ đã bàn giao — cần bạn quyết định</h3><p>Xem kết quả của Agent kiểm soát trước khi nhận xét. Việc duyệt gắn với đúng phiên bản đầu ra.</p><textarea value={note} onChange={e=>setNote(e.target.value)} maxLength={1000} rows={2} aria-label="Nhận xét hồ sơ" placeholder="Nhận xét hoặc yêu cầu bổ sung…"/><div className="mw-review-actions"><button onClick={()=>review("approve")} disabled={busy||note.trim().length<3||blockers.length>0} className="mw-primary">Duyệt hồ sơ</button><button onClick={()=>review("request_changes")} disabled={busy||note.trim().length<3} className="mw-secondary">Yêu cầu bổ sung</button></div></div>}
      {current?.review&&<p className="mw-output-text">Nhận xét đã lưu: {current.review.note}</p>}
      {(error||syncError||current?.error)&&<p role="alert" className="mw-error">{error||syncError||current.error}</p>}
      {current&&["blocked","failed","interrupted","revision_requested"].includes(current.status)&&<div><button onClick={event=>create(event,current)} disabled={busy||active} className="mw-primary">Chạy lại mục tiêu từ dữ liệu mới</button></div>}
      {current?.trace?.length>0&&<details className="mw-trace"><summary>Nhật ký kỹ thuật · {current.trace.length} sự kiện</summary><ol>{current.trace.map((item,index)=><li key={index}><time>{new Date(item.at).toLocaleTimeString("vi-VN")}</time> <code>{item.tool} · {item.kind}</code>{item.text}{item.elapsed_ms!=null&&` · ${item.elapsed_ms} ms`}</li>)}</ol></details>}
      <div className="mw-footer"><p>Các nhân vật thể hiện vai trò dùng chung hệ thống điều phối, không phải bốn mô hình độc lập. Hoạt động và phản hồi lấy từ backend. Kết quả thuộc lab, chưa phải chứng nhận ISO.</p>{current&&<button onClick={download} className="mw-secondary"><FileDown size={14}/>Tải toàn bộ hồ sơ</button>}</div>
    </div>
  </section>;
}
