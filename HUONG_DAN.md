# ISO Agent City — Giai đoạn 3: Tự đọc nguồn được cấp quyền + xem lỗi 6 control

## Mục đích

- **Không có nút upload**. Giao diện 3D, đăng nhập, API FastAPI và dữ liệu PostgreSQL cũ được giữ nguyên.
- Khi Auto-Audit chạy, collector tùy chọn đọc **các tệp PDF/DOCX đã được khai báo trong một thư mục được người quản trị chủ động cho phép**. Đây là nguồn thật, phân biệt với synthetic lab evidence.
- Không quét cả máy, không tự truy cập web/email/ERP và không đọc tệp ngoài danh sách `manifest.json`.
- Đánh giá tiếp tục nếu không đủ bằng chứng. Không tự kết luận tuân thủ.
- Hiển thị **danh sách control bị lỗi** và mã job đã lưu trong PostgreSQL, giúp kiểm tra trước khi chạy lại.
- **Không khẳng định 6 lỗi cũ đã tự được sửa**; bản này giúp xác định và xử lý đúng nguyên nhân. Các lỗi job cũ có thể chỉ có thông báo chung, trong khi lượt chạy mới sẽ ghi thêm tên loại ngoại lệ.

## Cài đặt — nên dùng thư mục giải nén riêng

1. Dừng Uvicorn bằng `Ctrl+C`; vẫn để Docker PostgreSQL và Ollama chạy.
2. Giải nén ZIP vào `D:\ISO_AgentCity_GiaiDoan3`.
3. Mở PowerShell trong thư mục chứa `CAI_GIAI_DOAN_3.ps1` và chạy:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
& "D:\ISO_AgentCity_GiaiDoan3\CAI_GIAI_DOAN_3.ps1" -ProjectRoot "D:\AI_Agent_ISO27001"
```

Nếu bạn đã giải nén thẳng vào `D:\AI_Agent_ISO27001`, cũng có thể chạy:

```powershell
& "D:\AI_Agent_ISO27001\CAI_GIAI_DOAN_3.ps1" -ProjectRoot "D:\AI_Agent_ISO27001"
```

Script xử lý an toàn trường hợp file nguồn và file đích là cùng một đường dẫn, và tạo bản sao lưu ở bên ngoài thư mục dự án.

4. Build và kiểm thử:

```powershell
cd D:\AI_Agent_ISO27001
.\.venv\Scripts\Activate.ps1
python -m compileall backend
python -m pytest tests/test_auto_sources.py -q
cd frontend-react
npm run build
cd ..
python -m uvicorn backend.main:app --env-file .env --host 127.0.0.1 --port 8000
```

## Kết quả ngay cả khi chưa cấu hình tài liệu thật

Mở `http://127.0.0.1:8000`, đăng nhập, kéo xuống phần **TIẾN ĐỘ KIỂM TOÁN THỰC THI**. Bạn sẽ thấy dòng **Nguồn bằng chứng tự động: Chưa kết nối thư mục — hiện chỉ sử dụng dữ liệu lab**.

Bấm **Xem 6 tác vụ lỗi** để xem các control, job ID và lỗi backend đã lưu. Với các job trước bản vá, thông báo có thể vẫn là `Không thể chạy Agent...` vì dữ liệu lịch sử không chứa nguyên nhân chi tiết. Không thể tự suy ra lỗi từ tổng `6`.

## Bật thư mục bằng chứng thật (không upload)

1. Tạo thư mục riêng, ví dụ `D:\ISO_Evidence_Approved`.
2. Đặt các tài liệu PDF/DOCX bạn được phép xử lý trong thư mục này, **không để tài liệu có thông tin cá nhân nhạy cảm nếu chưa được phép sử dụng**.
3. Tạo file `D:\ISO_Evidence_Approved\manifest.json` dựa trên file mẫu trong ZIP. Mỗi item khai báo:
   - `control_id`: ví dụ `A.6.1`.
   - `file`: **tên file**, ví dụ `HR_Screening_Policy.pdf`, không dùng đường dẫn hay thư mục con.
   - `evidence_type`: một loại bằng chứng hợp lệ của control. Ví dụ A.6.1 có `EVID_PPL_HR_RECORD`. Các loại khác xem ở `docs/56_controls_scope.json`.
   - `enabled`: `true`/`false`.
4. Thêm dòng sau vào file `.env` của dự án (không commit file `.env`):

```dotenv
ISO_AUTO_EVIDENCE_DIR=D:\ISO_Evidence_Approved
```

5. Dừng và khởi động lại FastAPI để đọc `.env`; chạy một phiên Auto-Audit mới. Khi job kiểm tra A.6.1, connector sẽ đọc file, kiểm tra dung lượng <=15MB, định dạng PDF/DOCX, trích xuất text, lưu evidence với SHA-256 vào PostgreSQL rồi chạy pipeline Agent.

6. Nhật ký sẽ xuất hiện `SOURCE_INDEXED` nếu file mới được lưu, `SOURCE_ALREADY_INDEXED` nếu cùng mã băm đã có, `SOURCE_CHANGED_REVIEW` nếu cùng tên nhưng nội dung thay đổi (cần đổi tên file phiên bản và cập nhật manifest), hoặc `SOURCE_ERROR` nếu không đọc được.

**Quan trọng:** không đưa manifest/tài liệu thật hoặc `.env` lên GitHub. Nếu PDF chỉ là ảnh scan không có văn bản, parser hiện chưa OCR; nguồn sẽ báo lỗi đọc chứ không bịa nội dung. Tài liệu được trích xuất vào PostgreSQL, vì vậy phải giới hạn quyền truy cập database và đảm bảo bạn được phép lưu trữ.

## API mới (được bảo vệ bởi đăng nhập và quyền đợt đánh giá)

- `GET /api/auto-audits/{run_id}/failures` — danh sách control lỗi, job ID, lý do có sẵn.
- `GET /api/assessments/{assessment_id}/auto-audits/sources` — trạng thái nguồn thư mục (không công khai đường dẫn local).

**Không thay đổi `backend/main.py` hoặc `frontend-react/src/App.jsx`** vì router Auto-Audit đã được đăng ký ở giai đoạn trước. Nếu chương trình không có `app.include_router(auto_audit.router)`, script sẽ dừng an toàn.

## Giới hạn

- Auto source là bộ thu thập **theo danh sách đã cấp quyền**; chưa phải AI tự mở trình duyệt, đọc email, đăng nhập AD/ERP/SIEM hay lấy dữ liệu mạng.
- Các vai trò AI chuyên gia được trực quan hóa trên map; chưa phải 6 mô hình chạy độc lập.
- Worker hiện vẫn nằm trong tiến trình FastAPI; tắt API lúc đang chạy sẽ làm gián đoạn phiên. Chưa có queue bền vững.
- Đã kiểm tra cú pháp Python, phân tích cú pháp JSX, và kiểm thử mock connector. Chưa chạy end-to-end với Docker, PostgreSQL, Ollama và trình duyệt trên máy của bạn.
