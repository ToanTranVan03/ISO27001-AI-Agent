export default function ReviewProvenance({assistance,exposure,setAssistance,setExposure}) {
 return <fieldset className="space-y-2 rounded border border-slate-600 p-3"><legend>Nguồn hỗ trợ khi chấm control này</legend>
  <label className="block">Cách đánh giá <select aria-label="Nguồn hỗ trợ đánh giá" value={assistance} onChange={e=>setAssistance(e.target.value)} className="bg-slate-800 p-2"><option value="unknown">Chưa khai báo</option><option value="unassisted">Tôi tự đọc và đánh giá</option><option value="ai_assisted">Có AI hỗ trợ kết luận/căn cứ</option><option value="team_discussion">Có trao đổi kết luận với người khác</option></select></label>
  <label className="block">Trước khi nộp <select aria-label="Đã xem kết quả trước khi chấm" value={exposure} onChange={e=>setExposure(e.target.value)} className="bg-slate-800 p-2"><option value="unknown">Chưa khai báo</option><option value="no">Chưa xem kết luận Agent/đáp án</option><option value="yes">Đã xem kết luận Agent hoặc đáp án</option></select></label>
  <p>Nhãn có hỗ trợ hoặc chưa khai báo vẫn được lưu và tính tiến độ; được tách khỏi đối chiếu độc lập. Hãy khai báo đúng thực tế. Khai báo này không xác nhận bạn là chuyên gia bên ngoài.</p>
 </fieldset>;
}
