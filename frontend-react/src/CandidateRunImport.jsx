import {useState} from 'react';
export default function CandidateRunImport({request,url,mode,onCreated}) {
 const [file,setFile]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 async function start(){setBusy(true);setError('');try{if(file.size>10*1024*1024)throw new Error('Gói vượt 10 MB.');const plan=JSON.parse(await file.text());const r=await request(url,{method:'POST',body:JSON.stringify({plan,mode})});onCreated(r);}catch(e){setError(e.message);}finally{setBusy(false);}}
 return <details className="rounded border border-slate-600 p-4"><summary>Nhập gói nguồn ứng viên đã chốt · admin</summary><p>Chọn JSON từ CLI a8_protocol prepare --raw-root. Kiểm tra hash, rubric/recipe và dấu trùng fixture trước khi chạy trên snapshot; không thu lại nguồn. Chưa xác nhận độc lập/chuyên môn, không gán đáp án thiết kế. Hai người chấm dùng cùng mã lượt mới.</p><input aria-label="Gói ứng viên JSON đã chốt" type="file" accept=".json" onChange={e=>setFile(e.target.files?.[0]||null)}/><button className="rounded bg-teal-800 p-2" disabled={!file||busy} onClick={start}>{busy?'Đang nhập':'Nhập và chạy gói ứng viên'}</button>{error&&<p role="alert">{error}</p>}</details>;
}
