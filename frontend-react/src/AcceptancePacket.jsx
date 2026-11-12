const safe = value => String(value ?? 'Chưa xác định').replaceAll('|', '/').replaceAll('\n', ' ');

export default function AcceptancePacket({packet,exportFile,onSelect,controls}) {
 if(!packet)return null;
 function markdown() {
  return ['# Gói bàn giao và yêu cầu hồ sơ 56 control','',packet.note,'',
   `Đợt: ${packet.assessment_id}`,`Rubric: ${packet.rubric_sha256}`,`SoA: ${packet.soa_fingerprint}`,`Hash gói: ${packet.sha256}`,
   '', '## Điều kiện cần người thật xác nhận','',...packet.external_requirements.map(text=>`- [ ] ${text}`),
   ...packet.controls.flatMap(row=>['',`## ${row.control_id} — ${safe(row.name)}`,'',
    `Vai trò đề nghị: ${row.owner_role}`,`Vướng mắc: ${row.gaps.join(', ')||'Không phát hiện trong checklist hồ sơ'}`,
    `Kết luận máy: ${row.machine_conclusion}; thẩm định hiện hành: ${row.current_human_conclusion||'Chưa có'}`,
    `Loại nguồn cần rà: ${row.expected_evidence_types.join(', ')}`,'',
    '| Tiêu chí | Thẩm định | Viện dẫn | Yêu cầu |','|---|---|---|---|',
    ...row.criteria.map(c=>`| ${safe(c.criterion)} | ${c.verified_verdict} | ${c.verified_evidence_ids.join(', ')} | ${safe(c.request||'Không có yêu cầu bổ sung tự động')} |`),'',
    'Nguồn hiện có (chưa xác nhận đủ nội dung):',...row.sources.map(s=>`- ${safe(s.evidence_id)} · ${safe(s.source)} · SHA256 ${s.sha256} · synthetic=${s.is_synthetic}`),'',
    `Đề xuất chưa duyệt: ${row.treatment_proposal.action}`,
    `Người nhận đã ghi: ${safe(row.recorded_follow_up?.owner)}; hạn: ${safe(row.recorded_follow_up?.due_date)}; kiểm tra lại: ${safe(row.recorded_follow_up?.verification_plan)}`,
    `Kế hoạch đã ghi: ${safe(row.treatment_proposal.recorded_treatment)}`])].join('\n');
 }
 return <section className="space-y-3 rounded border border-slate-600 p-4">
  <h2 className="text-xl">Gói bàn giao · Yêu cầu hồ sơ theo từng tiêu chí</h2>
  <p>{packet.note}</p>
  <div className="flex flex-wrap gap-3">
   <button className="rounded bg-teal-800 p-2" onClick={()=>exportFile(packet,'ban-giao-56.json')}>Xuất gói bàn giao JSON</button>
   <button className="rounded bg-slate-700 p-2" onClick={()=>exportFile(markdown(),'ban-giao-56.md','text/markdown;charset=utf-8')}>Xuất gói bàn giao Markdown</button>
  </div>
  <details><summary>Điều kiện nghiệm thu cần xác nhận</summary><ul className="list-disc pl-6">{packet.external_requirements.map(text=><li key={text}>{text}</li>)}</ul></details>
  <details><summary>Yêu cầu nguồn và đề xuất xử lý · {packet.controls.length} control</summary>
   <div className="max-h-96 space-y-3 overflow-auto">{packet.controls.map(row=><article key={row.control_id} className="border-t border-slate-700 py-3">
    <button className="text-teal-300 underline" onClick={()=>onSelect(controls.find(c=>c.control_id===row.control_id))}>{row.control_id} · {row.name}</button>
    <p>{row.owner_role} · {row.excluded_by_recorded_decision?'Đã ghi loại trừ, chờ rà căn cứ':row.gaps.join(' · ')||'Không phát hiện vướng mắc trong checklist hồ sơ'}</p>
    <ul className="list-disc pl-6">{row.criteria.map(c=><li key={c.criterion_index}>{c.criterion} — {c.verified_verdict}{c.request&&<p>{c.request}</p>}</li>)}</ul>
    <p>Đề xuất chưa duyệt: {row.treatment_proposal.action}</p><p>Kế hoạch đã ghi — phụ trách: {row.recorded_follow_up?.owner||'chưa ghi'} · hạn: {row.recorded_follow_up?.due_date||'chưa ghi'} · kiểm tra lại: {row.recorded_follow_up?.verification_plan||'chưa ghi'}</p>
   </article>)}</div>
  </details>
 </section>;
}
