export default function A8EvidencePack({record}) {
 if(!record)return null;
 const evidence=record.evidence;
 function readable(artifact) {
  if(artifact.artifact.endsWith('.json')){try{return JSON.stringify(JSON.parse(artifact.content),null,2);}catch{/* Preserve malformed source text for review. */}}
  return artifact.content;
 }
 return <section className="space-y-3 rounded border border-slate-600 p-4">
  <h3 className="text-lg font-bold">{record.control_id} · {record.name}</h3>
  <p>Đọc điều kiện và nguồn dưới đây để tự kết luận. Màn hình này không hiển thị kết luận Agent hoặc đáp án nhóm.</p>
  <ol className="list-decimal space-y-2 pl-5">{record.criteria_details.map((c,i)=><li key={c.check||i}><strong>{c.check}</strong><p>Điều kiện đạt: {c.pass_condition}</p><p>Nguồn cần xem: {c.raw_source}</p><p className="text-amber-200">{c.missing_condition}</p></li>)}</ol>
  <p>Thu lúc: {evidence.collected_at} · Quan sát lúc: {evidence.observed_at||'Chưa có'} · Tài sản: {evidence.asset_id||'Chưa xác định'}</p>
  {!evidence.artifacts?.length?<p className="text-amber-200">Gói này không có artifact gốc. Hãy ghi nhận phần chưa thể xác minh.</p>:evidence.artifacts.map(a=><details key={a.artifact} className="rounded bg-slate-800 p-3"><summary>{a.artifact}</summary><p className="break-all text-xs">SHA256: {a.sha256}</p><pre className="max-h-96 overflow-auto whitespace-pre-wrap text-sm">{readable(a)}</pre></details>)}
  {!!evidence.collection_errors?.length&&<details open><summary>Lỗi/nguồn chưa thu được</summary><pre className="overflow-auto whitespace-pre-wrap text-xs">{JSON.stringify(evidence.collection_errors,null,2)}</pre></details>}
  <details><summary>Metadata đầy đủ để đối chiếu kỹ thuật</summary><pre className="max-h-72 overflow-auto whitespace-pre-wrap text-xs">{JSON.stringify(evidence,null,2)}</pre></details>
 </section>;
}
