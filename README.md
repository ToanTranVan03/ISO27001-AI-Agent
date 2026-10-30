# HiveFive — ISO 27001 People Simulation

Bản mô phỏng doanh nghiệp 50 nhân sự, 4 phòng ban, 200 tài khoản phần mềm và
50 laptop, có mô hình tòa nhà văn phòng 3D tương tác. Trọng tâm là con người A.6.1–A.6.8, kết nối với quyền truy cập
phần mềm và thiết bị được cấp. Toàn bộ hồ sơ là giả lập.

## Khởi động trên Windows

```powershell
cd D:\ISO27001-AI-Agent
py -3.11 -m pip install -r requirements.txt
py -3.11 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Mở [giao diện mô phỏng](http://127.0.0.1:8000/simulation).
API có tài liệu tại [Swagger](http://127.0.0.1:8000/docs).
Dùng `py -3.11` nếu lệnh `python` bị chuyển đến Microsoft Store.

## Luồng chính: bạn thao tác, Agent tự phát hiện

Màn hình chính hiện là doanh nghiệp vận hành theo sự kiện. Chọn nhân sự
ngay trong mô hình hoặc ở bảng bên cạnh, chọn nghiệp vụ rồi **Ghi nhận thay
đổi**. Không có bước bấm nút chạy kiểm tra. Ví dụ ghi nhận HF-025 nghỉ việc
sẽ tự phát hiện A.6.5 do còn tài khoản và laptop chưa bàn giao. Ghi nhận
thu hồi tài khoản và nhận lại laptop sẽ tự đối chiếu lại.

Quy tắc phát hiện xuất hiện ngay. Worker máy chủ tự chạy Agent Ollama để
kiểm tra sâu, cập nhật công việc và xác minh. UI đọc kết quả mỗi hai giây;
worker vẫn chạy khi đóng tab, miễn máy chủ và Ollama còn hoạt động. Khi AI
lỗi, trạng thái ghi rõ chưa hoàn tất và giữ phát hiện theo quy tắc; không
chuyển giả thành AI thành công. Thay đổi mới được xử lý tiếp tự động.

Nguồn sống và nhật ký trước/sau lưu riêng tại `data/live/agent_runs.sqlite3`.
Chạy Uvicorn với một worker như lệnh trên. API nghiệp vụ:

- `GET /api/live`: trạng thái, phiên bản, phát hiện, tiến độ công cụ và báo cáo.
- `POST /api/live/events`: `{"person_id":"HF-025","action":"terminate"}`.
  Nghiệp vụ khắc phục tương ứng: `recover_access`. Danh sách thao tác trả
  trong `actions` của API trạng thái.

Thiết kế phục vụ báo cáo và bảo vệ đồ án tại
[`docs/THIET-KE-DO-AN.md`](docs/THIET-KE-DO-AN.md).

## Luồng nhận mục tiêu trước đây (API nghiên cứu)

Endpoint nhận mục tiêu được giữ để nghiên cứu và so sánh, đã thay bằng luồng
sự kiện trên giao diện chính. Trong chế độ **AI chọn công cụ**, Ollama `qwen2.5:7b` chọn hành
động tiếp theo từ các công cụ khả dụng dựa trên mục tiêu và quan sát vừa nhận.
Phạm vi công cụ cố định cho kiểm tra con người; đây là agent chuyên biệt.
Model không tự sinh bộ đánh giá cho các yêu cầu ngoài phạm vi.

Agent đọc nhân sự và tài sản, đánh giá A.6, tự mở kiểm tra sâu nghỉ việc hoặc
làm từ xa khi tìm thấy vấn đề, đối chiếu phạm vi, lưu việc đề xuất và xác minh
báo cáo. Nhật ký truyền trực tiếp bằng NDJSON, không tạo tiến độ giả. Chế độ
**Workflow quy tắc** dùng thứ tự cố định, được ghi rõ và không gọi là AI.
Lỗi model dừng lần chạy, không âm thầm chuyển sang workflow.

Lịch sử và công việc lưu tại `data/agent_runs.sqlite3`. Mỗi kiểm soát có mã
công việc ổn định nên chạy lại không tạo trùng. Nguồn mặc định là snapshot
giả lập có nhiều vấn đề cùng lúc. Có thể đặt snapshot thay thế tại
`data/enterprise_snapshot.json` theo cấu trúc `build_enterprise()` và bắt buộc
`synthetic: true`. Lần chạy mới đọc lại nguồn; công việc chỉ được đánh dấu
hết phát hiện trong mô phỏng khi bằng chứng mới đạt quy tắc. Agent không sửa
nguồn để tự chứng minh đã khắc phục, không gửi công việc ra ngoài.

Đã có evaluator cho **8/56 kiểm soát thuộc phạm vi đồ án**; 48 A.7/A.8 hiện
chỉ có danh mục và yêu cầu bằng chứng. 56 không phải tổng số kiểm soát của
ISO/IEC 27001:2022 (Phụ lục A có 93). Không suy ra chứng nhận ISO từ kết quả.

- `POST /api/agent/run`: `{"goal":"Kiểm tra HiveFive","mode":"ai"}`;
  phản hồi `application/x-ndjson`: start, action, tool_result, complete/error.
- `GET /api/agent/history`: 10 lần chạy gần nhất, có cả thất bại.
- `GET /api/agent/latest`: báo cáo hoàn tất gần nhất hoặc `null`.

## Khám phá tòa nhà 3D

Mô hình là một tòa nhà ba tầng trên Trái Đất: lễ tân, khu HR/đào tạo, phòng
máy chủ ở tầng 1; IT và Ops ở tầng 2; Finance và Sales ở tầng 3. Có sân vườn,
kiến trúc kính và vườn mái. Phong cách nhân vật và góc nhìn tham khảo video
người dùng cung cấp, theo yêu cầu giữ bối cảnh một tòa nhà trên Trái Đất.

- Mặc định là một phòng nhìn xiên kiểu game văn phòng, không xếp chồng các tầng.
- Bấm chọn nhân vật rồi bấm vị trí trống trên sàn: nhân vật tìm đường vòng
  qua bàn. Có thể dùng **WASD / phím mũi tên** khi vùng 3D có focus, hoặc
  giữ các nút mũi tên trên màn hình. Nhân vật không đi xuyên bàn hoặc ra khỏi phòng.
- Kéo chuột để xoay, cuộn để phóng to. **Xem tòa nhà** mở mô hình kiến trúc;
  **Về phòng diễn tập** trở lại khu vực có sự việc.
- **Đổi phòng / góc nhìn** chứa các phòng ban và tùy chọn camera ít dùng.
- Bấm **Xem hồ sơ nhân sự** trong thẻ nhân vật để mở chi tiết NDA, đào tạo,
  tài khoản HR/Email/VPN/Nghiệp vụ và laptop. Danh sách 50 người mặc định thu gọn.
- Chạy tình huống sẽ làm nổi bật người cần xử lý, gắn nhãn công việc và
  tự đưa camera tới phòng ban liên quan.
- Trình duyệt cần WebGL 2. Nếu không khởi tạo được 3D, phần tình huống và
  bảng nhân sự vẫn dùng được. Chuyển động nhẹ tôn trọng tùy chọn giảm chuyển động.

Three.js **0.170.0** và OrbitControls được lưu tại `backend/static/vendor/`,
nguồn `https://unpkg.com/three@0.170.0/`, có `THREE-LICENSE.txt` (MIT).
Ứng dụng không cần CDN để hiển thị 3D và không cần npm để khởi động.

