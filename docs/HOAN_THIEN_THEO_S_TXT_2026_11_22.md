# Hoàn thiện theo s.txt — 22/11/2026

Yêu cầu gốc: [s.txt](../s.txt). Đây là bản nâng cấp trên React/FastAPI/PostgreSQL hiện có, không xây lại hoặc bỏ luồng đánh giá 56 control / thực nghiệm 18 A.8. Các kết quả cũ, nhãn và nguồn vẫn giữ riêng.

## Rà hiện trạng và việc đã nâng cấp

| Chức năng | Đã có trước | Hoạt động / minh chứng | Còn thiếu trước đợt này | Nâng cấp đã thực hiện |
|---|---|---|---|---|
| Tiếp nhận/phạm vi | Bối cảnh theo assessment, inventory lab | Luồng cũ đã có kiểm thử | Chưa có khách hàng và nhiều đợt trên UI | Đăng ký/sửa khách hàng có phiên bản; tạo nhiều đợt riêng và chọn đợt trên thanh điều hướng |
| Tách dữ liệu | Membership theo assessment | Kiểm thử API cũ | Tự seed lab vào mọi đợt, chưa quản lý khách hàng | Đợt `client` bắt đầu rỗng; membership cấp riêng; kiểm quyền backend; không tự thêm tài khoản khách hàng vào lab sau restart |
| Danh mục doanh nghiệp | Nhân viên/tài khoản/tài sản lab | Lưu PostgreSQL | Chưa có danh mục khai báo cho khách hàng mới | Tạo/sửa nhân viên, tài khoản, tài sản bằng snapshot hiện hành; lưu trước/sau vào audit; không tự sinh MFA/hợp đồng/đào tạo/mã hóa |
| Đánh giá | 56 control, nguồn/quality, Agent, thẩm định, SoA | Bộ test hiện hành | Đợt khách hàng có nguy cơ gọi collector lab | Đợt khách hàng chỉ dùng nguồn nộp; cả worker và API đồng bộ cũ đều không lấy preset; thiếu nguồn trả thiếu bằng chứng |
| Phát hiện | Thủ công/ứng viên, control, nguyên nhân đề nghị, vị trí/rủi ro, baseline, chống trùng/history | Ghi thật cô lập | Giữ nguyên nền tảng này | Nối phát hiện với dashboard và danh sách việc theo control |
| AI tư vấn | Qwen structured draft; bước làm/nguồn lực/nghiệm thu | Qwen thật đã chạy | Thiếu mục tiêu, lý do, ước lượng, bằng chứng/cách kiểm tra lại, câu hỏi; đầu vào trích đoạn bị rỗng | Schema mở rộng; đọc trích đoạn đúng đợt/control; thêm sổ đã rà và hành động trước; thiếu nguồn phải có câu hỏi; không có fallback giả |
| Duyệt/giao | Sửa nháp, chuyên viên duyệt, người chính/phối hợp, hạn | Engine/API và ghi thật | Chưa giao riêng từng công việc con; form sửa gửi thừa metadata | Giao bước cho thành viên đã nhận hành động; chặn người ngoài/đổi bước đã xong; sửa form chỉ gửi trường schema |
| Thực hiện | Hướng dẫn, task tuần tự, note, nguồn sau, gửi xác minh | Luồng cũ và luồng khách hàng mới | Quyền cập nhật theo người phụ trách bước | Người nhận bước hoặc người chính được cập nhật; chỉ người chính gửi; người phối hợp không tự xác minh |
| Xác minh/đánh giá lại | Thẩm định tiêu chí, trả bổ sung/làm lại/một phần/đạt/đóng | Agent đánh giá trước/sau + người xác minh thử riêng | Không thay người thật quyết định | Giữ gate nguồn/rubric/context/token; bước hoàn tất không tự biến control thành tuân thủ |
| Dashboard | Tổng quan 56, số hành động cơ bản | Đọc DB và API | Chưa đủ góc nhìn tư vấn/doanh nghiệp/lãnh đạo | Đợt/khách hàng được xem, phát hiện, việc đang làm/sắp hạn/quá hạn/chờ xác minh/đã xác minh/trả lại, tiến độ hành động, phân loại rủi ro đề nghị, tiêu chí chưa đáp ứng, mức độ đáp ứng, nguồn lực dự kiến trong kế hoạch và quyết định còn chờ; chi phí để chưa có dữ liệu |
| Nguồn của 56 control | Checklist nguồn, review, áp dụng | Luồng hiện hành | Chưa nối đầy đủ trạng thái khắc phục vào danh sách | Bộ lọc theo thiếu/nguồn lỗi/cần đánh giá/chưa review/chưa áp dụng/có phát hiện/đang khắc phục/chờ xác minh/có hành động đã xác minh; kèm danh sách công việc cụ thể cần thực hiện (`required_tasks`) cho từng control |
| Thông báo | Inbox riêng, giao việc/gửi/xác minh, nhắc hạn | Kiểm thử quyền/idempotence | Chưa thông báo quản lý, phân công bước con và cấu hình SMTP an toàn | Thông báo quản trị doanh nghiệp; thông báo khi phân công bước con (`assign_task`); phân biệt đạt/một phần/làm lại/bổ sung; nhắc hạn cả người phối hợp/quản lý; hỗ trợ tùy chọn SMTP qua biến môi trường `REMEDIATION_SMTP_*` (không hardcode credentials) |
| Báo cáo | JSON/CSV/HTML/PDF/XLSX trước–sau | Export thật và unit test | Chưa có tổng quan lãnh đạo, sổ rủi ro/yêu cầu, worklist và tư vấn mở rộng | Bổ sung các phần đó vào toàn bộ báo cáo tổng hợp (PDF, Excel nhiều sheet, HTML in và CSV): phần lãnh đạo/đánh giá/kế hoạch/nguồn/xác minh/tồn đọng |
| Quyền/lịch sử | Bốn vai trò theo đợt, CAS, audit | Chặn tự xác minh/cũ nguồn | Bổ sung kiểm tra xuyên khách hàng và restart | API từ chối 403 khi biết ID doanh nghiệp khác; UI đổi góc nhìn không tăng quyền; giữ lịch sử danh mục/hồ sơ |

