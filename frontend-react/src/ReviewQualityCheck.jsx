import {useState} from 'react';
export default function ReviewQualityCheck({request,url,controlId,rationale,acknowledged,onAcknowledge}) {
 const [result,setResult]=useState(null);
 const key=JSON.stringify([controlId,rationale]);
 const check=result?.key===key?result.check:null,error=result?.key===key?result.error:'';
 async function inspect(){try{const value=await request(url,{method:'POST',body:JSON.stringify({control_id:controlId,rationale})});setResult({key,check:value,error:''});}catch(e){setResult({key,check:null,error:e.message});}}
 return <section className="space-y-2 rounded border border-slate-600 p-3"><button type="button" className="rounded bg-slate-700 p-2" disabled={rationale.trim().length<10} onClick={inspect}>Kiểm tra căn cứ trước khi nộp</button>
  <p>Phát hiện ký tự thử, trùng nguyên văn hoặc viện dẫn nguồn control khác. Không chọn kết luận thay bạn.</p>{error&&<p role="alert">{error}</p>}
  {check&&<><p>{check.note}</p>{check.issues.length?<ul>{check.issues.map(i=><li className="text-amber-200" key={i.code}>{i.message}</li>)}</ul>:<p>Chưa phát hiện dấu hiệu hình thức bất thường; vẫn cần tự đối chiếu nguồn.</p>}
   {!!check.issues.length&&!check.blocked&&<label className="block"><input type="checkbox" checked={acknowledged} onChange={e=>onAcknowledge(e.target.checked)}/> Tôi đã đọc lại nguồn và xác nhận căn cứ này có chủ đích, không dán nhầm.</label>}
  </>}
 </section>;
}
