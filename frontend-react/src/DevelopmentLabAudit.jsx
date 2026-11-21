import {useEffect,useState} from 'react';
import {conclusionLabels} from './assessmentLabels';

const labels={met:'Đạt tiêu chí',not_met:'Không đạt',unknown:'Chưa rõ'};
export default function DevelopmentLabAudit({request,url,onSelect,download}){
 const [data,setData]=useState(null),[error,setError]=useState(''),[onlyDifferences,setOnlyDifferences]=useState(true);
 useEffect(()=>{let active=true;request(url).then(r=>{if(active)setData(r);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[request,url]);
 return <section className="space-y-3 rounded-xl border border-slate-600 p-4"><h3 className="font-semibold">Rà sai khác theo từng tiêu chí lab</h3>
  {error&&<p role="alert">{error}</p>}{data&&<><p className="text-sm">{data.controls_with_status_difference} control lệch kết luận · {data.controls_with_criterion_difference} control lệch ít nhất một tiêu chí · {data.differing_criteria} tiêu chí khác khóa thiết kế.</p><p className="text-xs text-slate-400">{data.note}</p>
  {data.key_binding!=='FROZEN_BEFORE_RUN'&&<p className="text-xs text-amber-200">Lượt cũ chưa lưu hash khóa tiêu chí trước khi chạy. Phân tích này dùng khóa hiện hành; không coi là đáp án đã chốt trước dự đoán.</p>}
  <div className="flex flex-wrap gap-3"><button className="rounded border border-slate-600 p-2 text-sm" onClick={()=>download(data,`ra-tieu-chi-lab-${data.run_id}.json`)}>Xuất phân tích tiêu chí</button><label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={onlyDifferences} onChange={e=>setOnlyDifferences(e.target.checked)}/>Chỉ hiện control có tiêu chí lệch</label></div>
  <div className="max-h-[32rem] space-y-3 overflow-auto">{data.controls.filter(c=>!onlyDifferences||c.differing_criteria).map(c=><article key={c.control_id} className="space-y-2 rounded-xl bg-slate-900 p-4"><button className="text-sm font-semibold text-teal-200 underline" onClick={()=>onSelect(c.control_id)}>{c.control_id} · {c.name}</button><p className="text-xs text-slate-400">Khóa thiết kế: {conclusionLabels[c.designer_status]||c.designer_status} · Model: {conclusionLabels[c.model_status]||c.model_status||'Không có kết quả hợp lệ'}. Trạng thái: chờ người rà.</p>{c.criteria.filter(v=>!onlyDifferences||v.differs).map(v=><div key={v.criterion_index} className="space-y-1 border-t border-slate-700 pt-2 text-xs"><strong>{v.criterion_index+1}. {v.criterion}</strong><p>Khóa: {labels[v.designer_verdict]} · Model: {labels[v.model_verdict]||'Lỗi kỹ thuật'}</p>{v.category_label&&<p className="text-amber-200">{v.category_label}</p>}<p className="whitespace-pre-wrap break-words">Lý do model: {v.model_rationale||'Không có lý do hợp lệ'}</p>{v.citations.map((s,i)=><p key={i} className="break-all text-slate-400">Nguồn: {s.filename} · SHA256 {s.sha256}</p>)}</div>)}</article>)}</div>
  <p className="break-all text-[10px] text-slate-500">Hash báo cáo đã phân tích: {data.report_sha256}. Đây là phiếu rà kỹ thuật, không ghi quyết định hoặc xóa lỗi.</p></>}
 </section>;
}
