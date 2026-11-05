import { useEffect, useRef, useState } from "react";
import { Building2, CheckCircle2, FileDown, Loader2, Send } from "lucide-react";
import DepartmentHeadquarters from "./DepartmentHeadquarters";

const DEPARTMENTS=[
  {id:"coordination",name:"Điều phối",role:"Nhận chủ đề · chia bước",icon:"01",color:"#78d7e9"},
  {id:"inventory",name:"Tài sản & nhân sự",role:"Thu thập danh mục · bàn giao",icon:"02",color:"#ffca91"},
  {id:"security",name:"SOC · ứng phó",role:"Quét dấu hiệu · gọi công cụ",icon:"03",color:"#c4b5ff"},
  {id:"report",name:"Kiểm soát nội bộ",role:"Lập hồ sơ · chờ người duyệt",icon:"04",color:"#6ee7b7"},
];
const LABELS={waiting:"Chờ bàn giao",running:"Đang thực hiện",completed:"Đã bàn giao",blocked:"Bị chặn",failed:"Gặp lỗi",queued:"Đã nhận nhiệm vụ",awaiting_review:"Chờ người phụ trách duyệt",approved:"Đã duyệt hồ sơ",revision_requested:"Yêu cầu bổ sung",interrupted:"Bị gián đoạn"};
const SCOPES={all:"Toàn bộ dữ liệu lab",people:"Con người",hardware:"Phần cứng",software:"Phần mềm"};

function outputSummary(task) {
  if(!task?.output) return null;
  const data=task.output;
  if(task.id==="coordination") return `Phạm vi: ${SCOPES[data.scope]}`;
  if(task.id==="inventory") return `${data.people.length} hồ sơ nhân sự · ${data.assets.length} tài sản`;
  if(task.id==="security") return `${data.scan.findings.length} dấu hiệu · ${data.reports.length} kết quả xử lý`;
  return data.summary;
}

