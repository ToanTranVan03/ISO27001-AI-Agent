# Trạng thái triển khai

| Giai đoạn | Trạng thái | Phạm vi |
| --- | --- | --- |
| 01 | PASS | Khung dự án, cấu hình, health, Compose và kiểm thử |
| 02 | PASS | Danh mục, rubric và chính sách |
| 03 | PASS | PostgreSQL, migrations và phân quyền |
| 04 | PASS | Bộ sinh dữ liệu và mô phỏng |
| 05 | IN_PROGRESS | Tiêm lỗi và nhãn chuẩn cho benchmark |
| 06 | IN_PROGRESS | API đánh giá nghiệp vụ |
| 07 | PASS | Công cụ và cổng chính sách |
| 08 | BLOCKED | RAG và nguồn tham chiếu |
| 09 | IN_PROGRESS | Đồ thị tác nhân |
| 10 | IN_PROGRESS | Đánh giá con người, phần cứng và phần mềm |
| 11 | IN_PROGRESS | Phê duyệt, thực thi và xác minh |
| 12 | BLOCKED | Lab máy ảo cô lập |
| 13 | IN_PROGRESS | Dashboard và báo cáo |
| 14 | IN_PROGRESS | Benchmark M1–M4 |
| 15 | IN_PROGRESS | Đóng gói và nghiệm thu |

## Phase 01

Khởi tạo dự án mới trong thư mục đích theo xác nhận của người dùng. Ngày kiểm chứng 2026-11-26, cây làm việc mới trên nền Git 7ee5918, chưa tạo commit mới.

- Python 3.11.9. Pip tạo lockfile, cài từ lockfile và cài dự án dạng editable thành công.
- python -m ruff check . thành công. python -m mypy kiểm tra 4 tệp thành công.
- python -m pytest -q có 4 bài kiểm thử đạt. Starlette cảnh báo về TestClient với httpx.
- Uvicorn phục vụ HTTP thật trên loopback. GET /health trả {"status":"ok","execution_mode":"SIMULATION"}.
- docker compose config --quiet hợp lệ. docker compose up -d --wait db báo Healthy. Truy vấn pg_available_extensions thành công và có mục vector.
- Tiếp theo là Phase 02. Kích hoạt extension, migration và kiểm thử cô lập tenant thuộc Phase 03.

## Phase 02

Ngày kiểm chứng 2026-11-26, cây làm việc chưa commit.

- python -m compliance_ai.cli validate-catalog xác nhận 26 mã, 26 tiêu chí, 20 họ kịch bản và 3 chính sách mẫu.
- python -m ruff check . và python -m mypy thành công. python -m pytest -q có 9 bài kiểm thử đạt.
- Kiểm thử dữ liệu thiếu, mâu thuẫn, cũ hoặc đang chờ, ngưỡng chính sách, lý do loại trừ và điểm không đếm trùng.
- Nguồn là research_rubric, chờ đối chiếu tài liệu được cấp phép và chuyên gia. Phase này có ánh xạ kịch bản, rubric mẫu và quy tắc nền. Bộ sinh và luồng phỏng vấn sẽ được kiểm thử ở các lượt sau.
- Tiếp theo là Phase 03.

## Phase 03

Ngày kiểm chứng 2026-11-26, cây làm việc chưa commit. PostgreSQL 16.16 và extension vector 0.8.7 chạy trên Docker Compose cục bộ.

- python -m compliance_ai.cli configure-db-roles và python -m alembic upgrade head thành công. python -m alembic current trả 0001_tenant_foundation (head).
- Cơ sở compliance_ai_test riêng chạy chuỗi upgrade head, downgrade base và upgrade head thành công. Kiểm tra rollback chỉ chạy trên cơ sở test.
- python -m pytest -q với đủ ba TEST_*_DATABASE_URL có 17 bài kiểm thử đạt và không có skip. Bài tích hợp kiểm tra tenant và vai trò, quyền chỉ xem hồ sơ của mình, thu hồi membership, phiên bản cập nhật và audit, cách ly vector, kho benchmark chỉ đọc và seed chạy lặp.
- python -m ruff check ., python -m mypy và python -m pip check thành công. Uvicorn qua HTTP trả {"status":"ok","execution_mode":"SIMULATION"} tại /ready và công bố endpoint xác thực trong OpenAPI. Kiểm tra Git xác nhận .env và .venv bị bỏ qua.
- Mô hình hiện bao phủ danh tính, tenant, nhân viên, chính sách, SoA, bằng chứng, đoạn vector, audit và kho benchmark. Các bảng vận hành của NV015, đào tạo, phiên đánh giá và hành động sẽ được tạo với lát cắt dọc ở lượt 2.
- Cấu hình VS Code đã được thêm. Lệnh Uvicorn tương ứng được kiểm chứng trên terminal. Chưa chạy F5 trực tiếp trong IDE.
- AC01 có bằng chứng khởi động và migration. AC03 đã xác thực danh mục nghiên cứu, phần đối chiếu nguồn cấp phép và chuyên gia đang chờ. AC04 đã kiểm tra phạm vi API và truy vấn dữ liệu của Lượt 1. Cần bổ sung kiểm thử cách ly khi có API worker, báo cáo và RAG đầy đủ.

