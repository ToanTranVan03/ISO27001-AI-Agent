import {useEffect,useState} from 'react';

export default function A8SimulatedReview({request,url,download,practice=false}) {
 const [result,setResult]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 useEffect(()=>{if(!practice)return;let active=true;request(url).then(r=>{if(active&&r.saved_at)setResult(r);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[practice,request,url]);
 async function run(){setBusy(true);setError('');try{setResult(await request(url,practice?{method:'POST'}:undefined));}catch(e){setError(e.message);}finally{setBusy(false);}}
 return <section className="space-y-3 rounded border border-amber-500 p-4">
  <h2 className="text-xl">{practice?'Chấm giả định để luyện tập · Gói mẫu riêng':'Chấm giả lập · Tách khỏi người đánh giá'}</h2>
  <p>Kiểm thử đối chiếu bằng luật trên facts và rubric lab đã lưu. Không nộp dưới tài khoản thành viên, không tính accuracy với người thật hoặc mở quyền duyệt SoA.</p>
  {practice&&<p>Áp dụng cho mọi tài khoản. Dùng bộ phát triển raw mixed đã công khai; không dùng lượt đang chọn. Sau khi xem mẫu, cần khai đúng việc đã tiếp xúc bộ phát triển khi chấm thật.</p>}
  <button disabled={busy} onClick={run} className="rounded bg-amber-900 p-2">{busy?'Đang chấm giả lập':practice?'Chấm nhanh 18 control mẫu':'Chấm giả lập lượt này (admin)'}</button>
  {error&&<p role="alert">{error}</p>}
  {result&&<><p>{result.note}</p>{result.saved_at&&<p>Đã lưu gói giả lập cho {result.practice_account_name} · {result.labels.length}/18 · {result.saved_at}. Người thực hiện: bộ máy giả lập, không phải chủ tài khoản.</p>}{result.exposure_note&&<p>{result.exposure_note}</p>}<button className="rounded bg-slate-700 p-2" onClick={()=>download(result,practice?'cham-gia-dinh-luyen-tap.json':'cham-gia-lap-a8.json')}>Xuất kết quả giả lập JSON</button>
   <div className="max-h-96 overflow-auto"><table className="w-full text-left text-sm"><thead><tr><th>Control</th><th>Giả lập</th><th>Agent</th><th>Căn cứ tiêu chí</th></tr></thead><tbody>{result.labels.map((row,i)=><tr key={row.control_id} className="border-t border-slate-700"><td>{row.control_id}</td><td>{row.expected}</td><td>{result.simulated_comparison.cases[i].prediction||'Lỗi engine'}</td><td className="p-2">{row.rationale}</td></tr>)}</tbody></table></div>
  </>}
 </section>;
}
