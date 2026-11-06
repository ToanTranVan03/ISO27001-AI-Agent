# Chạy project trên máy hiện tại

Project gồm React/Vite + Three.js (`frontend-react`), FastAPI (`backend`),
Agent/LangGraph (`agent_core`), PostgreSQL và Ollama.

## Mở ứng dụng

- React khi phát triển: http://127.0.0.1:5173
- React đã build, phục vụ bởi FastAPI: http://127.0.0.1:8000
- Mô phỏng Triad: http://127.0.0.1:8000/simulation
- API docs: http://127.0.0.1:8000/docs

Đăng nhập bằng `INITIAL_ADMIN_USERNAME` và `INITIAL_ADMIN_PASSWORD` trong `.env`.
Thông tin này đã được kiểm tra đăng nhập với database hiện tại.

## Khởi động lại

Mở Docker Desktop và Ollama, sau đó chạy trong PowerShell:

```powershell
cd D:\AI_Agent_ISO27001
docker compose -f docker-compose.enterprise-lab.yml up -d postgres
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
node --test tests/navigation.test.mjs
```

Sau khi build, khởi động lại FastAPI nếu cần và mở cổng 8000 để dùng bản build.
Các bài test Python cô lập bước khởi tạo PostgreSQL; chúng không thay thế kiểm tra
API thực tế và suy luận Ollama. Không đưa `.env` hoặc mật khẩu vào Git.
