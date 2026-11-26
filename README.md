# AI Agent đánh giá an toàn thông tin

Dự án nghiên cứu đánh giá một số tiêu chí tham chiếu ISO/IEC 27001:2022, ưu tiên con người. Bản mô phỏng có đánh giá NV015, phỏng vấn và đào tạo, phê duyệt hành động, xác minh nguồn, báo cáo và benchmark. Chế độ vận hành là `SIMULATION`.

## Chạy API trên Windows

Yêu cầu Python 3.11 trở lên. Chạy các lệnh tại thư mục dự án.

```powershell
py -3.11 -m venv .venv
$python = '.\.venv\Scripts\python.exe'
& $python -m pip install -r requirements.lock
& $python -m pip install --no-deps -e .
& $python -m uvicorn compliance_ai.api:create_app --factory --host 127.0.0.1 --port 8000
```

Mở [OpenAPI](http://127.0.0.1:8000/docs) hoặc chạy `Invoke-RestMethod http://127.0.0.1:8000/health` ở cửa sổ khác. Trên Linux/macOS, dùng `python3.11 -m venv .venv` và `.venv/bin/python` thay cho lệnh Windows.

## Chạy và debug bằng VS Code

Mở cả thư mục dự án bằng **File → Open Folder**. Cài hai extension Python và Python Debugger trong phần đề xuất của workspace. Chạy **Python: Select Interpreter** rồi chọn `.venv\Scripts\python.exe`. Sau khi cấu hình cơ sở dữ liệu ở dưới, chọn **Compliance AI — FastAPI** trong **Run and Debug** và bấm F5. API mặc định ở cổng 8000.

## PostgreSQL cục bộ

Cần Docker có Compose. Tạo `.env` từ `.env.example` nếu chưa có. Mỗi biến `POSTGRES_PASSWORD`, `APP_DB_PASSWORD`, `EVALUATOR_DB_PASSWORD` và `APP_SECRET_KEY` cần một giá trị riêng. Có thể sinh chuỗi hex bằng `python -c "import secrets; print(secrets.token_hex(32))"`. Lưu các giá trị vào `.env` cục bộ. Nếu `.env` đã được cấu hình cho container đang chạy, giữ nguyên mật khẩu và các URL đó.

Điền `MIGRATION_DATABASE_URL` theo mẫu `postgresql+psycopg://compliance_migrator:<POSTGRES_PASSWORD>@127.0.0.1:55432/compliance_ai` và `DATABASE_URL` theo mẫu `postgresql+psycopg://compliance_app:<APP_DB_PASSWORD>@127.0.0.1:55432/compliance_ai`. Thay các giá trị trong dấu góc bằng giá trị tương ứng. Khi đổi `POSTGRES_PORT`, cập nhật cả hai URL.

```powershell
docker compose up -d --wait db
& $python -m compliance_ai.cli configure-db-roles
& $python -m alembic upgrade head
& $python -m compliance_ai.cli seed-demo --seed 42
& $python -m compliance_ai.cli seed-demo-identities
```

Lệnh seed hỏi mật khẩu thử nghiệm do bạn chọn. Các tài khoản là `abc-admin`, `abc-auditor`, `abc-nv001` và `xy-admin`. Chạy lại seed giữ mật khẩu đã đặt cho các tài khoản hiện có. ABC có 50 hồ sơ mô phỏng sau lệnh seed-demo.

Sau khi khởi động lại API, kiểm tra [trạng thái DB](http://127.0.0.1:8000/ready). Xem [hợp đồng API](docs/API.md) để dùng token đăng nhập và thử phạm vi tenant.

PostgreSQL được công bố tại `127.0.0.1:55432` theo mặc định. Đặt `POSTGRES_PORT` trong `.env` nếu cần cổng khác. Dùng `docker compose stop db` để dừng và giữ dữ liệu cục bộ.

## Chạy dashboard

Giữ API đang chạy và mở terminal thứ hai tại dự án.

```powershell
$python = '.\.venv\Scripts\python.exe'
& $python -m streamlit run ui/streamlit_app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

Mở [dashboard](http://127.0.0.1:8501) và dùng tài khoản đã seed. Xem các bước [trình diễn NV015 và đào tạo](docs/USER_GUIDE.md).

Có thể chạy cả hai dưới Docker sau khi đã cấu hình role, chạy migration và seed như ở trên. Dừng lệnh Uvicorn và Streamlit đã chạy ở terminal trước khi dùng cùng cổng trong Docker.

```powershell
docker compose --profile app up -d --build api ui
```

## Kiểm thử

Phỏng vấn mặc định dùng rubric xác định. Để thử chấm ngữ nghĩa với model đã có trong Ollama trên cùng máy, đặt `LOCAL_INTERVIEW_MODEL=qwen2.5:3b` trong `.env` rồi khởi động lại API (Compose: chạy lại `docker compose --profile app up -d api ui`). Màn hình nhân viên sẽ cho chọn Ollama. Đây là tính năng thử nghiệm với câu trả lời mô phỏng; kết quả không chắc chắn hoặc lỗi dịch vụ chuyển sang thẩm định. Không cần bật model để chạy các phần còn lại.

Xem [ma trận 26 tiêu chí](docs/CONTROL_TRACEABILITY.md) và [RQ1–RQ5 cùng thiết kế đối chứng](docs/EXPERIMENT.md) để đối chiếu đề cương.

```powershell
& $python -m ruff check .
& $python -m mypy
& $python -m pytest -q
& $python -m compliance_ai.cli validate-catalog
& .\scripts\test-postgres.ps1
```

Xem [trạng thái triển khai](docs/IMPLEMENTATION_STATUS.md) và [kiến trúc](docs/ARCHITECTURE.md) để biết các giai đoạn đã được kiểm chứng.

Để chạy kiểm thử tích hợp, tạo cơ sở PostgreSQL dùng riêng có tên kết thúc bằng `_test`. Các biến `TEST_MIGRATION_DATABASE_URL`, `TEST_DATABASE_URL` và `TEST_EVALUATOR_DATABASE_URL` cùng trỏ tới cơ sở này với ba tài khoản riêng. Chạy `alembic upgrade head` với `MIGRATION_DATABASE_URL` trỏ tới cơ sở test, rồi chạy `python -m pytest -q`. Các bài tích hợp sẽ báo skip nếu thiếu biến. Xem [mô hình dữ liệu](docs/DATA_MODEL.md) và [rubric](docs/RUBRIC.md).

Đọc [quy trình benchmark](docs/EXPERIMENT.md), [điều kiện lab](docs/LAB.md) và [bằng chứng nghiệm thu](docs/IMPLEMENTATION_STATUS.md). Nếu chạy trên máy mới, giữ bản sao dữ liệu cục bộ, cấu hình kết nối và các bí mật trong kho phù hợp trước khi nâng cấp. Có thể dùng `pg_dump` cho cơ sở `compliance_ai`. Khôi phục thử trên một cơ sở dùng riêng và áp dụng migration theo phiên bản tương ứng.
