import { useEffect, useState } from 'react';

export default function CompanyInventory({assessment,request,onOpenDossier}) {
  const [data,setData]=useState(null),[selected,setSelected]=useState(''),[action,setAction]=useState('training_missing');
  const [error,setError]=useState(''),[busy,setBusy]=useState(false);
  const path=`/api/assessments/${assessment.assessment_id}/enterprise/company`;
  useEffect(()=>{let active=true,loading=false;async function load(){if(loading)return;loading=true;try{const result=await request(path);if(active){setData(result);setError('');}}catch(e){if(active)setError(e.message);}finally{loading=false;}}load();const timer=setInterval(load,5000);return()=>{active=false;clearInterval(timer);};},[path,request]);
  const person=data?.people.find(p=>p.id===selected);
  async function record(){setBusy(true);setError('');try{await request(path+'/events',{method:'POST',body:JSON.stringify({employee_id:selected,action})});setData(await request(path));}catch(e){setError(e.message);}finally{setBusy(false);}}
  return <main className="min-h-screen bg-[#101d2b] px-5 pb-12 pt-24 text-slate-100"><section className="mx-auto max-w-6xl space-y-5">
    <h1 className="text-3xl font-bold">Doanh nghiệp dùng chung</h1><p>Nhân viên, tài khoản và thiết bị của đợt đánh giá hiện tại · Dữ liệu giả lập.</p>
    {error&&<p role="alert">{error}</p>}{!data&&!error&&<p>Đang đọc doanh nghiệp...</p>}
    {data&&<><div className="flex flex-wrap gap-4">{[['Nhân viên',data.people.length],['Tài khoản',data.accounts.length],['Thiết bị',data.devices.length]].map(([label,n])=><div key={label} className="rounded-xl bg-slate-800 p-5">{label}: <strong>{n}</strong></div>)}<button onClick={onOpenDossier} className="rounded-xl bg-teal-700 p-4">Mở hồ sơ ISO</button></div>
    <p className="break-all text-xs text-slate-400">Ngày đánh giá: {data.assessment_date} · Snapshot: {data.snapshot_hash}</p>
    <div className="overflow-auto"><table className="w-full text-left text-sm"><thead><tr>{['Nhân viên','Phòng ban','Tình trạng','Tài khoản','Thiết bị'].map(x=><th key={x} className="p-3">{x}</th>)}</tr></thead><tbody>{data.people.map(p=><tr key={p.id} className="border-t border-slate-700"><td className="p-3"><button className="text-teal-300 underline" onClick={()=>setSelected(p.id)}>{p.id} · {p.name}</button></td><td>{p.department}</td><td>{p.status}</td><td>{data.accounts.filter(a=>a.person_id===p.id).length}</td><td>{data.devices.filter(d=>d.person_id===p.id).length}</td></tr>)}</tbody></table></div>
    {person&&<article className="space-y-4 rounded-xl bg-slate-800 p-5"><h2 className="text-xl font-bold">{person.id} · {person.name}</h2><p>Mã cũ: {person.legacy_id} · Vai trò: {person.role}</p><label className="block">Ghi nhận sự kiện nghiệp vụ <select value={action} onChange={e=>setAction(e.target.value)} className="m-2 rounded bg-slate-700 p-2">{data.actions.map(a=><option key={a.id} value={a.id}>{a.name}</option>)}</select></label><button disabled={busy} onClick={record} className="rounded bg-teal-700 px-4 py-2">{busy?'Đang lưu…':'Ghi nhận vào doanh nghiệp'}</button><p>Thay đổi được lưu cho mọi màn hình. Ngày mô phỏng và ngoại lệ bàn giao ảnh hưởng kết quả đánh giá; dữ liệu chưa biết giữ nguyên là chưa biết.</p>
    <h3>Hồ sơ nhân viên</h3><pre className="overflow-auto whitespace-pre-wrap text-xs">{JSON.stringify(person,null,2)}</pre><h3>Tài khoản</h3><pre className="overflow-auto whitespace-pre-wrap text-xs">{JSON.stringify(data.accounts.filter(a=>a.person_id===person.id),null,2)}</pre><h3>Thiết bị</h3><pre className="overflow-auto whitespace-pre-wrap text-xs">{JSON.stringify(data.devices.filter(d=>d.person_id===person.id),null,2)}</pre></article>}</>}
  </section></main>;
}