Các skill đã áp dụng và minh chứng cho báo cáo đồ án được ghi tại
[`docs/SKILLS-APPLIED.md`](docs/SKILLS-APPLIED.md).

Chọn tình huống rồi bấm **Bắt đầu diễn tập**, xem lần lượt ba bước:
**Sự việc → Agent kiểm tra → Cách xử lý**. Chỉ các kiểm soát cần xử lý được
mở trong kết quả; các kiểm soát còn lại và JSON kỹ thuật nằm trong mục thu gọn.
Di chuyển nhân vật không tự hoàn thành đào tạo, ký NDA hoặc thay đổi kết quả ISO.
Để dùng Ollama, mở **Tùy chọn AI** trước khi bắt đầu.

## Hai chế độ diễn tập thủ công

- **Quy tắc**: chạy độc lập với model và không cần Docker. Đánh giá bằng
  dữ liệu hồ sơ; không dùng nhãn `expected_status` của benchmark cũ.
- **Quy tắc + Ollama giải thích**: kiểm tra như trên, sau đó gọi
  `http://127.0.0.1:11434/api/chat` với model `qwen2.5:7b` để viết giải thích.
  Model không được ghi đè trạng thái kiểm soát. Cần Ollama đang chạy và model
  đã được tải trước. Timeout 60 giây; khi lỗi trả HTTP 503 và thông báo có thể
  chọn Quy tắc để chạy lại. Không âm thầm giả lập phản hồi AI.