`has_verified_action` nghĩa là đã có hành động đi qua trạng thái xác minh, không phải mọi tiêu chí của control đều đạt. Tỷ lệ hoàn thành tính từ hành động đã xác minh/đóng trên số hành động được xem; không có hành động thì để chưa có mẫu. Doanh nghiệp đã đăng ký được tính riêng, không tự coi đợt lab cũ là khách hàng thật.

## File và migration

Mở rộng các module cũ:

- `backend/teamwork.py`, `team_api.py`: khách hàng, đợt, thành viên, inventory mode và audit.
- `backend/company.py`, `company_storage.py`, `enterprise_lab.py`, `compliance_report.py`, `enterprise_api.py`, `main.py`: giữ lab cũ, tách khách hàng khỏi seed/collector; danh mục khai báo có snapshot và quyền backend.
- `backend/remediation.py`, `remediation_api.py`, `remediation_notifications.py`, `remediation_document_export.py`: dashboard, công việc con, tư vấn cụ thể, quản lý thông báo và nội dung báo cáo.
- `frontend-react/src/App.jsx`, `CompanyInventory.jsx`, `RemediationWorkspace.jsx`: nối lựa chọn đợt, danh mục, giao việc và tư vấn với màn hình cũ.

Component mới cho phần chưa có: `ClientManagement.jsx`, `ClientInventoryEditor.jsx`, `ConsultingDashboard.jsx`. Không tạo một engine/module khắc phục song song.

Migration cộng thêm trong `init_teamwork()`:

1. `assessment_campaigns.inventory_mode` mặc định `lab` cho đợt cũ; khách hàng mới ghi `client`.
2. `consulting_clients`: profile JSONB/version/người tạo; sửa giữ lịch sử.
3. `consulting_campaigns`: liên kết khách hàng–assessment, FK tới các bảng hiện hành.

