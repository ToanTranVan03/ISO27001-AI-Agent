# Chạy project trên máy hiện tại

Project gồm React/Vite (`frontend-react`), FastAPI (`backend`),
Agent/LangGraph (`agent_core`), PostgreSQL và Ollama.

## Trọng tâm hiện tại

Live A.8 đã mở rộng sang 18 probe đại diện với rubric `a8-live-v2-active`. Nếu đang dùng image cũ, chạy `docker compose -f docker-compose.a8.yml build` trước `up -d`. Runtime dùng Python/OpenSSL trong container không có mạng ngoài; tiêu chí mới và giới hạn tại [Live A.8 v2](docs/LIVE_A8_V2.md). Các lượt live v1 vẫn là lịch sử riêng, không đổi nhãn đang chấm.

Từ 10/11/2026, giao diện mặc định là **Phạm vi 56 control** (8 A.6, 14 A.7, 34 A.8). Nhóm **Thực nghiệm 18 A.8** ưu tiên đo chuyên sâu; SoA tổng thể đủ 56 dòng, bản A.8 là báo cáo con. Văn phòng 3D/bình luận đã dừng phát triển. Xem [phạm vi và cách kiểm chứng mới](docs/HUONG_DE_TAI_A8.md).

## Mở ứng dụng

- React khi phát triển: http://127.0.0.1:5173
- React đã build, phục vụ bởi FastAPI: http://127.0.0.1:8000
- Đường dẫn cũ http://127.0.0.1:8000/simulation chuyển về giao diện đánh giá; trang 3D đã được gỡ.
- API docs: http://127.0.0.1:8000/docs

Đăng nhập bằng `INITIAL_ADMIN_USERNAME` và `INITIAL_ADMIN_PASSWORD` trong `.env`.
Thông tin này đã được kiểm tra đăng nhập với database hiện tại.

## Khởi động lại

Mở Docker Desktop và Ollama, sau đó chạy trong PowerShell:

```powershell
cd D:\AI_Agent_ISO27001
docker compose -f docker-compose.enterprise-lab.yml up -d postgres
docker compose -f docker-compose.a8.yml up -d
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Mở terminal thứ hai để chạy giao diện có tự cập nhật khi sửa mã:

```powershell
cd D:\AI_Agent_ISO27001\frontend-react
npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Máy này có PostgreSQL Windows ở cổng 5432. Container project dùng cổng **5433**,
được cấu hình bằng `POSTGRES_PORT` và `DATABASE_URL` trong `.env`.
Không cần dừng PostgreSQL Windows. Dữ liệu Docker được giữ trong volume hiện có.

## Build và kiểm tra

```powershell
cd D:\AI_Agent_ISO27001\frontend-react
npm.cmd run build
cd ..
.\.venv\Scripts\python.exe -m pytest tests -q
node --test tests/*.test.mjs
```

Sau khi build, khởi động lại FastAPI nếu cần và mở cổng 8000 để dùng bản build.
Các bài test Python cô lập bước khởi tạo PostgreSQL; chúng không thay thế kiểm tra
API thực tế và suy luận Ollama. Không đưa `.env` hoặc mật khẩu vào Git.

Lab A.8 dùng container `iso-a8-lab`, không có cổng công khai. Khi dừng toàn bộ bài, dừng cả container này. Chi tiết raw v2 và chấm mù: [Quy trình nghiệm thu](docs/QUY_TRINH_NGHIEM_THU_A8.md).
