# ISO Enterprise Lab — Giai đoạn 2 (mô hình doanh nghiệp giả lập)

## Phạm vi thật sự của bản này

- Giữ nguyên Giai đoạn 1: xác thực, 56 controls, tiến độ dùng chung PostgreSQL, khóa tránh chạy trùng, LangGraph và Ollama.
- Thêm 5 khu vực doanh nghiệp giả lập: HR, Physical, IAM, Network, SecOps. Kịch bản `healthy`, `partial`, `gap` do admin chọn, lưu cho **cùng đợt đánh giá**.
- Thêm **5 collectors đại diện** ở A.6.1, A.7.1, A.8.5, A.8.20 và A.8.13. Các controls còn lại không được giả mạo bằng chứng tự động.
- Nút chạy Agent hiện hữu sẽ tạo **immutable synthetic snapshot** từ tình huống lab tại thời điểm chạy, cấp mã evidence `LAB-*`, lưu SHA-256, metadata, và gửi bằng chứng tới LangGraph/Ollama để đánh giá. Việc ghi evidence không thay đổi môi trường doanh nghiệp thực tế.
- Thay kịch bản làm trạng thái control liên quan quay về `NOT_STARTED`; **lịch sử đánh giá và snapshot trước được giữ**, snapshot mới được chọn thay snapshot cũ trong lần chạy kế tiếp.
- **Quan trọng**: Đây là simulated enterprise, chưa thu thập live configuration từ container Ubuntu, Nginx hoặc máy thật. Trạng thái `healthy` không đồng nghĩa control ISO thực tế đã đạt. Không dùng dữ liệu này làm kết quả đánh giá doanh nghiệp thật hay số liệu benchmark chứng nhận.

## Chép vào Git repository ổ D (Windows PowerShell)

1. Kiểm tra đang ở nhánh tính năng và working tree sạch hoặc đã commit/lưu lại thay đổi trước khi chép. **Không ghi đè những phần đang làm dở**.
2. Sao lưu các file sẽ cập nhật (`backend/main.py`, `backend/database.py`, `agent_core/graph_builder.py`, `frontend/workspace.html`) hoặc commit công việc hiện tại trước.
3. Giải nén ZIP này vào `D:\ISO_Enterprise_Stage2` (hoặc thư mục riêng bất kỳ). Cấu trúc trong ZIP có thư mục `ISO_Enterprise_Lab`.
4. Chạy trong PowerShell:

```powershell
$src = "D:\ISO_Enterprise_Stage2\ISO_Enterprise_Lab"
$dst = "D:\AI_Agent_ISO27001"
$files = @(
  "backend\enterprise_spec.py", "backend\enterprise_lab.py", "backend\enterprise_api.py",
  "backend\database.py", "backend\main.py",
  "agent_core\graph_builder.py",
  "frontend\enterprise.html", "frontend\workspace.html",
  "tests\test_enterprise_spec.py", "HUONG_DAN_GIAI_DOAN_2.md"
)
foreach ($file in $files) {
  $target = Join-Path $dst $file
  New-Item -ItemType Directory -Force (Split-Path $target) | Out-Null
  Copy-Item (Join-Path $src $file) $target -Force
}
```

**Không** chép đè `.env`, `.venv`, `.git`, `docker-compose.enterprise-lab.yml`, database hoặc dữ liệu cũ. Nếu mã ở D đã sửa khác Giai đoạn 1, dùng so sánh diff thay vì sao chép mù quáng.

## Khởi động

Với PostgreSQL Docker `iso27001-postgres` đã kết nối được, Ollama đã cài và `qwen2.5:7b` đã tải:

```powershell
cd D:\AI_Agent_ISO27001
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --env-file .env --host 127.0.0.1 --port 8000
```

- `http://127.0.0.1:8000` — Control Workspace, đăng nhập như trước.
- Sau đăng nhập bấm **🏢 Doanh nghiệp giả lập** ở thanh trên hoặc mở `http://127.0.0.1:8000/enterprise` trong cùng tab.
- Admin chọn node IAM → chuyển tình huống `gap` → **Áp dụng** → **Chạy AI Agent**; xem bằng chứng. Giai đoạn này vẫn cần mô hình Ollama hoạt động và mất thời gian xử lý tùy máy.
- Mở cùng địa chỉ trên máy khác trong mạng LAN và cùng campaign, tiến độ của control sẽ được đồng bộ (API phải được cấu hình lắng nghe IP LAN và có bảo vệ mạng phù hợp). Không công khai demo với mật khẩu bị lộ.

## Kiểm thử chức năng

```powershell
python -m pytest -q tests/test_enterprise_spec.py
```

Chưa có `pytest` thì cài gói dev từ `requirements-dev.txt` trong venv. Hãy kiểm tra `GET /docs` để thấy `Enterprise Lab` APIs. Mô-đun thu thập sử dụng `psycopg` và cần PostgreSQL thực sự để chạy end-to-end.

## Hướng tiếp theo sau giai đoạn 2

- Gắn collectors **read-only** vào các container lab / API nội bộ thực sự (không cấp Docker socket hoặc quyền admin cho LLM).
- Thiết kế chấm deterministic rules theo rubric được xác minh + đối chứng SLM; cách chấm phải dựa trên bằng chứng, không lộ ground-truth label.
- Benchmark chạy 3 profiles × 56 controls với dataset và nhãn độc lập; tách dữ liệu `simulated`, `observed` và kết luận `human-reviewed`.
- Dashboard biểu đồ so sánh bằng **dữ liệu thực sự đã chạy**, không gắn nhãn như số liệu công ty có chứng nhận.