Không DROP, không xóa nguồn/kết quả/nhãn. [Migration local](a8-results/s-prompt-main-migration-2026-11-22.json): API mới 200; bảng chính theo dõi không đổi; không tạo khách hàng hoặc hồ sơ thử vào đợt chính. Các bảng danh mục hiện có tiếp tục dùng assessment ID; phiên bản hồ sơ khách hàng tách khỏi snapshot/baseline từng đợt. Tạo đợt mới không tự sao chép nhân sự/nguồn/kết luận từ đợt trước.

API đã đọc/triển khai trực tiếp trong code:

- `GET/POST /api/clients`, `PUT /api/clients/{client_id}`.
- `POST /api/clients/{client_id}/campaigns`.
- `POST /api/clients/{client_id}/campaigns/{assessment_id}/members`.
- `PUT /api/assessments/{assessment_id}/enterprise/company/inventory/{kind}/{identifier}`.
- `GET /api/assessments/{assessment_id}/remediation/dashboard`.
- Các API finding/action/event/report hiện có vẫn dùng lại; event thêm `assign_task`.

Chỉ quản trị hệ thống đăng ký khách hàng/cấp thành viên. Tư vấn/quản trị doanh nghiệp được sửa danh mục trong đợt đã cấp; người thực hiện chỉ đọc danh mục. Dùng chức năng cấp thành viên của khách hàng cho tài khoản khách hàng mới, không dùng chức năng tạo thành viên nhóm lab cũ. Cơ chế này được kiểm qua restart.

## Kiểm thử và lỗi phát hiện

- [Python release](a8-results/s-prompt-python-release-2026-11-22.xml): **438 đạt** (gồm 436 mốc đầu và 2 test bổ sung cho SMTP an toàn + báo cáo HTML/CSV lãnh đạo), còn ba cảnh báo deprecation từ thư viện. Không xóa test để đạt.
- **14 JavaScript đạt**, lint/build đạt.
- [17 kịch bản UI](a8-results/s-prompt-ui-first-2026-11-22.json): gồm hồi quy cũ, form khách hàng và dashboard. Form mới ở bộ này dùng API mock; không ghi dữ liệu vào đợt chính.
- [Ba form ở mốc cuối](a8-results/s-prompt-ui-forms-release-2026-11-22.json): khách hàng, dashboard và khắc phục đều đạt sau khi đồng bộ giới hạn trường tư vấn với backend.
- [Ghi thật và restart](a8-results/s-prompt-isolated-release-2026-11-22.json): API/PostgreSQL/Qwen thật trên DB tạm; hai khách hàng, nhiều đợt, membership, danh mục, upload, đánh giá, AI, phân công bước/phối hợp, nguồn sau, gửi/xác minh/đóng, PDF/XLSX. Có thao tác UI thật và kiểm tách khách hàng. Receipt ghi rõ synthetic, không phải chấm người thật. DB thử được dọn; bảng chính theo dõi giữ nguyên số dòng.
- [Lần đầu](a8-results/s-prompt-isolated-first-2026-11-22.json): bốn luồng qua nhưng phép so sánh restart chưa đạt; khi đó đang thay projection response. Không dùng lần này làm minh chứng thành công. [Lần chạy lại](a8-results/s-prompt-isolated-final-2026-11-22.json) đã đạt; lần release kiểm thêm API cũ và phiên bản khách hàng. [Kiểm seed guard](a8-results/s-prompt-isolated-seed-guard-2026-11-22.json) kiểm thêm tài sản phần mềm không tự tạo tài khoản sau restart và Back/F5 giữa khách hàng.
- [Python lần đầu](a8-results/s-prompt-python-first-2026-11-22.xml): phát hiện test lỗi JSON chạm DB ngoài ý định sau bổ sung kiểm inventory mode. Đã chỉ đọc mode khi cần; luồng nguồn-only giữ kiểm tra lỗi JSON/schema. Bản release chạy lại toàn bộ đạt.

Lỗi chức năng đã sửa: seed lab xuyên đợt, tự thêm thành viên khách hàng vào lab khi restart, trích đoạn AI rỗng, form sửa kế hoạch gửi metadata không hợp schema. Không sửa hồ sơ thật để làm xanh kết quả.

