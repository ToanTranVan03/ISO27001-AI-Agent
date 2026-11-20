import {useState} from 'react';

const states={needs_evidence:'Cần bổ sung bằng chứng',needs_new_review:'Cần lượt chấm mới',discussion_recorded:'Đã ghi nội dung thảo luận'};
export default function ReviewFollowups({doc,canManage,onSave,download}){
 const [cid,setCid]=useState(''),[state,setState]=useState('needs_new_review'),[note,setNote]=useState('');
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');
 const history=doc.review_followups||[];
 async function submit(e){e.preventDefault();setBusy(true);setError('');setNotice('');try{
  await onSave({control_id:cid,report_sha256:doc.report.sha256,state,note:note.trim()});
  setNote('');setNotice('Đã lưu biên bản riêng; nhãn khóa, số liệu đối chiếu và phê duyệt không thay đổi.');
 }catch(e){setError(e.message);}finally{setBusy(false);}}
 return <section className="space-y-3 rounded-xl border border-slate-600 p-4">
  <h3 className="font-semibold">Sổ xử lý bất đồng & căn cứ cần rà</h3>
  <p className="text-xs text-slate-400">Gắn đúng lượt và hash nguồn. Ghi chú điều phối không thay kết luận người chấm, không xóa lỗi chất lượng, không làm tăng độ đúng hoặc duyệt SoA. Nhãn đã khóa được giữ nguyên.</p>
  {canManage&&<form onSubmit={submit} className="space-y-3"><fieldset disabled={busy} className="space-y-3">
   <label className="block text-sm">Control cần xử lý<select aria-label="Control cần xử lý bất đồng" required value={cid} onChange={e=>setCid(e.target.value)} className="mt-1 block bg-slate-800 p-2"><option value="">Chọn control</option>{doc.report.records.map(r=><option key={r.control_id}>{r.control_id}</option>)}</select></label>
   <label className="block text-sm">Hướng xử lý<select aria-label="Hướng xử lý bất đồng" value={state} onChange={e=>setState(e.target.value)} className="mt-1 block bg-slate-800 p-2">{Object.entries(states).map(([id,label])=><option key={id} value={id}>{label}</option>)}</select></label>
   <label className="block text-sm">Nội dung đối soát<textarea aria-label="Nội dung đối soát bất đồng" required minLength={30} maxLength={3000} value={note} onChange={e=>setNote(e.target.value)} placeholder="Ghi căn cứ đã đối chiếu, phần chưa rõ và việc tiếp theo; không nhập đáp án thay người chấm." className="mt-1 block w-full bg-slate-800 p-3"/></label>
   <button disabled={!cid||note.trim().length<30} className="rounded bg-teal-800 p-3">{busy?'Đang lưu…':'Lưu biên bản xử lý riêng'}</button>
  </fieldset></form>}
  {error&&<p role="alert">{error}</p>}{notice&&<p role="status">{notice}</p>}
  <button onClick={()=>download({run_id:doc.run_id,report_sha256:doc.report.sha256,meaning:'COORDINATION_ONLY',history},`xu-ly-bat-dong-${doc.run_id}.json`)} className="rounded border border-slate-600 p-2 text-sm">Xuất sổ xử lý · {history.length} bản ghi</button>
  <ol className="max-h-80 space-y-3 overflow-auto">{history.map(item=><li key={item.followup_id} className="rounded bg-slate-800 p-3 text-sm"><strong>{item.control_id} · {states[item.state]||item.state}</strong><p className="whitespace-pre-wrap break-words">{item.note}</p><p className="mt-2 break-all text-xs text-slate-400">Người ghi: {item.recorded_by} · {item.recorded_at} · Hash nguồn: {item.evidence_sha256}</p></li>)}</ol>
 </section>;
}
