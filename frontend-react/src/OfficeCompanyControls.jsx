import { useRef, useState } from "react";

export default function OfficeCompanyControls({ base, request, workspace, onWorkspace, onEntries }) {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const pending = useRef(null);
  const inFlight = useRef(false);
  const working = workspace.filter(({state:s})=>s.shift==="on" && s.location==="desk" && s.screen_state==="unlocked" && s.device_status!=="locked" && !s.network_isolated).length;
  async function send(action) {
    if(inFlight.current) return;
    if(pending.current?.action!==action) pending.current={action,request_id:crypto.randomUUID()};
    inFlight.current=true; setBusy(true); setError(""); setResult(null);
    try {
      const data=await request(`${base}/office-commands`,{method:"POST",body:JSON.stringify(pending.current)});
      onWorkspace(data.workspace); onEntries(data.entries); setResult(data.results); pending.current=null;
    } catch(err) {setError(err.message);}
    finally {inFlight.current=false; setBusy(false);}
  }
  const skipped=result?.filter(item=>!item.ok) || [];
  return <section className="mb-3 rounded-2xl border border-emerald-200/30 bg-[#203c38] p-4 text-emerald-50" aria-label="Điều khiển toàn công ty">
    <div className="flex flex-wrap items-center justify-between gap-2"><h2 className="text-sm font-black">TOÀN CÔNG TY · {workspace.length} máy riêng</h2><span className="text-xs">{working}/{workspace.length} đang làm · {workspace.filter(x=>x.state.location==="break").length} đang nghỉ · {workspace.filter(x=>x.state.shift==="off").length} ngoài ca</span></div>
    <p className="mt-1 text-xs text-emerald-100/70">Ra lệnh cho tất cả nhân viên. Chọn một người trên bản đồ để điều khiển riêng.</p>
    <div className="mt-3 flex flex-wrap gap-2">{[["start_shift","Vào ca & làm việc tất cả"],["work","Tất cả về bàn"],["break","Tất cả nghỉ"],["end_shift","Tất cả tan ca"]].map(([action,label])=><button key={action} onClick={()=>send(action)} disabled={busy||!workspace.length} className="rounded-xl bg-emerald-100 px-3 py-2 text-xs font-bold text-emerald-950 hover:bg-white disabled:opacity-40">{label}</button>)}</div>
    <div role="status" className="mt-2 text-xs">{busy?"Đang gửi lệnh đến từng nhân viên…":result?`Đã thực hiện: ${result.length-skipped.length}/${result.length} nhân viên. Số người đang làm được cập nhật theo trạng thái máy thực tế.`:"Máy bị khóa hoặc cô lập vẫn giữ biện pháp bảo vệ của Agent."}</div>
    {skipped.length>0&&<details className="mt-2 text-xs text-amber-100"><summary className="cursor-pointer">{skipped.length} người chưa thực hiện được — xem lý do</summary><ul className="mt-2 space-y-1">{skipped.map(item=><li key={item.employee_id}>{item.employee_id}: {item.reason}</li>)}</ul></details>}
    {error&&<p role="alert" className="mt-2 text-xs text-rose-200">{error}</p>}
  </section>;
}
