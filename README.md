# ISO 27001 AI Agent

## Current deployment status

This repository is a local development/demo application, not a production enterprise deployment. The API and Ollama model run on the developer machine. Docker Compose can run a PostgreSQL database and simulated enterprise hosts, but it does not provide production identity management, TLS, secrets management, backups, monitoring, or high availability.

## Run locally on Windows

1. Install Python 3.11+, Docker Desktop with Compose, and Ollama. Pull the model with `ollama run qwen2.5:7b`.
2. Create a local environment file and change its sample password:

   ```powershell
   Copy-Item .env.example .env
   ```

   Keep the password in `POSTGRES_PASSWORD` and the password embedded in `DATABASE_URL` identical. Use a URL-safe password.

3. Install Python dependencies and start PostgreSQL:

   ```powershell
   pip install -r requirements.txt
   docker compose -f docker-compose.enterprise-lab.yml up -d postgres
   ```

4. Start the API:

   ```powershell
   uvicorn backend.main:app --reload --env-file .env
   ```

   On first startup the API creates its PostgreSQL tables, loads the 56 ISO controls from `docs/56_controls_scope.json`, and inserts the six existing demo cases. Open `http://127.0.0.1:8000/` for the web interface or `http://127.0.0.1:8000/docs` for Swagger.

The web interface uploads PDF/DOCX files to `/api/evidence`; extracted text, source metadata, and SHA-256 hashes are stored in PostgreSQL. `/api/evaluate` runs LangGraph, whose `COLLECT` node retrieves evidence from PostgreSQL. Each evaluation is also persisted in PostgreSQL. Adding real evidence for a demo control replaces its seeded sample evidence for subsequent evaluations.

The other simulated enterprise hosts are optional and can be started with the same Compose file. Do not use this lab Compose configuration as a production deployment.

## Shared multi-user Enterprise Lab (Giai đoạn 1)

**Mới:** xem tài liệu [HUONG_DAN_GIAI_DOAN_1.md](HUONG_DAN_GIAI_DOAN_1.md) để cài và chạy phiên đánh giá chung với tài khoản riêng, job lock PostgreSQL và bảng tiến độ theo thời gian gần thực.

Giao diện mới chạy tại `/`. Giao diện tuần 2 còn giữ tại `/legacy` (API legacy dùng dữ liệu không theo phiên đánh giá; **không dùng để thống kê tiến độ chung**). Chạy từ thư mục repo với:

```powershell
uvicorn backend.main:app --env-file .env --host 127.0.0.1 --port 8000
```

**Không khai báo số liệu mô phỏng thành benchmark thực nghiệm**; các chart và CSV cũ chỉ để tham khảo cho đến khi chạy lại bằng ground truth độc lập.
