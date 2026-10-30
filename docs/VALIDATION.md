# Kiểm chứng bản mô phỏng HiveFive

Ngày thực hiện: 2026-10-30. Môi trường Windows, Python 3.11, Edge headless
qua Playwright, FastAPI chạy local cổng 8000.

## Kết quả

Bản chỉnh sửa theo phản hồi giao diện rối:

- 16 kiểm thử Python và 3 kiểm thử tìm đường JavaScript đạt.
- Kiểm thử tìm đường: vòng qua bàn, chặn mục tiêu trong bàn/ngoài biên và
  không tìm đường qua lối đã bị chắn hoàn toàn.
- Kiểm thử trình duyệt thật: mặc định một phòng, ba bước diễn tập, chỉ một
  kiểm soát đào tạo mở trong kết quả và 7 kiểm soát thu gọn; danh sách nhân sự
  không mở mặc định. Đã kiểm tra WASD làm đổi vị trí nhân vật và click sàn
  khởi động đường đi; số phát hiện ISO vẫn giữ nguyên sau khi nhân vật di chuyển.
- Bằng chứng tình huống đào tạo hiển thị 8 hồ sơ liên quan bằng ngôn ngữ
  dễ đọc, JSON đầy đủ nằm trong mục kỹ thuật. Bốn chiều rộng màn hình và
  khôi phục sau HTTP 503 đã được kiểm tra lại.
- Sửa MIME `.mjs` trên Windows; kiểm thử API xác nhận tệp tìm đường được
  phục vụ bằng JavaScript, không bị trình duyệt chặn module.

Kiểm chứng nền tảng bản đầu:

- 16 kiểm thử Python đạt: doanh nghiệp mẫu, sáu tình huống, liên kết người
  và tài sản, dữ liệu thiếu, tính độc lập của các lần chạy, API hợp lệ và lỗi,
  phản hồi Ollama không hợp lệ, lỗi kết nối và giữ hợp đồng API cũ.
- Trình duyệt thực tế đã khởi tạo WebGL và hiển thị tòa nhà 3D. Đã kiểm tra
  chọn nhân sự qua danh sách, chuyển phòng ban/tầng và bật/tắt nội thất.
- Tình huống đào tạo làm nổi bật đúng 8 nhân sự Sales trong bảng và cảnh 3D.
  Hồ sơ chọn `HF-050` hiển thị đào tạo chưa hoàn tất và laptop `LT-050`.
- Đã kiểm tra mở bằng chứng, lọc phòng ban, xử lý HTTP 503 và chạy lại bằng
  quy tắc; không có lỗi JavaScript qua sự kiện `pageerror`.
- Không có cuộn ngang toàn trang ở chiều rộng 320, 768, 1024 và 1440 pixel.
- Đã gọi Ollama `qwen2.5:7b` thật cho tình huống nghỉ việc, nhận đề xuất thu
  hồi quyền, nhận lại thiết bị và nhắc nghĩa vụ bảo mật với HR/IT phụ trách.
- JavaScript qua `node --check`; `git diff --check` không báo lỗi.

## Giới hạn kiểm chứng

Kiểm thử không chứng minh độ chính xác kiểm toán trên doanh nghiệp thật.
Chưa thực hiện đánh giá chứng nhận, kiểm thử tải nhiều người, kiểm thử trên
thiết bị cảm ứng thật hoặc kiểm toán WCAG đầy đủ. Hợp đồng API cũ được kiểm
tra bằng graph giả lập; lần gọi Ollama thật sử dụng luồng mô phỏng mới.
Kết luận vẫn dựa trên quy tắc đơn giản hóa. Agent mới có quyền chọn công cụ
trong mô phỏng; chưa vận hành HR/IAM thật hoặc tự thực hiện khắc phục.

Các cảnh báo deprecation từ dependency LangGraph/matplotlib cũ vẫn xuất hiện
khi kiểm thử API cũ; chúng không làm thất bại kiểm thử.

## Agent điều phối theo mục tiêu — cập nhật 30/10/2026

- 25 kiểm thử Python đạt, gồm 8 test Agent: phát hiện hỗn hợp, nhánh kiểm
  tra sâu, công việc không trùng, nguồn thay đổi và tái kiểm tra, công cụ
  ngoài allowlist, lỗi model, nguồn bất hợp lệ và lỗi lưu trữ.
- API kiểm thử stream NDJSON, lịch sử/latest và mục tiêu/mode không hợp lệ.
- 3 test tìm đường vẫn đạt; JavaScript mới qua `node --check`.
- Đã chạy Ollama `qwen2.5:7b` thật: tự chọn 8 công cụ và hoàn tất báo cáo.
  Trên giao diện: 14 nhân sự có phát hiện, 10 việc đề xuất nội bộ, 8/56 kiểm
  soát đã đánh giá, 48 kiểm soát chưa đánh giá. Đã xem công việc với HR/IT
  phụ trách và khôi phục báo cáo sau tải lại trang; mô hình 3D nhận 14 hồ sơ.
- Kiểm thử giao diện lần này qua tab trình duyệt trong ứng dụng. Bộ smoke
  Edge trước đó được điều chỉnh để mở phần diễn tập thủ công mới thu gọn;
  chưa chạy lại toàn bộ smoke Edge sau thay đổi này.
- Chưa có connector HR/IAM thực, evaluator A.7/A.8, tự chạy nền hay tự khắc
  phục. Mục tiêu tự do chỉ được xử lý bằng bộ công cụ chuyên biệt có sẵn.

## Giám sát sự kiện và mô hình 3D — cập nhật tiếp theo

