export default function AcceptanceWorklist({data,exportFile,onSelect}) {
 const list=data.acceptance_worklist;
 if(!list)return null;
 function markdown() {
  const rows=list.tasks.map(t=>`| ${t.control_id||'Toàn phạm vi'} | ${t.stage} | ${t.owner_role} | ${t.message.replaceAll('|','/')} |`);
  return ['# Việc cần hoàn thiện — 56 control','',list.note,'',`Rubric: ${list.rubric_sha256}`,`SoA: ${list.soa_fingerprint}`,'','| Control | Bước | Phụ trách | Công việc |','|---|---|---|---|',...rows].join('\n');
 }
 return <section className="space-y-3 rounded border border-slate-600 p-4"><h2 className="text-xl">Việc còn thiếu để bàn giao</h2><p>{list.note}</p><p>{Object.entries(list.by_stage).map(([stage,count])=>`${stage}: ${count}`).join(' · ')}</p>
  <p>{data.acceptance.controls_with_explicit_sources||0}/56 control có nguồn dùng được trong chế độ không lấy preset; trong đó {data.acceptance.controls_with_captured_lab_sources||0} có bản thu lab. Số lượng này chưa xác nhận đủ nội dung, nguồn production hoặc kết luận chính thức.</p>
  <div className="flex gap-3"><button onClick={()=>exportFile(list,'viec-can-lam-56.json')} className="rounded bg-slate-700 p-2">Xuất danh sách JSON</button><button onClick={()=>exportFile(markdown(),'viec-can-lam-56.md','text/markdown;charset=utf-8')} className="rounded bg-slate-700 p-2">Xuất danh sách Markdown</button></div>
  <details><summary>{list.tasks.length} việc theo thứ tự xử lý — mở để giao việc</summary><div className="max-h-96 overflow-auto"><table className="w-full text-left text-sm"><thead><tr><th>Control</th><th>Phụ trách</th><th>Việc cần làm</th></tr></thead><tbody>{list.tasks.map((t,i)=><tr key={i} className="border-t border-slate-700"><td className="p-2">{t.control_id?<button className="text-teal-300 underline" onClick={()=>onSelect(data.controls.find(c=>c.control_id===t.control_id))}>{t.control_id}</button>:'Toàn phạm vi'}</td><td>{t.owner_role}</td><td className="p-2">{t.message}</td></tr>)}</tbody></table></div></details>
 </section>;
}