export default function EnterpriseMissionControl({base,request}) {
  const [goal,setGoal]=useState("Kiểm tra các dấu hiệu vi phạm và lập hồ sơ bàn giao ISO");
  const [scope,setScope]=useState("all");
  const [missions,setMissions]=useState([]);
  const [selected,setSelected]=useState("");
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState("");
  const [syncError,setSyncError]=useState("");
  const [note,setNote]=useState("");
  const [focused,setFocused]=useState(null);
  const pending=useRef(null);
  const sending=useRef(false);
  const current=missions.find(item=>item.mission_id===selected)||missions[0];
  const active=missions.some(item=>["queued","running"].includes(item.status));
  const blockers=current?.tasks.find(task=>task.id==="report")?.output?.blockers||[];
  useEffect(()=>{
    let cancelled=false,timer;
    async function poll(){
      try {const data=await request(`${base}/missions`);if(!cancelled){setMissions(data);setSyncError("");}}
      catch(err){if(!cancelled)setSyncError(err.message);}
      finally {if(!cancelled)timer=setTimeout(poll,2500);}
    }
    poll();return ()=>{cancelled=true;clearTimeout(timer);};
  },[base,request]);
  async function create(event){
    event.preventDefault();if(sending.current||active)return;
    sending.current=true;setBusy(true);setError("");
    const key=JSON.stringify({goal:goal.trim(),scope});
    if(pending.current?.key!==key)pending.current={key,request_id:crypto.randomUUID()};
    try{
      const doc=await request(`${base}/missions`,{method:"POST",body:JSON.stringify({goal:goal.trim(),scope,request_id:pending.current.request_id})});
      setMissions(items=>[doc,...items.filter(item=>item.mission_id!==doc.mission_id)]);setSelected(doc.mission_id);setNote("");pending.current=null;
    }catch(err){setError(err.message);}
    finally{sending.current=false;setBusy(false);}
  }
  async function review(decision){
    if(sending.current||!current)return;
    sending.current=true;setBusy(true);setError("");
    try{
      const doc=await request(`${base}/missions/${current.mission_id}/review`,{method:"POST",body:JSON.stringify({decision,note:note.trim()})});
      setMissions(items=>items.map(item=>item.mission_id===doc.mission_id?doc:item));
    }catch(err){setError(err.message);}
    finally{sending.current=false;setBusy(false);}
  }
  function download(){
    const url=URL.createObjectURL(new Blob([JSON.stringify(current,null,2)],{type:"application/json"}));
    const link=document.createElement("a");link.href=url;link.download=`mission-${current.mission_id}.json`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  return <section className="mb-5 overflow-hidden rounded-[28px] border border-cyan-200/20 bg-[#142334]" aria-label="Trụ sở điều phối doanh nghiệp">
    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 bg-gradient-to-r from-cyan-300/10 to-emerald-300/5 p-5"><div><div className="flex items-center gap-2 text-[10px] font-black tracking-widest text-cyan-200"><Building2 size={16}/> VIỆT TÍN · TRỤ SỞ ĐIỀU PHỐI</div><h2 className="mt-2 text-xl font-black">Một nhiệm vụ. Mỗi phòng một phần việc.</h2><p className="mt-2 max-w-3xl text-xs leading-5 text-slate-400">Giao chủ đề kiểm tra ISO. Các phòng bàn giao dữ liệu, SOC dùng Agent hiện có để xử lý dấu hiệu, hồ sơ cuối cùng chờ bạn duyệt.</p></div><span className="rounded-full border border-white/15 px-3 py-2 text-[10px] text-emerald-200">DỮ LIỆU DOANH NGHIỆP GIẢ LẬP</span></div>
    <form onSubmit={create} className="flex flex-wrap items-end gap-3 border-b border-white/10 p-5"><label className="min-w-56 flex-1 text-xs text-slate-300">Chủ đề kiểm tra<input value={goal} onChange={e=>setGoal(e.target.value)} minLength={8} maxLength={600} disabled={busy} className="mt-2 block w-full rounded-xl border border-white/15 bg-[#0d1b2a] p-3 text-sm text-white"/></label><label className="text-xs text-slate-300">Phạm vi<select value={scope} onChange={e=>setScope(e.target.value)} disabled={busy} className="mt-2 block rounded-xl border border-white/15 bg-[#0d1b2a] p-3 text-sm text-white">{Object.entries(SCOPES).map(([id,label])=><option key={id} value={id}>{label}</option>)}</select></label><button disabled={busy||active||goal.trim().length<8||!!syncError} className="flex items-center gap-2 rounded-xl bg-cyan-200 px-4 py-3 text-xs font-black text-slate-950 disabled:opacity-40">{busy?<Loader2 size={16} className="animate-spin"/>:<Send size={16}/>}Giao nhiệm vụ kiểm tra</button></form>
    <DepartmentHeadquarters tasks={current?.tasks} focused={focused} onFocus={setFocused}/>
    <div className="p-5"><div className="mb-4 flex flex-wrap items-center justify-between gap-3"><p role="status" className="text-xs text-cyan-100">{current?`${LABELS[current.status]} · ${current.tasks.filter(task=>task.status==="completed").length}/4 phần việc`:"Các phòng sẵn sàng nhận nhiệm vụ"}</p>{missions.length>0&&<label className="text-[10px] text-slate-400">Lịch sử nhiệm vụ<select aria-label="Chọn nhiệm vụ" value={current?.mission_id||""} onChange={e=>{setSelected(e.target.value);setNote("");setError("");}} className="ml-2 max-w-64 rounded-lg bg-[#0d1b2a] p-2 text-xs text-slate-200">{missions.map(item=><option key={item.mission_id} value={item.mission_id}>{item.goal.slice(0,45)} · {LABELS[item.status]}</option>)}</select></label>}</div>
      {current&&<p className="mb-4 text-sm font-bold text-white">{current.goal} <span className="ml-2 text-[10px] font-normal text-slate-400">{SCOPES[current.scope]}</span></p>}
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{DEPARTMENTS.map(dept=>{const task=current?.tasks.find(item=>item.id===dept.id);return <article key={dept.id} className="rounded-2xl border bg-[#0e1c2b] p-4" style={{borderColor:`${dept.color}40`}}><div className="flex items-center justify-between"><span className="flex h-10 w-10 items-center justify-center rounded-xl border text-sm font-black" style={{color:dept.color,borderColor:`${dept.color}50`}}>{dept.icon}</span>{task?.status==="running"?<Loader2 size={18} className="animate-spin text-cyan-200"/>:task?.status==="completed"?<CheckCircle2 size={18} className="text-emerald-300"/>:null}</div><h3 className="mt-3 text-sm font-black" style={{color:dept.color}}>{dept.name}</h3><p className="mt-1 text-[10px] leading-5 text-slate-400">{dept.role}</p><p className="mt-3 text-xs font-bold text-slate-200">{task?LABELS[task.status]:"Chưa có nhiệm vụ"}</p>{outputSummary(task)&&<p className="mt-2 text-[11px] leading-5 text-slate-300">{outputSummary(task)}</p>}{task?.output&&<details open={focused===dept.id} className="mt-3 text-[10px] text-slate-400"><summary className="cursor-pointer">Xem đầu ra bàn giao</summary><pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap break-all rounded-lg bg-black/25 p-2">{JSON.stringify(task.output,null,2)}</pre></details>}</article>;})}</div>
      {current?.handoffs.length>0&&<ol className="mt-4 flex flex-wrap gap-2 text-[10px] text-slate-400">{current.handoffs.map((item,index)=><li key={index} className="rounded-lg bg-white/5 px-3 py-2">{item.from} → {item.to}</li>)}</ol>}
      {blockers.length>0&&<div className="mt-4 rounded-xl border border-amber-200/20 bg-amber-200/5 p-3 text-xs text-amber-100"><b>Hồ sơ cần bổ sung</b><ul className="mt-2 list-inside list-disc space-y-1">{blockers.map(item=><li key={item}>{item}</li>)}</ul></div>}
      {current?.status==="awaiting_review"&&<div className="mt-4 rounded-xl border border-white/10 p-4"><label className="block text-xs text-slate-300">Nhận xét người duyệt<textarea value={note} onChange={e=>setNote(e.target.value)} maxLength={1000} rows={2} className="mt-2 block w-full rounded-lg bg-[#0d1b2a] p-3 text-xs text-white" placeholder="Nhận xét hồ sơ, hoặc yêu cầu bổ sung dữ liệu…"/></label><div className="mt-3 flex flex-wrap gap-2"><button onClick={()=>review("approve")} disabled={busy||note.trim().length<3||blockers.length>0} className="rounded-lg bg-emerald-200 px-3 py-2 text-xs font-bold text-emerald-950 disabled:opacity-35">Duyệt hồ sơ kiểm tra</button><button onClick={()=>review("request_changes")} disabled={busy||note.trim().length<3} className="rounded-lg border border-amber-200/30 px-3 py-2 text-xs text-amber-100 disabled:opacity-35">Yêu cầu bổ sung</button></div></div>}
      {current?.review&&<p className="mt-4 text-xs leading-5 text-emerald-100">Nhận xét đã lưu: {current.review.note}</p>}
      <div className="mt-4 flex flex-wrap items-center justify-between gap-3"><p className="max-w-3xl text-[10px] leading-5 text-slate-500">Các bước được điều phối theo quy trình có giới hạn. Chỉ bước xử lý sự cố gọi cơ chế AI/công cụ hiện có. Duyệt hồ sơ là xác nhận lượt kiểm tra dữ liệu lab, không phải chứng nhận tuân thủ toàn bộ ISO.</p>{current&&<button onClick={download} className="flex items-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-[10px] text-cyan-200"><FileDown size={14}/>Tải hồ sơ JSON</button>}</div>
      {(error||syncError||current?.error)&&<p role="alert" className="mt-3 text-xs text-rose-200">{error||syncError||current.error}</p>}
    </div>
  </section>;
}
