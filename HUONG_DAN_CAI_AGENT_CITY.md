# ISO Enterprise Lab — Giao diện theo 2 video MP4

Đây là **giao diện mô phỏng để thử UX**, không phải backend AI Agent mới, không gọi Ollama hay tự đánh giá ISO. `ISOAgentCity.jsx` sử dụng React, Tailwind CSS và `lucide-react` vốn có trong `frontend-react`.

## 1) Chép file

Giải nén file ZIP vào thư mục tạm, sau đó chép `frontend-react/src/ISOAgentCity.jsx` vào `D:\AI_Agent_ISO27001\frontend-react\src\ISOAgentCity.jsx`.

## 2) Giữ đăng nhập và dashboard cũ

Trong `frontend-react/src/App.jsx`, thêm import:

```jsx
import ISOAgentCity from "./ISOAgentCity";
```

Bên trong component `App()`, thêm state:

```jsx
const [showAgentCity, setShowAgentCity] = useState(true);
```

Trong nhánh đã đăng nhập, thay **duy nhất vùng return giao diện** bằng khối sau. Giữ nguyên logic `login`, `logout`, `clearSession`, `request`, các API và khai báo state khác:

```jsx
if (user && assessment && token) {
  return (
    <>
      <div className="fixed right-3 bottom-3 z-[999] flex gap-2">
        <button type="button" onClick={() => setShowAgentCity(v => !v)} className="rounded-full bg-orange-400 px-4 py-2 text-xs font-black text-[#172337] shadow-lg">
          {showAgentCity ? "Xem Dashboard cũ" : "Xem AI Agent City"}
        </button>
      </div>
      {showAgentCity ? (
        <ISOAgentCity user={user} assessment={assessment} request={request} onLogout={logout} />
      ) : (
        <SpaceBaseDashboard key={assessment.assessment_id} user={user} assessment={assessment} request={request} onLogout={logout}/>
      )}
    </>
  );
}
```

**Nếu App.jsx hiện tại có sẵn một nhánh demo `AutonomousAuditDemo`, không xóa hoặc ghi đè chúng.** Chỉ cập nhật phần chọn giao diện nếu cần, vẫn giữ màn hình đăng nhập hiện tại.

## 3) Build và chạy

```powershell
cd D:\AI_Agent_ISO27001\frontend-react
npm run build
cd D:\AI_Agent_ISO27001
python -m uvicorn backend.main:app --env-file .env --host 127.0.0.1 --port 8000
```

Mở http://127.0.0.1:8000 và đăng nhập tài khoản PostgreSQL hiện có. Refresh bằng Ctrl+Shift+R.

## 4) Những gì demo này có

- Bản đồ isometric hai chủ đề: Sao Hỏa tối-cam và Pastel City gần phong cách video 2
- Sáu phòng ban; sáu bot chuyên gia AI Audit, danh sách đội chuyên gia như video 2
- Phóng to/thu nhỏ, chọn Agent để xem hồ sơ; chọn tòa nhà chỉ mở thẻ thông tin
- Bảng tiến độ nhiệm vụ, log não bộ AI có phân loại như video 1
- Một nút Auto-Audit; mô phỏng Agent bay qua các phòng, hỏi thiếu bằng chứng sau 3 giây
- Nhận file local để thử UX, nhưng **không upload** và **không phân tích nội dung file**

## 5) Phần cần phát triển tiếp để trở thành AI Agent thật

- API tạo Auto-Audit session/chạy nhiều control và job queue phía backend
- Polling/SSE từ FastAPI để robot di chuyển dựa trên trạng thái thực; không dùng timer
- Evidence upload thật và DB record (đúng schema hiện có)
- Trạng thái WAITING_EVIDENCE theo từng job, không treo toàn bộ workflow
- Liên kết kết quả Evaluator/Verifier với evidence ID, kiểm soát quyền truy cập và lưu audit trail
- Triển khai PostgreSQL/Ollama phù hợp môi trường deploy

Tuyệt đối không coi các sự kiện hoặc kết luận demo là chứng nhận đạt ISO 27001.