## Phase 04

PASS trong phạm vi bộ sinh và mô phỏng. `seed-demo --seed 42` tạo ABC 50 nhân viên, 165 ca. `generate --companies 25 --seed 2026 --split test` chạy hai lần với cùng manifest, 1.650 ca và SHA-256 b1c58f515651227ad60853b8cfeb1b5ea7b28df5cc5a33345a11dfdd9f9c7ca9. Hai bài kiểm thử simulator qua. Cơ sở đi từ revision 0001 lên 0002.

## Phase 05

20 họ kịch bản có ca sạch, lỗi, thiếu, mâu thuẫn và ngoài phạm vi. Nhãn được lưu dưới schema evaluator riêng. Kiểm thử rubric đối chiếu nhãn của bộ dữ liệu mô phỏng. Cần bổ sung bộ trường hợp giữ lại theo thời gian, độ trễ và đánh giá chuyên gia độc lập.

## Phase 06

API đánh giá và báo cáo được lưu trong PostgreSQL. Revision 0003 áp dụng thành công. Bài kiểm thử đầu cuối kiểm tra yêu cầu lặp, đoán ID tenant khác và xuất báo cáo. Phạm vi hiện đồng bộ và có giới hạn. Hàng đợi worker, checkpoint khôi phục và toàn bộ API quản trị còn thiếu.

## Phase 07

Revision 0004 cung cấp sổ hành động và quyền ghi riêng. Danh sách công cụ mô phỏng chỉ gồm thao tác định sẵn cho tài khoản, quyền, tài sản, đào tạo, khóa màn hình và bản vá. Bài kiểm thử đầu cuối chứng minh chặn thực thi khi chưa duyệt, hash không khớp hoặc revision cũ.

## Phase 08

Có nhập tệp UTF-8 có metadata và xác nhận quyền, truy vấn pgvector lọc tenant và mã kiểm soát. Tests `test_rag.py` và kiểm thử vector trên PostgreSQL qua. Truy xuất dùng vector băm từ vựng cục bộ. Chưa có tài liệu ISO được cấp phép để đối chiếu. Đánh giá hiện dựa vào rubric nghiên cứu. Nội dung nhập chỉ được trả dưới dạng tham chiếu.

Đã tích hợp dẫn nguồn vào báo cáo đánh giá. PostgreSQL trả tối đa ba đoạn theo đúng doanh nghiệp và mã tham chiếu. Báo cáo lưu mã đoạn, nguồn và hash nội dung. Dashboard đọc lại đúng đoạn theo quyền và hash. Mã thiếu tài liệu hiển thị chế độ rubric nghiên cứu. Phần tài liệu chuẩn vẫn cần nguồn được cấp quyền.

## Phase 09

LangGraph đánh giá chạy lần lượt observe → people → hardware → software → report và lưu workflow_steps cùng báo cáo. Graph phỏng vấn có câu hỏi bổ sung hữu hạn và tùy chọn chấm ngữ nghĩa bằng Ollama trên máy cục bộ, kiểm tra schema và trích dẫn phải có trong câu trả lời. Không lưu nguyên văn câu trả lời, tắt tracing ngoài cho hai graph. Test kiểm tra chấm theo cụm từ, ngữ nghĩa với provider giả lập, trích dẫn bịa, chỉ thị giả, timeout và dịch vụ lỗi. Thiếu supervisor LLM tự chọn tool suốt chu trình, checkpoint graph lưu bền và khôi phục worker.

## Phase 10

