# ISO Enterprise Lab — Giai đoạn 1: làm việc chung nhiều người

Đây là bản mở rộng trực tiếp từ ZIP của Khoa. Mã nguồn gốc vẫn nằm trong các thư mục `agent_core/`, `backend/`, `evidence_collectors/`, `frontend/` và tập dữ liệu gốc `docs/`.

**Đã xây dựng:** đăng nhập; admin tạo thành viên; bảng tiến độ A.6 (8), A.7 (14), A.8 (34) theo phiên đánh giá; nút chạy Agent theo từng control; tránh chạy trùng bằng transaction PostgreSQL; job lưu DB; tự cập nhật trạng thái giao diện 3 giây; upload evidence gắn với phiên đánh giá; lịch sử kết quả; xác nhận `Not Applicable` bởi admin; khôi phục trạng thái sau khi API restart.

**Chưa xây trong giai đoạn này:** dockerized application đầy đủ, xác thực cấp doanh nghiệp/SSO, TLS, queue worker bền vững, collectors từ HR/Physical/IAM/Network/SecOps thật, đủ catalog A.5 (37), benchmark định lượng đầy đủ, dashboard biểu đồ mô hình có số đo thực, RAG hoàn chỉnh. Ba container hiện có trong `docker-compose.enterprise-lab.yml` chỉ mang tính mô phỏng, không được coi là bằng chứng chứng nhận.

## 1. Cài đặt Windows 10/11

Cần: Python 3.11+, Docker Desktop đang chạy, Ollama. Nếu phần cứng có thể chạy Qwen 7B, dùng bản mặc định trong dự án. Mở PowerShell **tại thư mục chứa `backend`, `frontend`**.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Chỉnh `.env` để có mật khẩu riêng cho PostgreSQL và admin; giữ giá trị mật khẩu trong `POSTGRES_PASSWORD` và `DATABASE_URL` giống nhau (chỉ dùng ký tự URL-safe):

```dotenv
POSTGRES_PASSWORD=YOUR_OWN_STRONG_DB_PASSWORD
DATABASE_URL=postgresql://iso27001_app:YOUR_OWN_STRONG_DB_PASSWORD@localhost:5432/iso27001
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=REPLACE_WITH_YOUR_LONG_UNIQUE_ADMIN_PASSWORD
```

Không đẩy `.env` lên Git/GitHub và không chia sẻ mật khẩu trong video demo.

## 2. Bật database và Ollama

```powershell
docker compose -f docker-compose.enterprise-lab.yml up -d postgres
ollama pull qwen2.5:7b
```

Đảm bảo ứng dụng Ollama đang chạy. Kiểm tra ở cửa sổ terminal khác:

```powershell
ollama list
docker compose -f docker-compose.enterprise-lab.yml ps
```

Có thể bật thêm các node mô phỏng (không cần thiết cho đăng nhập và công việc nhóm, và chưa được Agent thu thập dữ liệu tự động):

```powershell
docker compose -f docker-compose.enterprise-lab.yml up -d
```

## 3. Chạy API + giao diện

Mở PowerShell (sau khi kích hoạt `.venv`):

```powershell
uvicorn backend.main:app --env-file .env --host 127.0.0.1 --port 8000
```

Mở `http://127.0.0.1:8000/` rồi đăng nhập bằng `INITIAL_ADMIN_USERNAME` và `INITIAL_ADMIN_PASSWORD`. API tạo bảng PostgreSQL nếu chưa có, giữ nguyên bảng và dữ liệu có sẵn. Kết quả được lưu trong database, không nằm trong browser.

Tại màn hình chính, bấm **+ Thành viên** để tạo `khoa` và `toan` (đặt mật khẩu riêng). Chọn A.6.1, nạp tài liệu PDF/DOCX và bấm **Chạy AI Agent**. Nếu thiếu bằng chứng, control hiện **Chờ bằng chứng** thay vì tự suy đoán.

### Cho máy khác trong cùng mạng LAN truy cập

Trên máy chủ API, đổi lệnh chạy thành:

```powershell
uvicorn backend.main:app --env-file .env --host 0.0.0.0 --port 8000
```

Các máy khác mở `http://IP_MAY_CHU:8000/`. Chỉ làm vậy trong **mạng lab đáng tin cậy**; mở đúng cổng 8000 trong Windows Firewall khi cần. Không mở PostgreSQL (5432), Ollama (11434), hoặc API ra Internet. HTTP LAN không mã hóa nên nếu có dữ liệu nhạy cảm hoặc truy cập từ ngoài LAN, cần dựng HTTPS/reverse proxy và VPN. Nếu thành viên truy cập từ ngoài, trước mắt sử dụng mạng riêng VPN đã được cấu hình bảo mật. Không chia sẻ mật khẩu tài khoản giữa các thành viên.

## 4. Thử nghiệm đồng thời hai người

