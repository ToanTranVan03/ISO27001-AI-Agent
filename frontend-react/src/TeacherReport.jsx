import {useEffect,useState} from 'react';
const safe=x=>String(x??'Chưa có').replaceAll('|','/').replaceAll('\n',' ');
export default function TeacherReport({request,url,exportFile}) {
 const [data,setData]=useState(null),[error,setError]=useState(''),[hidden,setHidden]=useState(false);
 useEffect(()=>{let active=true;request(url).then(r=>{if(active)setData(r);}).catch(e=>{if(active){setHidden(e.status===403);setError(e.message);}});return()=>{active=false;};},[url,request]);
 if(hidden)return null;
 function markdown(){return ['# Báo cáo tiến độ đánh giá tuân thủ','',`Đợt: ${data.assessment_id}`,`Hash báo cáo: ${data.sha256}`,`SoA: ${data.soa_approval}`,'',
  `Phạm vi: ${data.scope_total}; A.8 ưu tiên: ${data.priority_count}. Chưa xác nhận nghiệm thu chuyên môn.`,
  `Nguồn ngoài preset: ${data.acceptance.controls_with_explicit_sources}; thẩm định hiện hành: ${data.acceptance.controls_with_current_human_review}.`,
  '', '## Giới hạn phương pháp','',...data.methodological_limits.map(x=>`- ${x}`),
  '', '## Phạm vi 56 control','', '| Control | Kết luận máy | Nguồn ngoài preset | Thẩm định hiện hành | Việc tiếp |','|---|---|---|---|---|',
  ...data.controls.map(c=>`| ${c.control_id} | ${safe(c.machine_conclusion)} | ${c.explicit_source_count} | ${c.human_review_current?'Có':'Chưa'} | ${safe(c.next_action)} |`),
  '', '## Kết quả thực nghiệm theo từng lượt','',...data.experiments.flatMap(r=>[
   `### ${r.run_id}`, '',`Nguồn: ${r.transport}; engine: ${r.mode}; rubric: ${r.rubric_version}; catalog: ${r.catalog_sha256}.`,
   `Quan sát: ${r.source_coverage}/${r.control_count}; lỗi đầu/cuối: ${r.first_errors}/${r.final_errors}; sửa hợp lệ: ${r.repaired}.`,
   `Người nộp đủ và tự khai báo độc lập: ${r.complete_independently_declared_reviewers.length}. ${r.pending_human_comparison?'Chưa có bảng độ đúng so với người chấm đủ.':'Xem bảng từng người trong JSON; tư cách chuyên môn cần xác nhận.'}`, '',
   '| Control | Kết quả máy | Lỗi | Hash bằng chứng |','|---|---|---|---|',
   ...r.control_results.map(c=>`| ${c.control_id} | ${safe(c.machine_status)} | ${c.error||''} | ${c.evidence_sha256} |`)]),
  '', '## Luyện tập giả lập','', `${data.practice_summary.simulated_label_count} nhãn giả lập, không cộng vào mẫu kiểm định hoặc nhãn người thật.`,
  '', '## Việc còn thiếu','',...Object.entries(data.pending_tasks).map(([stage,count])=>`- ${stage}: ${count}`)].join('\n');}
 return <section className="space-y-3 rounded border border-teal-700 p-4"><h2 className="text-xl">Báo cáo điều phối theo yêu cầu giảng viên (admin)</h2>
  {error&&<p role="alert">{error}</p>}{data?<><p>56 control và kết quả A.8 từng lượt; giữ riêng chấm giả định, chấm thật và kết luận hồ sơ. Báo cáo là snapshot lúc tải, chưa phải biên bản nghiệm thu.</p>
   <p>{data.experiments.length} lượt có report hợp lệ · {data.rejected_runs.length} lượt bị loại khỏi tổng hợp do dữ liệu/hash · {data.practice_summary.simulated_label_count} nhãn giả lập tách riêng.</p>
   <div className="flex flex-wrap gap-3"><button className="rounded bg-teal-800 p-2" onClick={()=>exportFile(data,'bao-cao-giang-vien.json')}>Xuất báo cáo JSON</button><button className="rounded bg-slate-700 p-2" onClick={()=>exportFile(markdown(),'bao-cao-giang-vien.md','text/markdown;charset=utf-8')}>Xuất báo cáo Markdown</button><button className="rounded bg-slate-700 p-2" onClick={async()=>{try{setData(await request(url));setError('');}catch(e){setError(e.message);}}}>Lấy snapshot mới</button></div>
  </>:<p>Đang tải báo cáo…</p>}
 </section>;
}