Luồng mô phỏng mới dùng các bước Python trong `agent_core/simulation.py`.
Luồng LangGraph/Ollama cũ trong `agent_core/graph_builder.py` được giữ qua
`POST /api/evaluate`; chỉ tải các dependency benchmark khi gọi API cũ.

## Tình huống

| Tình huống | Tác động mô phỏng | Trọng tâm |
|---|---|---|
| Doanh nghiệp mẫu | Hồ sơ đầy đủ theo quy tắc nội bộ | A.6.1–A.6.8 |
| Nhân viên mới | Thiếu cam kết lao động và NDA dù đã có tài khoản | A.6.2, A.6.6 |
| Đào tạo bỏ sót | 8 nhân viên Sales chưa hoàn tất | A.6.3 |
| Email đáng ngờ | Một nhân viên chưa biết báo cáo và chưa báo cáo sự kiện diễn tập | A.6.8 |
| Nghỉ việc | Còn tài khoản mở và laptop chưa trả | A.6.5 |
| Làm từ xa | Laptop chưa mã hóa, VPN thiếu MFA | A.6.7 |

## API và kiểm thử

- `GET /api/simulation`: doanh nghiệp gốc và danh mục tình huống.
- `POST /api/simulation/run`: ví dụ body
  `{"scenario_id":"training","mode":"rules"}`.
- `GET /`: thông báo backend cũ, giữ dạng JSON.
- `POST /api/evaluate`: API kiểm toán cũ; không đổi hợp đồng phản hồi.

```powershell
py -3.11 -m unittest discover -s tests -v
node --test tests/navigation.test.mjs
```

Kiểm thử trình duyệt tùy chọn dùng Playwright có sẵn trong môi trường, server
đang chạy tại cổng 8000:

```powershell
node tests/browser_smoke.cjs
```

Nếu Playwright không thuộc đường dẫn module Node hiện tại, đặt `NODE_PATH`
đến thư mục `node_modules` đã cài Playwright trước khi chạy. Thư viện này chỉ
dùng để kiểm thử, không cần cho ứng dụng. Kiểm thử API cần `httpx` (dependency
phát triển được liệt kê trong `requirements-dev.txt`).

## Giới hạn

Đây là công cụ diễn tập theo tập tiêu chí đơn giản hóa của dự án, không phải
đánh giá chứng nhận. Các trạng thái “đạt” chỉ nói về bằng chứng và các quy tắc
đang mô phỏng, không xác nhận mọi yêu cầu trong `docs/compliance_rubrics.json`
hoặc toàn bộ ISO 27001. Thiếu bằng chứng trả `Insufficient Evidence`.
SHA-256 dùng đối chiếu nội dung trong báo cáo, không chứng minh nguồn gốc hồ sơ.