Chạy lại độc lập, dùng tên output mới:

```powershell
.venv\Scripts\python.exe -m pytest tests -q
node --test tests/*.test.mjs
.venv\Scripts\python.exe run_isolated_acceptance.py --execute --remediation --governance --clients --output docs/a8-results/NEW-clients-check.json
```

## Cách dùng

1. Khởi động theo [hướng dẫn](../HUONG_DAN.md). Vào `http://127.0.0.1:8000/` hoặc bản phát triển `http://127.0.0.1:5173/`.
2. Quản trị mở **Doanh nghiệp → Khách hàng tư vấn**, nhập thông tin thật và phạm vi đợt. Chọn đợt ở thanh điều hướng; cấp tài khoản và vai trò đúng đợt. Đợt mới bắt đầu rỗng.
3. Trong **Doanh nghiệp**, khai báo danh mục. Việc lưu tên/tài khoản/thiết bị không tự tạo bằng chứng tuân thủ. Không có quyền thì chỉ xem; không thể gọi API sửa thay bằng việc hiện nút.
4. Trong **Tổng quan 56**, bổ sung nguồn gốc cho control và chạy kiểm tra. Dashboard/bộ lọc chỉ rõ phần còn chờ. Khách hàng mới chỉ đánh giá nguồn nộp, không dùng mẫu lab.
5. Mở **Tư vấn & khắc phục**, tạo phát hiện hoặc phân tích ứng viên. Xem baseline, yêu cầu AI, đọc câu hỏi còn thiếu, sửa kế hoạch rồi duyệt/giao người chính/phối hợp/hạn; có thể giao riêng từng bước. Chưa rõ dữ liệu thì cần bổ sung trước khi chuyên viên quyết định.
6. Người thực hiện làm task, ghi note và nộp nguồn sau. Chạy đánh giá lại khi có nguồn mới. Chỉ người chính gửi xác minh.
7. Người xác minh khác người thực hiện tự thẩm định tiêu chí trên nguồn hiện hành, viện dẫn nguồn sau rồi xác minh. Có thể trả bổ sung/làm lại/một phần; xác minh đạt mới được đóng. Nguồn/phiên bản đổi thì cần rà lại.
8. Tải báo cáo tổng hợp JSON/CSV/HTML/XLSX/PDF. Số liệu báo cáo lấy từ DB theo quyền, không phải tỷ lệ chứng nhận hoặc accuracy chuyên gia. Thẩm định/SoA vẫn theo gate riêng.

## Còn cần dữ liệu và quyết định thực tế

- Nhóm cung cấp nguồn còn thiếu cho 37 control, thay A.6.2, xác nhận nội dung/phạm vi; nâng cấp chức năng không tự giải quyết khoảng thiếu này.
- Người phụ trách/giảng viên xác nhận rubric, nguồn tiêu chuẩn/pháp lý hợp pháp, phương pháp/người chấm và bộ kiểm định chưa dùng phát triển.
- Người đánh giá tự đọc và ghi kết luận; quyết định áp dụng, xử lý rủi ro và phê duyệt SoA phải do đúng người thực hiện.
- Chưa kiểm trên doanh nghiệp thật. Bài thử synthetic chỉ xác nhận phần mềm; không phải nghiệm thu chuyên môn.
- Thông báo hiện trong ứng dụng. Chưa cấu hình/gửi email/SMTP ra ngoài; không hardcode hoặc phát tán credentials.
- Chưa tuyên bố production Internet: còn triển khai TLS, chính sách backup/restore, giám sát, phân quyền vận hành và kiểm tải/bảo mật theo môi trường thực tế. Worker đánh giá/reminder hiện vẫn nằm trong tiến trình API, không phải hàng đợi phân tán HA.
- Giữ phạm vi 56; không tự nhập toàn văn có bản quyền, A.5/toàn bộ ISMS, OCR/video/chữ ký hoặc coi hệ thống là tổ chức chứng nhận.

Đã hoàn thiện thêm phần kỹ thuật có thể kiểm trong môi trường hiện tại; không đánh dấu hoàn thành các mục cần nguồn/phê duyệt/người đánh giá thật.
