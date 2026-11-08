import {useRef,useState} from 'react';
import {Bot,Send,ArrowUpRight,Loader2} from 'lucide-react';
import {ROLES,STATUS_LABELS,messagesOf,subtasksOf,sourceForRole} from './missionView';
import {agentSubmission} from './office3dModel';

export default function AgentOfficeConsole({roleId,base,request,employees,target,onTargetChange,mission,onCreated,onOpenDetails,onBack}) {
  const role=ROLES.find(r=>r.id===roleId)||ROLES[0];
  const [goal,setGoal]=useState(role.preset),[mode,setMode]=useState('agent'),[fallback,setFallback]=useState(false);
  const [busy,setBusy]=useState(false),[error,setError]=useState('');
  const pending=useRef(null),sending=useRef(false);
  const active=['queued','running'].includes(mission?.status);
  async function submit(event){
    event.preventDefault();if(sending.current||active)return;
    try{
      const body=agentSubmission(roleId,goal,mode,fallback,target),key=JSON.stringify(body);
      if(pending.current?.key!==key)pending.current={key,request_id:crypto.randomUUID()};
      sending.current=true;setBusy(true);setError('');
      const doc=await request(`${base}/missions`,{method:'POST',body:JSON.stringify({...body,request_id:pending.current.request_id})});
      onCreated(doc);pending.current=null;
    }catch(e){setError(e.message);}finally{sending.current=false;setBusy(false);}
  }
  const jobs=subtasksOf(mission).filter(t=>t.role===roleId),messages=messagesOf(mission).filter(m=>m.role===roleId).slice(-5);
  return <aside className="oi3d-agent-console" aria-label={`Bình luận giao việc cho ${role.agent}`} style={{'--role-color':role.color}}>
    <header><div className="oi3d-agent-icon"><Bot size={25}/></div><span>PHÒNG AGENT</span><h2>{role.agent}</h2><p>{role.job}</p><button onClick={onBack}>← Bình luận cho nhân viên</button></header>
    <form onSubmit={submit}><label>Nhân viên / máy mục tiêu<select value={target?.employee_id||''} onChange={e=>onTargetChange(e.target.value)} disabled={busy}>{!target&&<option value="">Chờ đồng bộ…</option>}{employees.map(p=><option key={p.employee_id} value={p.employee_id}>{p.employee_id} · {p.display_name}</option>)}</select></label><p className="oi3d-agent-target">{target?.asset_id||'Chọn nhân viên có máy trước khi giao việc'}</p><label>Bình luận mục tiêu<textarea value={goal} onChange={e=>setGoal(e.target.value)} minLength={8} maxLength={600} rows={4} disabled={busy} placeholder="Ví dụ: Kiểm tra USB lạ trên máy nhân viên đang chọn"/></label>
    <label>Cách thực thi<select value={mode} onChange={e=>setMode(e.target.value)} disabled={busy}><option value="agent">LLM lập kế hoạch</option><option value="workflow">Workflow quy tắc</option></select></label>{mode==='agent'&&<label className="oi3d-check"><input type="checkbox" checked={fallback} onChange={e=>setFallback(e.target.checked)}/>Cho phép workflow nếu bước lập kế hoạch LLM lỗi</label>}
    {error&&<p className="oi3d-error" role="alert">{error}</p>}<button type="submit" className="oi3d-send" disabled={busy||active||!target}>{busy?<Loader2 size={15}/>:<Send size={15}/>} {busy?'Đang gửi mục tiêu…':active?'Nhiệm vụ hiện tại đang chạy':'Gửi bình luận giao việc'}</button><p className="oi3d-agent-help">Gửi sẽ tạo nhiệm vụ thật trong lab. Nhân vật chỉ làm việc khi backend ghi nhận công việc đang chạy.</p></form>
    <section className="oi3d-agent-work"><h3>Công việc của phòng</h3>{mission&&<p className="oi3d-agent-source">Nhiệm vụ đang xem: {mission.target?.employee_id||'Phạm vi doanh nghiệp'} · {mission.goal}</p>}{!jobs.length&&<p>Chưa có công việc được bàn giao.</p>}{jobs.map(job=><article key={job.id}><b>{job.title||job.purpose}</b><span>{STATUS_LABELS[job.status]||job.status}</span></article>)}{mission&&<p className="oi3d-agent-source">Nguồn: {sourceForRole(mission,roleId)}</p>}{messages.map(message=><p className="oi3d-agent-reply" key={message.id}>{message.text}</p>)}{mission?.status==='awaiting_review'&&<p className="oi3d-review">Hồ sơ đã lập, đang chờ người phụ trách xem và duyệt.</p>}<button className="oi3d-details" onClick={()=>onOpenDetails(roleId)}>Mở công việc, kết quả và bàn duyệt<ArrowUpRight size={14}/></button></section>
  </aside>;
}
