import {useEffect,useState} from 'react';

export default function A8PracticeProgress({request,url,download}) {
 const [data,setData]=useState(null),[error,setError]=useState('');
 useEffect(()=>{let active=true;async function load(){try{const r=await request(url);if(active){setData(r);setError('');}}catch(e){if(active)setError(e.message);}}load();const timer=setInterval(load,4000);return()=>{active=false;clearInterval(timer);};},[request,url]);
 return <section className="space-y-3 rounded border border-amber-500 p-4"><h2 className="text-xl">Admin · Tổng hợp chấm giả định của các tài khoản</h2>
  {error&&<p role="alert">{error}</p>}{data&&<><p>{data.note}</p><p>{data.accounts.length} tài khoản đã lưu · {data.simulated_label_count} nhãn giả lập · 0 nhãn người thật từ khu luyện tập.</p>
   <table className="w-full text-left text-sm"><thead><tr><th>Tài khoản</th><th>Giả định đã lưu</th><th>Thời điểm</th></tr></thead><tbody>{data.accounts.map(row=><tr key={row.account_id} className="border-t border-slate-700"><td className="p-2">{row.account_name}</td><td>{row.submitted}/{row.total}</td><td>{new Date(row.saved_at).toLocaleString('vi-VN',{timeZone:'Asia/Bangkok'})}</td></tr>)}</tbody></table>
   <button className="rounded bg-slate-700 p-2" onClick={()=>download(data,'tien-do-cham-gia-dinh.json')}>Xuất tổng hợp giả định</button><p>Tự cập nhật mỗi 4 giây. Bảng “Tiến độ chấm thật của lượt đang chọn” bên dưới là dữ liệu khác.</p>
  </>}
 </section>;
}