- 33 test Python đạt. Bổ sung test worker tự nhận thay đổi, ánh xạ nghiệp vụ
  đến đủ 8 kiểm soát A.6, khắc phục/tái kiểm tra, thay đổi trong lúc Agent
  đang chạy, lưu bền và không chạy lại với thao tác không đổi dữ liệu.
- Đã sửa lỗi áp dụng A.6.7 cho VPN đã thu hồi của người nghỉ việc; có test
  hồi quy xác nhận bàn giao hoàn tất không sinh thiếu bằng chứng remote giả.
- Chạy trực tiếp trên UI với Ollama thật, chỉ gửi nghiệp vụ: HF-025 nghỉ
  việc tự phát hiện A.6.5 (4 tài khoản, 1 laptop); thu hồi/bàn giao tự loại
  phát hiện đó. HF-036 chưa hoàn tất đào tạo tự phát hiện A.6.3; ghi nhận
  hoàn tất tự loại phát hiện theo bằng chứng và kích hoạt xác minh tiếp.
- Đã quan sát trạng thái AI xác minh hoàn tất từ sự kiện, có nhật ký công
  cụ, mã snapshot và revision. Không cần gọi endpoint chạy Agent từ UI.
- WebGL khởi tạo, nội thất/nhân vật mới hiển thị. Kiểm tra DOM ở 320, 768,
  1440 pixel không thấy cuộn ngang toàn trang. Ảnh minh chứng ở
  `docs/charts/hivefive-live-3d.jpg`.
- Ghi chú giới hạn cũ về “chưa tự chạy nền” đã được thay thế: hiện worker
  tự xử lý sự kiện khi máy chủ chạy, kể cả đóng tab. Chưa có scheduler đa
  tiến trình, connector hệ thống thật, tự khắc phục thật hoặc evaluator A.7/A.8.
- Bộ smoke Edge cũ được điều chỉnh để mở phần ghi chú mô phỏng mới; chưa
  chạy lại toàn bộ sau thay đổi hình học. Kiểm tra UI lần này qua trình
  duyệt trong ứng dụng, không tuyên bố đã kiểm toán hiệu năng/GPU đầy đủ.
# Kiểm chứng nâng cấp học thuật ngày 2026-10-30

- Terminal đã đọc README và kiểm tra mã nguồn thực tế.
- `py -3.11 -m unittest discover -s tests -q`: **40 test đạt**.
- `node --test tests/navigation.test.mjs`: **3 test đạt**.
- `node --check backend/static/live.js` và `git diff --check`: đạt.
- `py -3.11 -m agent_core.research_benchmark --ai`: rules 28/28,
  workflow 28/28, Ollama qwen2.5:7b thật 3/3 hoàn tất và khớp toàn bộ nhãn.
  Số liệu chi tiết lưu `research-results.json`; không suy rộng ra dữ liệu thật.
- UI thật: chọn HF-042 → `training_unverified` → revision 5, A.6.3 thiếu
  bằng chứng, `inspect_evidence` được AI tự chọn. Nút khắc phục trong hồ sơ
  tạo revision 6; worker tự xác minh, 1 việc hết phát hiện. Hai trường từ null
  sang true được hiển thị; nguồn và báo cáo cùng revision 6.
- API export trả HTTP 200 với `Content-Disposition: attachment`, snapshot
  hash 64 ký tự và thay đổi trước/sau. GET research trả kết quả thực nghiệm.
- DOM không tràn ngang tại 320px và 1440px. Không có console error sau reload.
- Minh chứng ảnh: `charts/hivefive-case-verified.jpg`.

Không đo token, chi phí tiền, tải đồng thời, độ trễ từ sự kiện, hay hiệu quả
học tập của người dùng. Nhãn tổng hợp do dự án tự xây dựng, chưa được chuyên
gia gán nhãn mù. Những mục kiểm chứng cũ bên dưới là lịch sử, không thay thế
số liệu thực nghiệm mới.


## Kiểm chứng ngữ cảnh nâng cao và thực nghiệm ghép cặp

- 47 test Python đạt; 3 test tìm đường đạt.
- Catalog nghiên cứu có 37 ca; thực nghiệm ghép cặp chạy 8 ca × 3 lần × 3 chế
  độ = 72 lượt, cùng snapshot và đủ số lượt ở mỗi chế độ.
- Kết quả mới tại research-results.json, generated_at 2026-10-30T12:31:08Z:
  rules/workflow/AI đều hoàn tất, exact-match 24/24 mỗi chế độ. Thời gian TB:
  3.25 / 29.40 / 8764.67 ms. AI gọi model 177 lần. Có SHA256 bốn tệp nguồn.
- Đây là kiểm tra đặc tả tổng hợp với evaluator chung, không chứng minh AI tốt
  hơn workflow. Không có kết quả khảo sát hoặc gán nhãn chuyên gia giả lập.
- UI/Ollama thật: HF-042 training_conflict revision 7 thiếu bằng chứng A.6.3,
  giữ HR/LMS mâu thuẫn, tự inspect_context và inspect_evidence; sửa revision 8.
  role_change revision 9 phát hiện A.6.5; ghi nhận rà soát quyền revision 10,
  Agent xác minh và đóng việc. Ảnh charts/hivefive-source-conflict.jpg.
- Quan trọng: máy chủ hiện chạy đã tải phần lớn nâng cấp, nhưng chưa nạp hai
  sửa cuối: training_passed=null khi HR/LMS mâu thuẫn ở cả hai chiều; ngoại lệ
  chỉ cho tài khoản HR với approver/reason là chuỗi không rỗng. Các sửa này đã
  được test và chạy benchmark trong tiến trình mới. Lệnh dừng/khởi động lại
  server bị xét duyệt tự động từ chối: blocked by policy, không nêu thêm lý do.
  Cần khởi động lại máy chủ trước khi coi bản đang phục vụ đã có đủ sửa cuối.