165 ca ABC bao phủ cả 20 họ kịch bản và 26 tiêu chí theo danh mục. Luồng trạng thái nguồn tích hợp ưu tiên NV015, đào tạo, khóa màn hình và bản vá. Các tình huống khác dùng quan sát fixture và thẩm định thủ công theo ma trận. Chưa đầy đủ kết nối nghiệp vụ và bộ chấm ngữ nghĩa của mọi tiêu chí.

## Phase 11

Revision 0005 lưu bằng chứng từ đúng nhân viên tự nộp. Revision 0006 thêm trạng thái ROLLED_BACK. Kịch bản đầu cuối chạy phê duyệt hai vai, chống sửa kế hoạch, chống lặp, sai revision, đọc nguồn mới, chờ trả thiết bị, giao bài và kiểm tra lại. Phân cấp low/medium/high; bản vá và cấu hình mô phỏng là medium, vẫn cần admin độc lập. Snapshot chỉ giữ trường bị thay đổi; API và dashboard hỗ trợ khôi phục bởi người duyệt, kiểm tra hash, revision, chính sách và đối chiếu sau khôi phục. Test kiểm tra từ chối sai role/hash, snapshot cũ, khôi phục thành công, gửi lặp và đánh giá mới sau khôi phục. Chưa có kịch bản kiểm thử hết hạn riêng hoặc rollback trên VM thật.

Phần S02 trong Phase 07/10/11 bổ sung hành động `request_mfa_enrollment`, thông báo cho đúng nhân viên và lệnh `demo-mfa-observe` cho người vận hành nguồn định danh mô phỏng. Đọc riêng hai trạng thái đăng ký và cưỡng chế, yêu cầu sự kiện đúng mã hành động để xác minh. Khi chỉ thiếu cưỡng chế, người vận hành cập nhật nguồn định danh. Migration `0008_mfa_notice` giới hạn dữ liệu nhân viên nhìn thấy ở mã yêu cầu của mình. Kiểm thử PostgreSQL bao phủ tạo yêu cầu, trạng thái chờ, phạm vi tenant, revision cũ, dữ liệu thiếu, đạt một phần, xác minh và tái phát sau khi đóng. Hướng dẫn chạy thử ở [hướng dẫn trình diễn](USER_GUIDE.md).

**Bổ sung H06 cho Phase 07/10/11.** Migration `0007_nda_acknowledgement` hỗ trợ đối chiếu chính sách và ghi sự kiện xác nhận của nhân viên. Luồng SC-H05 gồm lập yêu cầu, nhân viên đọc và xác nhận văn bản mô phỏng, đọc lại biên nhận và đánh giá H06. Kiểm thử PostgreSQL bao phủ dữ liệu cũ, hash sai, revision cũ, sai vai trò hoặc tenant, gửi lặp, trạng thái chờ và xác minh thành công. Chạy `scripts/test-postgres.ps1` đạt 30 bài, Ruff đạt và mypy đạt trên 40 tệp. Hướng dẫn chạy thử có trong [hướng dẫn trình diễn](USER_GUIDE.md).

Kiểm tra S02 ngày 2026-11-26 đạt 30 bài PostgreSQL, Ruff và mypy trên 42 tệp. Docker đã chạy migration 0008, API và Streamlit đều trả trạng thái sẵn sàng.

Phần D02 của Phase 07/10/11 dùng migration `0009_asset_receipts` và lệnh `demo-asset-receive` để ghi nhận sự kiện trả laptop NV015 từ kho mô phỏng ABC. Lần đánh giá và xác minh đều đối chiếu người, thiết bị, phiếu, mã biên nhận và trạng thái người giữ. Biên nhận không khớp cần đối soát. Gửi lại cùng giao nhận giữ nguyên mã và revision. Đã kiểm thử hai trạng thái chờ/hoàn tất, xung đột dữ liệu, sai phạm vi, revision cũ, quyền đọc/ghi và bảo toàn báo cáo trước bàn giao. Lệnh `scripts/test-postgres.ps1` đạt 30 bài và mypy đạt trên 44 tệp. [Hướng dẫn trình diễn](USER_GUIDE.md)

Hạn trả tài sản D02 lấy từ chính sách của doanh nghiệp. Lịch mô phỏng tính từ thứ Hai đến thứ Sáu theo UTC+7 và chưa tính ngày lễ. Bài kiểm thử bao phủ qua cuối tuần, giao ngày, thiếu biên nhận, quá hạn và trả trễ. API chạy thử và bước thực thi dùng chung cổng kiểm tra. Kiểm thử phê duyệt bao phủ hết hạn kế hoạch, hết hạn duyệt, tài khoản được bảo vệ, tự duyệt, revision cũ và trường lệnh ngoài schema.