1. Admin đăng nhập trình duyệt 1. Thành viên B đăng nhập trình duyệt 2 (máy khác hoặc cửa sổ riêng tư).
2. Cả hai mở A.6.1 thuộc cùng đợt đánh giá.
3. Người A bấm **Chạy AI Agent**; màn hình người B đổi thành **Đang chạy** sau tối đa vài giây.
4. Nếu người B bấm chạy cùng lúc, backend trả **HTTP 409**, không chạy trùng. Khoá nằm trong PostgreSQL nên vẫn hiệu quả khi dùng hai trình duyệt/máy.
5. Kết quả được lưu bảng `evaluations`, `agent_jobs`, `assessment_events` và `control_progress`. Sau tải lại trang, tất cả vẫn thấy trạng thái chung.
6. Khi Agent trả `Insufficient Evidence`, tiến độ là `WAITING_EVIDENCE`; tải bằng chứng rồi bấm **Đánh giá lại**. Nếu `Not Applicable`, admin xác nhận với lý do.

**Lưu ý:** `COMPLETED` là hoàn tất lượt đánh giá, **không có nghĩa `Compliant`**.

## 5. Vì sao một số control chưa có kết quả?

Các bằng chứng seed của bộ 6 test cases trong phiên bản Khoa được gắn `is_sample=TRUE`. Trong luồng multi-user mới, **không dùng các sample này như bằng chứng doanh nghiệp**. Phải nạp PDF/DOCX qua giao diện, hoặc gắn collector lab thực tế trong giai đoạn kế tiếp.

Trong `agent_core/graph_builder.py`, `expected_status` trong test case không còn được dùng để ghi đè kết luận AI; Agent chỉ lưu evidence ID hợp lệ xuất hiện trong kết quả mô hình. Đây là sửa đổi nhằm tránh nhầm dữ liệu ground truth với dữ liệu lúc chạy Agent.

## 6. Những bảng mới

- `team_users`: tài khoản, password PBKDF2 và phân quyền.
- `team_sessions`: phiên truy cập (chỉ lưu hash của token, tự hết hạn sau 8h).
- `assessment_campaigns` và `assessment_members`: một đợt đánh giá nhóm chung.
- `control_progress`: khoá `(assessment_id, control_id)` và trạng thái, chủ xử lý, job, kết quả mới nhất.
- `agent_jobs`: trạng thái job và thời điểm bắt đầu/kết thúc.
- `assessment_events`: audit log các thao tác.
- `login_attempts`: hạn chế đăng nhập sai.

Tương thích bảng `controls`, `evidence`, `evaluations`, `compliance_rubrics` hiện có. Đã bổ sung trường gắn assessment/user vào evidence và evaluations. Bản giai đoạn 1 có **một đợt đánh giá doanh nghiệp mặc định**, tất cả user do admin tạo cùng tham gia đợt này. Nếu làm nhiều doanh nghiệp thật cần phân quyền tenant riêng và kiểm thử cách ly dữ liệu trước khi triển khai.

## 7. Các giới hạn kỹ thuật cần biết

- Job dùng `ThreadPoolExecutor` trong tiến trình API, max 2 jobs chạy song song. Sau restart job đang chạy được đánh dấu `FAILED` để có thể bấm chạy lại; không tự tiếp tục từ checkpoint.
- Chạy **một tiến trình Uvicorn** (`--workers 1`, mặc định) trong MVP. Nếu mở nhiều API instance, cần worker queue bền vững và cơ chế lease/retry.
- Giao diện polling mỗi 3 giây thay cho WebSocket ở phiên bản đầu.
- Chống prompt injection hiện là lớp bảo vệ prototype, chưa đạt đánh giá an toàn production.
- Công cụ thu thập evidence kỹ thuật và môi trường lab doanh nghiệp đầy đủ là giai đoạn 2.
- Không sử dụng kết quả này để tuyên bố doanh nghiệp được chứng nhận ISO/IEC 27001.

## 8. API chính

| Endpoint | Chức năng |
|---|---|
| `POST /api/auth/login` | Đăng nhập, nhận token |
| `POST /api/team/users` | Admin tạo thành viên |
| `GET /api/assessments` | Đợt đánh giá được tham gia |
| `GET /api/assessments/{id}/progress` | Bảng 56 controls chung |
| `POST /api/assessments/{id}/controls/A.6.1/run` | Khoá control, khởi chạy Agent |
| `GET /api/jobs/{job_id}` | Kiểm tra trạng thái job |
| `POST /api/assessments/{id}/controls/A.6.1/evidence` | Nạp bằng chứng gắn assessment |
| `GET /api/assessments/{id}/controls/A.6.1/history` | Lịch sử kết quả |
| `POST /api/assessments/{id}/controls/A.6.1/review` | Admin review khi cần |

Các endpoint dữ liệu yêu cầu `Authorization: Bearer <token>`.

## 9. Kiểm thử tự động

Trong môi trường Python đã cài dependencies:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q tests
```

Các bài kiểm thử gồm parser PDF/DOCX, authentication bắt buộc, PBKDF2 salt, bằng chứng ID không hợp lệ, và luồng bấm tạo Agent job (dùng mock, không cần gọi mô hình thật). Để thử **hai máy chạy đồng thời trên PostgreSQL**, làm thủ công theo bước 4; phần này chưa có integration test DB thực trong bản ZIP.
