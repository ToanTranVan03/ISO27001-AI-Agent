export default function ControlCriteriaReview({control,values,onChange}) {
 function update(index,key,value) {
  onChange(values.map((row,i)=>i===index?{...row,[key]:value}:row));
 }
 return <fieldset className="space-y-3 rounded border border-slate-600 p-3"><legend>Thẩm định từng tiêu chí của control</legend>
  <p>Ghi căn cứ và chọn nguồn cho từng tiêu chí. Thiếu nguồn chọn chưa rõ; kết luận tổng phải khớp rubric dự án: có chưa rõ → thiếu bằng chứng; đủ đạt → đạt; đủ không đạt → không đạt; đạt/không đạt → một phần.</p>
  {control.pass_criteria.map((text,index)=><article key={index} className="space-y-2 rounded bg-slate-800 p-3"><p>{index+1}. {text}</p>
   <select aria-label={`Kết quả tiêu chí ${index+1}`} value={values[index]?.verdict||'unknown'} onChange={e=>update(index,'verdict',e.target.value)} className="bg-slate-950 p-2"><option value="unknown">Chưa rõ / thiếu nguồn</option><option value="met">Đạt tiêu chí</option><option value="not_met">Không đạt tiêu chí</option></select>
   <textarea aria-label={`Căn cứ tiêu chí ${index+1}`} value={values[index]?.rationale||''} onChange={e=>update(index,'rationale',e.target.value)} className="block w-full bg-slate-950 p-2" placeholder="Căn cứ đối chiếu, tối thiểu 10 ký tự"/>
   <label className="block">Nguồn viện dẫn (có thể chọn nhiều)<select multiple aria-label={`Nguồn tiêu chí ${index+1}`} value={values[index]?.evidence_ids||[]} onChange={e=>update(index,'evidence_ids',Array.from(e.target.selectedOptions,o=>o.value))} className="block w-full bg-slate-950 p-2">{control.evidence.map(e=><option key={e.evidence_id} value={e.evidence_id}>{e.evidence_id} · {e.source}</option>)}</select></label>
  </article>)}
 </fieldset>;
}
