import { useEffect, useRef, useState } from "react";
import { MessageSquare, Send, Radio, Loader2, CheckCircle2 } from "lucide-react";
import { commandPhase, commandRecipient } from "./officeLive";

export default function EmployeeCommandConsole({ base, request, employees, monitoring, onActivity, onInspect, disabled, selectedEmployee: actorId, onSelect, onEntries, onWorkspace, suggestedCommand, autoPrepare=false }) {
  const [catalog, setCatalog] = useState({actors:[],commands:[]});
  const [workspace, setWorkspace] = useState([]);
  const [text, setText] = useState("");
  const [entries, setEntries] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [syncError, setSyncError] = useState("");
  const pending = useRef(null);
  const inFlight = useRef(false);
  const recipient = commandRecipient(text, actorId);
  const actor = employees.find(item => item.employee_id === recipient);
  const machine = workspace.find(item=>item.employee_id===recipient);
  const commands = (machine?.actions || []).map(command=>autoPrepare&&command.prepared_enabled!==undefined?
    {...command,enabled:command.prepared_enabled,reason:command.prepared_reason}:command);

  useEffect(()=>{if(suggestedCommand) setText(suggestedCommand.text);},[suggestedCommand]);

  useEffect(() => {
    let cancelled = false;
    request(`${base}/employee-commands/catalog`).then(data => {if(!cancelled) setCatalog(data);})
      .catch(err => {if(!cancelled) setSyncError(err.message);});
    return () => {cancelled=true;};
  },[base,request]);

  useEffect(() => {
    let cancelled = false;
    let timer;
    async function refresh() {
      try {
        const [data,machines] = await Promise.all([request(`${base}/employee-commands`),request(`${base}/office-state`)]);
        if (!cancelled) { setEntries(data); onEntries(data); setWorkspace(machines); onWorkspace(machines); setSyncError(""); }
      } catch (err) { if (!cancelled) setSyncError(err.message); }
      finally { if (!cancelled) timer = setTimeout(refresh, 2500); }
    }
    refresh();
    return () => { cancelled = true; clearTimeout(timer); };
  }, [base, request, onEntries, onWorkspace]);

  async function send(event) {
    event.preventDefault();
    if (!text.trim() || inFlight.current || disabled) return;
    const payload = { employee_id: recipient, text: text.trim(), prepare_workstation:autoPrepare };
    const key = JSON.stringify(payload);
    if (pending.current?.key !== key) pending.current = { key, request_id: crypto.randomUUID() };
    inFlight.current = true; setBusy(true); setError("");
    try {
      const receipt = await request(`${base}/employee-commands`, {
        method: "POST", body: JSON.stringify({ ...payload, request_id: pending.current.request_id }),
      });
      setEntries(current => [receipt, ...current.filter(item => item.event_id !== receipt.event_id)].slice(0, 30));
      setText(""); pending.current = null;
      onSelect(receipt.employee_id);
      onActivity(receipt);
      const machines=await request(`${base}/office-state`);
      setWorkspace(machines); onWorkspace(machines);
    } catch (err) { setError(err.message); }
    finally { inFlight.current = false; setBusy(false); }
  }

  return <section className="flex min-h-[540px] flex-col overflow-hidden rounded-[28px] border border-cyan-200/20 bg-[#142334] shadow-xl" aria-label="Bình luận điều khiển nhân viên">
    <div className="border-b border-white/10 bg-gradient-to-br from-cyan-300/10 via-transparent to-violet-400/10 p-5">
      <div className="flex items-center justify-between gap-2 text-[10px] font-bold uppercase tracking-widest text-cyan-200"><span className="flex items-center gap-2"><Radio size={14}/> Phòng diễn tập trực tiếp</span><span className="rounded-full border border-white/10 px-2 py-1 text-slate-400">Giả lập</span></div>
      <h2 className="mt-3 text-xl font-black text-white">Bình luận → nhân vật của bạn</h2>
      <p className="mt-2 text-xs leading-5 text-slate-400">Gõ “đi làm” để người đang chọn tham gia ca. Mỗi người nhận lệnh riêng, có trạng thái và dấu vết riêng.</p>
      <label htmlFor="command-employee" className="mt-4 block text-[10px] font-bold uppercase tracking-wider text-cyan-200">Nhân viên nhận lệnh</label>
      <select id="command-employee" value={actorId} disabled={busy} onChange={event=>{onSelect(event.target.value);setText("");setError("");}} className="mt-2 w-full rounded-xl border border-white/15 bg-[#142334] p-3 text-xs text-white">{employees.filter(person=>catalog.actors.some(item=>item.employee_id===person.employee_id)).map(person=><option key={person.employee_id} value={person.employee_id}>{person.display_name} · {person.employee_id}</option>)}</select>
      <p className="mt-2 text-[10px] text-slate-400">Hoặc gõ <code>@EMP-025 /cai-app-la</code> để chỉ định người nhận.</p>
      {autoPrepare&&<p className="mt-2 text-[10px] leading-5 text-emerald-200/70">Lệnh USB/app/rời máy sẽ tự vào ca hoặc về bàn nếu cần. Không tự mở máy đang bị cô lập, thu hồi hoặc chờ xử lý.</p>}
      {machine && <div className="mt-3 rounded-xl border border-white/10 bg-black/15 p-3 text-[10px] leading-5 text-slate-300"><b className="block font-mono text-cyan-200">{machine.asset_id}</b><div>{machine.state.shift==="on"?"Trong ca":"Ngoài ca"} · {machine.state.location==="desk"?"Tại bàn":machine.state.location==="break"?"Đang nghỉ":"Lễ tân"} · Màn hình {machine.state.screen_state==="locked"?"đã khóa":"đang mở"}</div><div>USB: {machine.state.usb_connected?machine.state.media_status:"chưa kết nối"} · App: {machine.state.software_status}</div><div>{machine.state.network_isolated?"Máy đang bị cô lập · ":""}{machine.pending_count} sự kiện chưa xử lý</div></div>}
    </div>
    <div className="flex items-center gap-2 border-b border-white/5 px-5 py-3 text-[10px] text-slate-300"><span className={`h-2 w-2 rounded-full ${monitoring.active ? "bg-emerald-300" : "bg-slate-500"}`}/>{monitoring.active ? "Agent đang giám sát" : "Gửi lệnh sẽ bật giám sát tự động"}</div>
    <div className="max-h-72 min-h-28 flex-1 space-y-3 overflow-y-auto p-4" aria-live="polite">
      {!entries.length && <div className="py-3 text-center text-xs leading-6 text-slate-500"><MessageSquare className="mx-auto mb-2 text-cyan-200/50" size={23}/>Bắt đầu bằng “làm việc” hoặc chọn một lệnh bên dưới.<br/>Lệnh chưa hiểu sẽ không tạo hành động.</div>}
      {entries.map(item => <article key={item.event_id} className="rounded-2xl border border-white/5 bg-[#0c1726]/65 p-3">
        <div className="flex justify-between gap-2 text-[10px]"><b className="text-cyan-200">{item.employee_name}</b><time className="text-slate-500">{new Date(item.observed_at).toLocaleTimeString("vi-VN")}</time></div>
        <p className="mt-2 break-words text-sm text-white">{item.text}</p>
        <p className="mt-1 text-[10px] leading-4 text-slate-400">{item.summary}</p>
        {item.incident_id ? <button type="button" onClick={() => onInspect(item)} className="mt-2 flex items-center gap-1 text-[10px] font-bold text-amber-200"><CheckCircle2 size={12}/>{item.detected_control} · {item.verified ? "Đã xử lý và xác minh" : "Cần rà soát"} →</button> : <p className="mt-2 text-[10px] text-slate-500">{commandPhase(item) === "routine" ? "Đã ghi hoạt động bình thường · chưa có cảnh báo liên kết" : "Đã ghi nhật ký · chờ Agent phát hiện"}</p>}
        {item.model && <p className="mt-1 text-[9px] text-slate-500">Nguồn quyết định xử lý: {item.model}</p>}
      </article>)}
    </div>
    <form onSubmit={send} className="border-t border-white/10 bg-[#101d2c] p-4">
      <div className="mb-3 grid grid-cols-2 gap-2">{commands.map(command=><button key={command.command} type="button" disabled={busy || !command.enabled} title={command.reason || command.command} onClick={() => {onSelect(recipient);setText(command.command);}} className={`rounded-xl border px-3 py-2 text-left text-[10px] font-bold disabled:opacity-35 ${command.risk ? "border-amber-200/20 bg-amber-300/5 text-amber-200" : "border-emerald-200/20 bg-emerald-300/5 text-emerald-200"}`}>{command.label}</button>)}</div>
      <label htmlFor="employee-command" className="mb-2 block text-[10px] text-slate-400">Gửi tới {actor?.display_name || recipient} · Enter để gửi</label>
      <div className="flex gap-2"><input id="employee-command" value={text} onChange={event => setText(event.target.value)} maxLength={240} disabled={busy || disabled} placeholder="Gõ: vào ca, làm việc, nghỉ…" className="min-w-0 flex-1 rounded-xl border border-white/10 bg-black/20 px-3 py-3 text-sm text-white outline-none focus:border-cyan-200/60"/><button type="submit" aria-label="Gửi lệnh nhân viên" disabled={busy || disabled || !text.trim() || !catalog.actors.length} className="rounded-xl bg-cyan-200 px-4 text-[#142334] hover:bg-cyan-100 disabled:opacity-40">{busy ? <Loader2 size={17} className="animate-spin"/> : <Send size={17}/>}</button></div>
      {(error || syncError) && <p role="alert" className="mt-2 text-xs text-rose-300">{error || `Chưa đồng bộ lịch sử: ${syncError}`}</p>}
      {monitoring.last_error && <p role="alert" className="mt-2 text-xs text-amber-200">Bộ giám sát gặp lỗi; hãy bật lại giám sát để thử tiếp.</p>}
      <p className="mt-2 text-[9px] leading-4 text-slate-500">Lệnh giới hạn trong lab. Điều khoản chỉ xuất hiện khi bộ giám sát đã kiểm tra dấu vết.</p>
    </form>
  </section>;
}
