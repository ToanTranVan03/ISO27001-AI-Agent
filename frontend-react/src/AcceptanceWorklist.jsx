import AcceptancePacket from './AcceptancePacket';

export default function AcceptanceWorklist({data,exportFile,onSelect}) {
 const list=data.acceptance_worklist;
 if(!list)return null;
 function markdown() {
  const rows=list.tasks.map(t=>`| ${t.control_id||'Toàn phạm vi'} | ${t.stage} | ${t.owner_role} | ${t.message.replaceAll('|','/')} |`);
  return ['# Việc cần hoàn thiện — 56 control','',list.note,'',`Rubric: ${list.rubric_sha256}`,`SoA: ${list.soa_fingerprint}`,'','| Control | Bước | Phụ trách | Công việc |','|---|---|---|---|',...rows].join('\n');
 }
 return <section className="space-y-3 rounded border border-slate-600 p-4"><h2 className="text-xl">Việc còn thiếu để bàn giao</h2><p>{list.note}</p><p>{Object.entries(list.by_stage).map(([stage,count])=>`${stage}: ${count}`).join(' · ')}</p>
  <p>{data.acceptance.controls_with_explicit_sources||0}/56 control có nguồn ngoài preset được lưu; trong đó {data.acceptance.controls_with_captured_lab_sources||0} có bản thu lab. Số lượng này chưa xác nhận đủ nội dung, nguồn production hoặc kết luận chính thức.</p>
  <p>{data.acceptance.controls_with_usable_text_sources??0}/56 control có nguồn qua kiểm tra nội dung tối thiểu; {data.acceptance.controls_with_source_quality_issues??0} control có nguồn cần kiểm tra lại. Kiểm tra này không xác nhận chất lượng chuyên môn hoặc tuân thủ.</p><div className="flex gap-3"><button onClick={()=>exportFile(list,'viec-can-lam-56.json')} className="rounded bg-slate-700 p-2">Xuất danh sách JSON</button><button onClick={()=>exportFile(markdown(),'viec-can-lam-56.md','text/markdown;charset=utf-8')} className="rounded bg-slate-700 p-2">Xuất danh sách Markdown</button></div>
  <details><summary>{list.tasks.length} việc theo thứ tự xử lý — mở để giao việc</summary><div className="max-h-96 overflow-auto"><table className="w-full text-left text-sm"><thead><tr><th>Control</th><th>Phụ trách</th><th>Việc cần làm</th></tr></thead><tbody>{list.tasks.map((t,i)=><tr key={i} className="border-t border-slate-700"><td className="p-2">{t.control_id?<button className="text-teal-300 underline" onClick={()=>onSelect(data.controls.find(c=>c.control_id===t.control_id))}>{t.control_id}</button>:'Toàn phạm vi'}</td><td>{t.owner_role}</td><td className="p-2">{t.message}</td></tr>)}</tbody></table></div></details>
  {data.source_requests&&<section className="space-y-3 rounded-xl border border-teal-800 p-4"><h3 className="font-semibold">Phiếu yêu cầu nguồn theo nhóm phụ trách</h3><p className="text-xs text-slate-400">{data.source_requests.note}</p><div className="flex flex-wrap gap-2">{Object.entries(data.source_requests.by_role).map(([role,count],i)=><button key={role} onClick={()=>exportFile({...data.source_requests,requests:data.source_requests.requests.filter(r=>r.owner_role===role)},`yeu-cau-nguon-nhom-${i+1}.json`)} className="rounded-xl border border-slate-600 p-3 text-xs">{role} · {count} control · Xuất JSON</button>)}</div></section>}
  <AcceptancePacket packet={data.handoff_packet} exportFile={exportFile} onSelect={onSelect} controls={data.controls}/>
 </section>;
}
