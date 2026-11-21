import {useState} from 'react';

const fields=['control_id','applicable','reason','treatment','treatment_owner','treatment_due','verification_plan'];
export default function DecisionBatchPanel({scope,request,url,onSaved,exportFile}){
 const [file,setFile]=useState(null),[note,setNote]=useState(''),[checked,setChecked]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[result,setResult]=useState(null);
 const stale=checked&&checked.body.expected_fingerprint!==scope.soa.fingerprint;
 function template(){
  const decisions=scope.controls.map(c=>Object.fromEntries(fields.map(k=>[k,k==='control_id'?c.control_id:c.applicability?.[k]??(k==='reason'||k==='treatment'?'':null)])));
  exportFile({assessment_id:scope.assessment_id,expected_fingerprint:scope.soa.fingerprint,decisions},'mau-quyet-dinh-ke-hoach-56.json');
 }
 async function inspect(){setBusy(true);setError('');setResult(null);setChecked(null);try{
  if(file.size>1024*1024)throw Error('Gói quyết định quá 1MB.');
  const body={...JSON.parse(await file.text()),note:note.trim()};
  const preview=await request(url+'/validate',{method:'POST',body:JSON.stringify(body)});setChecked({body,preview});
 }catch(e){setError(e.message);}finally{setBusy(false);}}
 async function apply(){if(!checked||stale)return;setBusy(true);setError('');try{
  const saved=await request(url,{method:'POST',body:JSON.stringify(checked.body)});setResult(saved);setChecked(null);await onSaved();
 }catch(e){setError(e.message);}finally{setBusy(false);}}
 return <details className="space-y-4 rounded-2xl border border-teal-800 bg-teal-950/20 p-5"><summary className="font-semibold">Nhập tính áp dụng & kế hoạch theo lô · người phụ trách</summary>
  <p className="text-sm text-slate-300">Xuất mẫu hiện hành, điền quyết định thực tế rồi kiểm tra trước khi lưu. Giữ tối đa 56 dòng; xóa các dòng chưa quyết định. Mẫu để trống tính áp dụng và thông tin chưa có; không tự chọn loại trừ, người nhận hoặc hạn.</p>
  <button onClick={template} disabled={busy} className="rounded border border-slate-600 p-2 text-sm">Xuất mẫu quyết định 56 control</button>
  <p className="text-xs text-slate-400">Trong JSON: applicable = true/false; reason = căn cứ áp dụng/loại trừ; treatment = kế hoạch; treatment_owner = người nhận; treatment_due = YYYY-MM-DD; verification_plan = cách kiểm tra lại. Có thể để null ở ba trường theo dõi khi lưu nháp; hồ sơ chưa đủ sẽ tiếp tục bị chặn duyệt.</p>
  <label className="block text-sm">Gói quyết định do người phụ trách cung cấp<input aria-label="Gói quyết định và kế hoạch JSON" type="file" accept=".json" disabled={busy} className="mt-2 block w-full" onChange={e=>{setFile(e.target.files?.[0]||null);setChecked(null);setResult(null);setError('');}}/></label>
  <label className="block text-sm">Căn cứ nhập gói / xuất xứ quyết định<textarea aria-label="Căn cứ nhập gói quyết định" minLength={20} maxLength={2000} value={note} disabled={busy} className="mt-2 block w-full bg-slate-800 p-3" onChange={e=>{setNote(e.target.value);setChecked(null);}} placeholder="Người phụ trách ghi nguồn quyết định và phạm vi đã rà, tối thiểu 20 ký tự"/></label>
  <button disabled={!file||busy||note.trim().length<20} onClick={inspect} className="rounded bg-slate-700 p-3 text-sm">Xem trước gói quyết định, chưa lưu</button>
  {error&&<p role="alert" className="text-sm text-rose-200">{error}</p>}
  {checked&&<section aria-label="Xem trước quyết định theo lô" className="space-y-3 rounded-xl border border-slate-700 p-4"><p>{checked.preview.changed_count} quyết định sẽ thay đổi · {checked.preview.projected_ready_controls}/56 hồ sơ dự kiến đủ điều kiện nội dung. Đây không phải số control tuân thủ hoặc phê duyệt.</p>
   <p className="break-all text-xs text-slate-400">Phiên bản đã đọc: {checked.preview.based_on_fingerprint}</p>
   <div className="max-h-96 space-y-2 overflow-auto">{checked.preview.changes.map(c=><details key={c.control_id} className="rounded border border-slate-700 p-3 text-xs"><summary>{c.control_id} · {c.name} · {({create:'Ghi mới',update:'Thay đổi',unchanged:'Giữ nguyên'})[c.action]} · {c.after.applicable?'Áp dụng':'Đề xuất loại trừ'}</summary><p className="mt-2">Căn cứ cũ: {c.before?.reason||'Chưa ghi'}</p><p>Căn cứ mới: {c.after.reason}</p><p>Kế hoạch: {c.after.treatment}</p><p>Người nhận: {c.after.treatment_owner||'Chưa ghi'} · Hạn: {c.after.treatment_due||'Chưa ghi'}</p><p>Kiểm tra lại: {c.after.verification_plan||'Chưa ghi'}</p><p className="mt-2 text-amber-200">Còn chặn: {c.remaining_blockers.join('; ')||'Cần kiểm tra cả rubric và hồ sơ toàn phạm vi trước khi duyệt'}</p></details>)}</div>
   {stale&&<p role="alert" className="text-sm text-amber-200">Hồ sơ đã đổi sau khi xem trước. Xuất lại mẫu và kiểm tra trên phiên bản hiện hành.</p>}
   <button disabled={busy||stale||!checked.preview.changed_count} onClick={apply} className="rounded bg-teal-700 p-3 text-sm">Lưu {checked.preview.changed_count} quyết định/kế hoạch đã xem trước</button>
   <p className="text-xs text-slate-400">Lưu dưới tài khoản đang đăng nhập, cùng mã lô và căn cứ nhập; giữ lịch sử cũ. Không tạo thẩm định hoặc phê duyệt SoA.</p>
  </section>}
  {result&&<p role="status" className="text-sm text-teal-200">Đã lưu {result.applied} quyết định/kế hoạch. {result.note}</p>}
 </details>;
}