Diễn tập thủ công tạo dữ liệu mới mỗi lần; luồng sống lưu snapshot, sự kiện và
công việc trong SQLite. Chưa có
đăng nhập nhiều người dùng hoặc tích hợp HR/IAM thật; server chỉ bind localhost.
Không gửi email, tự kỷ luật, khóa tài khoản hoặc thay đổi thiết bị thật.
Docker lab cũ là tùy chọn riêng, không cần để chạy giao diện mô phỏng.

## Hồ sơ sự việc và thực nghiệm học thuật

Chọn người trong 3D hoặc danh sách để xem ngay tài khoản, thiết bị và kiểm soát
liên quan trên cảnh. **Hồ sơ sự việc** bên dưới hiển thị thay đổi trước/sau,
vòng đời xử lý và bằng chứng theo từng A.6. Trạng thái thiếu dữ liệu được giữ
là **Chưa xác minh**; thử nghiệp vụ `training_unverified`, sau đó ghi nhận khắc
phục để worker tự tái kiểm tra. Nút khắc phục chỉ cập nhật dữ liệu mô phỏng.

- `GET /api/live/report`: tải JSON snapshot hiện tại, sự kiện gần nhất và báo cáo.
  So sánh `revision`, `trigger_revision` và `snapshot_hash` trước khi dùng báo cáo
  AI, vì báo cáo cũ có thể thuộc snapshot trước khi thay đổi.
- `GET /api/research`: kết quả thực nghiệm đã lưu, không khởi chạy model.
- Mục **Thực nghiệm học thuật** hiển thị số ca đã hoàn tất và khớp toàn bộ nhãn.

Tái lập (không sửa dữ liệu sống):

```powershell
py -3.11 -m agent_core.research_benchmark --ai
```

37 ca tổng hợp có nhãn viết riêng, bao phủ đúng/sai/thiếu dữ liệu của tám kiểm
soát, tài sản khi nghỉ việc, làm từ xa, khắc phục, đào tạo hết hạn, mâu thuẫn
HR/LMS, đổi vai trò và ngoại lệ giữ tài khoản. Nhãn không đưa
vào model. Kết quả ở `docs/research-results.json` gồm snapshot hash, quyết định
công cụ, thời gian và lỗi từng lần. Đây là tập chấp nhận tổng hợp tự xây dựng,
chưa là đánh giá mù hoặc dữ liệu doanh nghiệp độc lập. Ba chế độ cùng evaluator;
không dùng kết quả khớp nhãn để tuyên bố LLM chính xác hơn luật.

So sánh công bằng cùng 8 ca, lặp 3 lần mỗi chế độ (Ollama thật):

```powershell
py -3.11 -m agent_core.research_benchmark --paired --repeats 3
```

Đã chạy 72 lượt, ba chế độ đều hoàn tất/khớp nhãn 24/24; snapshot và số lượt
được kiểm tra cân bằng. JSON có mean/median/độ lệch chuẩn theo chế độ và từng
ca. Workflow hiện nhanh hơn AI trên tập này; chưa có bằng chứng LLM tốt hơn.

Nghiệp vụ mới trong dropdown: đào tạo hết hạn, HR/LMS mâu thuẫn, chuyển vai
trò/rà soát quyền, đề nghị/ghi nhận quản lý duyệt ngoại lệ giữ HR. Ngoại lệ
chỉ có hiệu lực với đúng tài khoản, phạm vi, người duyệt, lý do và thời hạn.
Agent không tự phê duyệt. **Chuyển ngày mô phỏng** tăng ngày trong snapshot,
tự phát hiện thời hạn quá hạn mà không cần sửa tài khoản. Ngày ban đầu là
2026-10-30; đây là đồng hồ mô phỏng, không phải scheduler thời gian thực.

Phạm vi rủi ro/SoA: `docs/SOA-MO-PHONG.md`. Kịch bản bảo vệ và mẫu khảo sát:
`docs/BAO-VE-VA-KHAO-SAT.md`. Chưa có người tham gia hay nhãn chuyên gia thật.

Phương pháp, câu hỏi nghiên cứu và căn cứ quy tắc xem
`docs/NGHIEN-CUU-VA-DANH-GIA.md`.
