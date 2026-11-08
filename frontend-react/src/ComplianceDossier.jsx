import { useEffect, useRef, useState } from 'react';
export default function ComplianceDossier({ assessment, request, onOpenDashboard, onOpenCompany }) {
  const [report, setReport] = useState(null), [error, setError] = useState(''), [selected, setSelected] = useState('');
  const [job, setJob] = useState(null), [busy, setBusy] = useState(false);
  const base = `/api/assessments/${assessment.assessment_id}/enterprise/shared-work`;
  const path = base;
  const queue = useRef({active:false, seen:new Set()});
  const [auto, setAuto] = useState(false), [notice,setNotice] = useState('');
  const labels = {not_started:'Chưa kiểm tra',running:'Đang xử lý',stale:'Cần đánh giá lại',failed:'Lỗi lần trước',awaiting_review:'Chờ người duyệt',waiting_evidence:'Chờ bằng chứng',evaluated:'Đã kiểm tra'};
  useEffect(()=>()=>{queue.current.active=false;},[path]);
  useEffect(() => { let active = true; request(path).then(r => { if (active) setReport(r); }).catch(e => { if (active) setError(e.message); }); return () => { active = false; }; }, [path, request]);
  useEffect(() => { if (!job) return; let checking=false; const timer = setInterval(async () => {
    if(checking)return;checking=true;
    try { const state = await request(`/api/jobs/${job.job_id}`); if (state.status !== 'RUNNING') {
      setJob(null); setBusy(false); const latest=await request(path); setReport(latest);
      if (state.status !== 'SUCCEEDED') { queue.current.active=false; setAuto(false); setError(state.error_message || 'Đánh giá không hoàn tất'); }
      else if(queue.current.active) {
        if(latest.next_control_id && !queue.current.seen.has(latest.next_control_id) && queue.current.seen.size<12) { await launch(latest.next_control_id); }
        else { queue.current.active=false; setAuto(false); setNotice('Đã kết thúc lượt tự động. Các mục chờ bằng chứng/duyệt cần người phụ trách tiếp tục.'); }
      }
    }} catch (e) { queue.current.active=false; setAuto(false); setError(e.message); setJob(null); setBusy(false); }
    finally { checking=false; }
  }, 2500); return () => clearInterval(timer); }, [job, path, request]);
  useEffect(()=>{let active=true;const timer=setInterval(()=>{request(path).then(r=>{if(active)setReport(r);}).catch(e=>{if(active)setError(e.message);});},5000);return()=>{active=false;clearInterval(timer);};},[path,request]);
  async function refresh() { try { setReport(await request(path)); setError(''); } catch(e) { setError(e.message); } }
  async function launch(cid, force=false) {
    setBusy(true); setError('');
    try {
      const result=await request(`${base}/start`,{method:'POST',body:JSON.stringify({control_id:cid,force})});
      if(result.control_id) { setSelected(result.control_id); queue.current.seen.add(result.control_id); }
      if(result.job_id) { setJob(result); setNotice(result.action==='following'?'Đang theo dõi công việc chung đã được khởi chạy.':'Agent đang thực hiện công việc chung.'); }
      else { setBusy(false); queue.current.active=false; setAuto(false); setNotice(result.action==='reused'?'Dùng kết quả đã lưu; xem kết luận và phần còn thiếu bên dưới.':result.message); }
      setReport(await request(path));
    } catch(e) {setError(e.message);setBusy(false);queue.current.active=false;setAuto(false);}
  }
  function automate() { queue.current={active:true,seen:new Set()};setAuto(true);launch(null); }
  function stopQueue() {queue.current.active=false;setAuto(false);setNotice('Đã dừng nhận việc tiếp theo; công việc đang chạy vẫn hoàn tất và lưu kết quả.');}
  function download() { const url = URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'})); const a=document.createElement('a');a.href=url;a.download=`ho-so-${assessment.assessment_id}.json`;a.click();URL.revokeObjectURL(url); }
  const detail=report?.controls.find(c=>c.control_id===selected);
  return <main className="min-h-screen bg-[#101d2b] px-5 pb-12 pt-24 text-slate-100"><section className="mx-auto max-w-6xl space-y-5">
    <h1 className="text-3xl font-bold">Hồ sơ đánh giá tuân thủ · Công việc chung</h1><p>Doanh nghiệp giả lập · Hỗ trợ người đánh giá, không phải chứng nhận ISO.</p>
    <div className="flex flex-wrap gap-3">{onOpenCompany&&<button onClick={onOpenCompany} className="rounded bg-slate-700 px-4 py-2">Xem doanh nghiệp dùng chung</button>}<button onClick={refresh} className="rounded bg-teal-700 px-4 py-2">Làm mới</button><button disabled={!report} onClick={download} className="rounded bg-slate-700 px-4 py-2">Xuất hồ sơ JSON</button></div>
    <div className="rounded-xl bg-slate-800 p-4 space-y-3"><p>Tiến độ dùng chung trong cùng đợt đánh giá. Đã kiểm tra không đồng nghĩa đã đáp ứng kiểm soát.</p><p>{report?.automation_policy}</p><p>Việc tiếp theo: {report?.next_control_id||'Không có mục tự động đang chờ'}</p><button disabled={busy||auto||!report?.next_control_id} onClick={automate} className="rounded bg-teal-700 px-4 py-2">Agent tiếp tục các việc còn lại (tối đa 12 mục)</button>{auto&&<button onClick={stopQueue} className="ml-3 rounded bg-amber-800 px-4 py-2">Dừng sau việc hiện tại</button>}<p role="status">{notice}</p><p className="text-sm">Lượt tự động tiếp tục khi trang đang mở; kết quả lưu trên server. Không tự duyệt hoặc tự sửa hồ sơ nhân viên.</p></div>
    {error&&<p role="alert">{error}</p>}{!report&&!error&&<p>Đang đọc hồ sơ...</p>}
    {report&&<>{report.company_summary&&<p>Nguồn chung: {report.company_summary.employees} nhân viên · {report.company_summary.accounts} tài khoản · {report.company_summary.devices} thiết bị</p>}<div className="flex flex-wrap gap-3">{Object.entries(report.summary).map(([k,v])=><div key={k} className="rounded-xl bg-slate-800 p-4">{k}: <strong>{v}</strong></div>)}</div><p>Collector lab: {report.supported_collectors.join(', ')}. Chưa hỗ trợ thu thập không có nghĩa là không áp dụng.</p>
    <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr>{['Kiểm soát','Nguồn lab','Kết luận','Quy trình','Bằng chứng'].map(x=><th key={x} className="p-3">{x}</th>)}</tr></thead><tbody>{report.controls.map(c=><tr key={c.control_id} className="border-t border-slate-700"><td className="p-3"><button disabled={busy} onClick={()=>setSelected(c.control_id)} className="text-teal-300 underline">{c.control_id} · {c.name}</button></td><td>{c.source||'Chưa có collector'}</td><td>{c.conclusion}</td><td>{labels[c.shared_state]||c.workflow_status}<br/>{c.assigned_to&&`Phụ trách: ${c.assigned_to}`}<br/>{c.updated_at}</td><td>{c.evidence.length}</td></tr>)}</tbody></table></div>
    {detail&&<article className="space-y-3 rounded-xl bg-slate-800 p-5"><h2 className="text-xl font-bold">{detail.control_id} · {detail.name}</h2><p>{detail.objective}</p><p>Kết luận: {detail.conclusion} · Công việc: {labels[detail.shared_state]||detail.workflow_status}</p><p>Đánh giá gần nhất: {detail.latest_evaluation_id||'Chưa có'} · Cập nhật: {detail.updated_at}</p><button disabled={busy} onClick={()=>launch(selected)} className="rounded bg-teal-700 px-4 py-2">{busy?'Agent đang đánh giá…':'Tiếp tục / xem kết quả chung'}</button><button disabled={busy} onClick={()=>launch(selected,true)} className="ml-3 rounded bg-slate-700 px-4 py-2">Chủ động đánh giá lại</button><p>Thu thập → kiểm tra → lưu kết luận. Khắc phục dữ liệu và duyệt tại Dashboard theo quyền hiện có.</p>
    {onOpenDashboard&&<button onClick={onOpenDashboard} className="rounded bg-slate-700 px-4 py-2">Mở Dashboard để bổ sung bằng chứng / duyệt</button>}<h3>Tiêu chí lab — chính sách dự án</h3><pre className="overflow-auto whitespace-pre-wrap text-xs">{JSON.stringify(detail.criteria,null,2)}</pre><h3>Căn cứ và lịch sử đánh giá</h3>{detail.evaluation_history.map(e=><details key={e.evaluation_id}><summary>#{e.evaluation_id} · {e.status} · {e.created_at}</summary><p>{e.rationale}</p><p>Người thực hiện: {e.performed_by}</p><pre className="overflow-auto whitespace-pre-wrap text-xs">{JSON.stringify({evidence_ids:e.evidence_ids,audit_trail:e.audit_trail},null,2)}</pre></details>)}<h3>Bằng chứng của đợt đánh giá</h3>{!detail.evidence.length&&<p>Chưa có bằng chứng gắn với kiểm soát trong đợt này.</p>}{detail.evidence.map(e=><details key={e.evidence_id}><summary>{e.evidence_id} · {e.is_synthetic ? "LAB" : "TẢI LÊN / NHẬP"} · revision {e.revision ?? "—"} · {e.created_at}</summary><pre className="overflow-auto whitespace-pre-wrap text-xs">{JSON.stringify(e,null,2)}</pre></details>)}</article>}
    <aside className="rounded-xl border border-amber-500/40 p-4"><h2 className="font-bold">Phạm vi và giới hạn</h2>{report.limitations.map(x=><p key={x}>{x}</p>)}<p className="break-all text-xs">SHA-256 hồ sơ: {report.sha256}</p></aside></>}
  </section></main>;
}
