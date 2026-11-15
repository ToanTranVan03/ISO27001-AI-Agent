export default function LegacyReviewNotice({runs,onSelect}) {
 const target=runs.find(r=>r.can_review&&r.has_artifacts);
 return <section role="status" className="space-y-3 rounded border border-amber-500 p-4"><h2 className="text-xl">Lượt lịch sử · Chỉ đọc, không thể nộp chấm mới</h2>
  <p>Lượt đang chọn dùng giao thức cũ. Đây không phải lỗi tài khoản. Phiếu nộp được ẩn để tránh nhập rồi không nộp được; dữ liệu và nhãn lịch sử vẫn giữ nguyên.</p>
  {target?<><p>Có lượt hỗ trợ chấm với artifact gốc: {target.run_id.slice(0,8)} · {target.created_at}. Khoa và Tú cần thống nhất cùng mã lượt trước khi chấm.</p><button className="rounded bg-teal-800 p-3" onClick={()=>onSelect(target.run_id)}>Mở lượt có thể chấm · {target.run_id.slice(0,8)}</button></>:<p>Chưa có lượt phù hợp. Nhờ admin tạo lượt mới theo giao thức hiện tại; không chuyển đổi hoặc sửa nhãn cũ.</p>}
 </section>;
}
