# Chấm thật 18 control A.8 — tài khoản Văn Tú

Nhánh bàn giao: `Tu/Tuan5`. Người chấm: **Lê Đoàn Văn Tú**, username **`vantu`**, role **`assessor`**.

Người chấm tự đọc bằng chứng gốc và rubric, tự đưa ra kết luận và lý do trước khi xem kết quả Agent, đáp án thiết kế hoặc nhãn của Khoa. Chỉ hướng dẫn thao tác không tạo ra nhãn con người; nhãn có AI hỗ trợ phải khai `ai_assisted`. Tiến độ giả lập/luyện tập được lưu riêng.

## 1. Chuẩn bị trên máy Windows

Tại thư mục dự án (máy hiện tại: `D:\ISO27001-AI-Agent`):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt pytest
npm.cmd ci --prefix frontend-react
npm.cmd run build --prefix frontend-react
```

Tạo `.env` từ `.env.example` nếu chưa có. Đặt mật khẩu riêng cho PostgreSQL và admin, bảo đảm `DATABASE_URL` khớp mật khẩu/cổng PostgreSQL. Giữ `.env` ở máy local; không commit mật khẩu. Nếu cổng 5432 đã dùng, đặt `POSTGRES_PORT=5433` và sửa cổng trong `DATABASE_URL`.

Mở Docker Desktop, chờ Engine hoạt động rồi chạy:

```powershell
docker compose -f docker-compose.enterprise-lab.yml up -d postgres
docker compose -f docker-compose.a8.yml up -d --build
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Để đánh giá bằng LLM, chạy Ollama với model khớp `OLLAMA_MODEL` trong `.env` (mặc định `qwen2.5:7b`). Lab Docker phục vụ nguồn live; replay file dùng nguồn lịch sử trong repository và không xác nhận hiện trạng hệ thống.

## 2. Chuẩn bị tài khoản Văn Tú

Sau khi backend khởi động và tạo schema, mở terminal khác:

```powershell
.\.venv\Scripts\python.exe scripts/seed_team_accounts.py --user tu
```

Nếu `vantu` đã tồn tại, script giữ nguyên mật khẩu và gắn tài khoản vào đợt đánh giá. Nếu chưa có, script hỏi mật khẩu mới ít nhất 12 ký tự và yêu cầu nhập lại. Script không reset admin/Khoa, không xóa phiên đăng nhập và không tạo nhãn chấm. Tài khoản trong database máy khác không tự có sau khi clone GitHub.

## 3. Người điều phối tạo lượt; Văn Tú chấm trên web

1. Người điều phối đăng nhập admin tại `http://127.0.0.1:8000`, chọn đợt đánh giá → **Thực nghiệm 18 A.8**. Tạo lượt bằng nguồn/engine đã thống nhất và chờ hoàn tất. Muốn đối chiếu với Agent LLM thì chọn engine LLM; baseline luật là một kết quả riêng.
2. Người điều phối cung cấp **run-id**. Văn Tú và Khoa chấm cùng lượt để dùng cùng snapshot/rubric. Người chấm không dùng tài khoản admin để xem trước kết quả.
3. Văn Tú đăng nhập `vantu`, mở đúng lượt. Kiểm tra thông báo **Gói đánh giá mù**. Lượt cũ không hỗ trợ giao thức hiện hành cần người điều phối tạo lại.
4. Với từng control, đọc rubric, các artifact cấu hình/log/probe, nguồn và thời điểm. Tự chọn kết luận và nhập lý do viện dẫn quan sát cụ thể. Không mở kho đáp án hoặc nhờ AI chọn kết luận nếu muốn đối chiếu tự chấm.
5. Khai trung thực mức hỗ trợ và mức đã tiếp xúc đáp án. Nhãn AI hỗ trợ/đã xem trước vẫn được lưu nhưng không tính thành nhãn tự khai độc lập.
6. Bấm **Nộp và khóa kết luận**. Nhãn đã nộp không sửa; có thể quay lại tiếp tục các control chưa nộp. Sau đủ 18/18, ứng dụng mở bảng đối chiếu cho tài khoản đó.

## 4. Lựa chọn chấm tương tác qua CLI

CLI mặc định tài khoản Văn Tú, hỏi mật khẩu bằng nhập ẩn, chỉ đọc/nộp qua API bằng chính tài khoản assessor. CLI không đăng nhập admin, không tự tạo lượt, không có đáp án gợi ý hoặc lựa chọn mặc định cho kết luận, không hỗ trợ `--auto`/`review-all`.

```powershell
# Xem danh sách lượt bằng quyền của Văn Tú; thông tin được API làm mù.
.\.venv\Scripts\python.exe scripts/run_human_review.py --action status --user tu

# Thay UUID bên dưới bằng run-id do người điều phối cung cấp.
.\.venv\Scripts\python.exe scripts/run_human_review.py --user tu --run-id <UUID>
```

CLI hiển thị rubric và bằng chứng gốc trước khi yêu cầu kết luận/lý do. Người chấm phải khai mức hỗ trợ/tiếp xúc cho từng control, xem lại nội dung rồi gõ `NOP` để nộp. Gõ `q` để dừng; chạy lại cùng run-id để tiếp tục. Đáp án không được tự điền nếu nhập trống hoặc căn cứ quá ngắn. Nếu dùng API máy khác, thêm `--url http://<dia-chi>:8000`.

## 5. Báo cáo và giới hạn nghiệm thu

Sau khi nộp, admin xem tiến độ từng người, bảng đối chiếu từng control và bất đồng người–máy/người–người; xuất JSON/CSV và SoA dự thảo trong ứng dụng. Các nhãn phải khớp report/evidence hash. Tài khoản riêng hoặc tự khai độc lập chưa tự chứng minh trình độ chuyên gia hay độc lập ngoài nhóm.

Đủ nhãn là một điều kiện của duyệt SoA A.8; còn cần rubric đúng hash được duyệt, quyết định tính áp dụng và kế hoạch từng control, cùng người phụ trách thực sự phê duyệt. SoA là phạm vi lab giới hạn, không phải chứng nhận ISO hay tự phát sinh thẩm quyền pháp lý.

Không dùng nhãn tự sinh hoặc bài test phần mềm để đóng tiến độ chấm thật trong nhật ký tuần 5. Nếu đã dùng công cụ `--auto` ở phiên bản cũ, giữ lịch sử và loại nhãn đó khỏi kết quả đối chiếu người tự chấm; người điều phối chuẩn bị lượt/bộ nguồn phù hợp để chấm lại, không sửa nhãn khóa thành nhãn người thật.