## Phase 12

`lab-plan --config configs/lab.example.yaml --dry-run` trả BLOCKED, connected=false, executed=false. PowerShell parser xác thực cú pháp hai script. Điều kiện còn thiếu là VM Windows cô lập có snapshot, tài khoản thử nghiệm và phê duyệt thao tác cụ thể. Chưa thực hiện kết nối, thay đổi hoặc đọc độc lập trên VM.

## Phase 13

Dashboard Streamlit lấy dữ liệu từ API, có đánh giá, kế hoạch, phê duyệt, xác minh, phỏng vấn và báo cáo JSON/CSV. AppTest kiểm tra màn hình đăng nhập. Bài tích hợp chạy Uvicorn thật, đăng nhập auditor qua dashboard và xác nhận chỉ thấy tenant được cấp quyền. Kiểm tra HTTP Streamlit trên Docker Compose trả ok. Chưa có kiểm thử trình duyệt xuyên qua tác vụ và chưa có trang benchmark chuyên biệt.

## Phase 14

- MOCK_TEST_ONLY, 25 doanh nghiệp, 1.650 ca. Báo cáo `artifacts/benchmarks/20881c05-edd5-4118-b64b-3c4b0423a02d`.
- Ollama qwen2.5:1.5b, 25 doanh nghiệp, 200 ca, 21 lượt gọi hợp lệ, 4 lượt gọi lỗi. Báo cáo `artifacts/benchmarks/4bedcb45-b9a1-4dc6-ad84-3dbe3df7f9cc`.
- M1–M4 hiện đo phát hiện có cấu trúc. M2/M3 dùng chung dự đoán. Chưa đo hành động và xác minh theo từng phương pháp, chi phí hay chất lượng trích dẫn. Không suy rộng kết quả tổng hợp.

## Phase 15

Lockfile được cài trên Windows và trong ảnh Linux. Ruff, mypy và pip check qua. Đợt bổ sung 2026-11-26: `scripts/test-postgres.ps1` chạy 30 bài đạt, không skip; mypy kiểm tra 38 tệp. Xem [nghiệm thu AC01–AC15](ACCEPTANCE.md) cho các mục còn mở.

## Đối chiếu đề cương và góp ý — 2026-11-26

- Mở rộng [ma trận](CONTROL_TRACEABILITY.md) thành 26 hàng có công cụ đọc, dữ liệu, độ mới, điều kiện đạt, hành động/rủi ro, xác minh và ánh xạ 20 họ kịch bản; ghi rõ fixture, luồng mô phỏng và thẩm định thủ công.
- [Thực nghiệm](EXPERIMENT.md) bổ sung RQ1–RQ5, đối chứng công bằng, manifest cần lưu, phân biệt SoA/Gap/Remediation trong ma trận và thiết kế nhóm tự nguyện tùy điều kiện. Đây là phương pháp cần thực hiện, không phải số liệu mới.
- Smoke Ollama thật `qwen2.5:3b` trên hai câu trả lời tổng hợp: câu diễn đạt khác cụm từ chỉ được model nhận safe_response (40 điểm, FOLLOWUP); câu chưa biết cách xử lý chuyển HUMAN_REVIEW. Chứng minh đường gọi hoạt động, chưa chứng minh độ chính xác; model còn bỏ sót ý. Không chỉnh đáp án kỳ vọng để đạt kết quả đẹp.
- Docker có thể truy cập Ollama trên cùng máy qua host.docker.internal. Chấm ngữ nghĩa vẫn tắt mặc định và chỉ dùng khi cấu hình model cùng chọn trên màn hình. Không thay cấu hình mạng/firewall hệ điều hành.
- Xem [đối chiếu và phần còn thiếu](PLAN_ALIGNMENT.md). Chưa hoàn thành toàn bộ đề cương.
- Kiểm tra ma trận bằng mã: khớp đủ 26 ID, công cụ đọc, trường bằng chứng bắt buộc và 20 họ kịch bản trong catalog.
- Build/recreate API và UI bằng Compose thành công. HTTP `/ready` trả `{"status":"ok","execution_mode":"SIMULATION"}`, Streamlit `/_stcore/health` trả `ok`; OpenAPI có `/actions/{action_id}/rollback`. Cơ sở cục bộ ở migration `0006_action_recovery (head)`.
