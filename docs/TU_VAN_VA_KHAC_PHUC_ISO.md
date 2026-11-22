# Tư vấn và khắc phục — hướng dẫn, migration và kết quả kiểm chứng

Cập nhật 22/11/2026. Mở **Tổng quan 56 control → Tư vấn & khắc phục · từ phát hiện đến xác minh**. Module bổ sung vào dự án React/FastAPI/PostgreSQL hiện có; không thay bộ đánh giá, không xóa lịch sử và không tạo văn phòng 3D.

## Luồng đã triển khai

1. **Tiếp nhận doanh nghiệp:** lưu tên, lĩnh vực, phạm vi ISMS, địa điểm, phòng ban, tài sản/hệ thống, nghĩa vụ, rủi ro cần xác nhận và liên hệ. Hồ sơ có phiên bản; sửa phải khớp phiên bản và giữ giá trị trước/người/thời điểm.
2. **Phát hiện:** tư vấn chọn control và ghi vấn đề, vị trí, nguyên nhân cần điều tra, mức rủi ro đề nghị. Snapshot đầu gồm tiêu chí, kết luận, nguồn/hash, thẩm định hiện hành và phiên bản bối cảnh được giữ nguyên. Có sửa thông tin phát hiện với lý do/lịch sử, không sửa baseline.
3. **Phân tích ứng viên:** nút phân tích chỉ lấy kết quả chưa đạt/một phần/thiếu bằng chứng đã đánh giá trên nguồn ngoài preset của đợt hiện tại; không lấy kết luận thử nghiệm A.8 hoặc preset. Cùng control/token đã có ứng viên thì không tạo trùng. Nguyên nhân, vị trí và rủi ro vẫn cần tư vấn xác định; thiếu bằng chứng không bị suy thành vi phạm.
4. **Đề xuất:** tạo kế hoạch thủ công hoặc gọi Qwen thật, đầu ra có cấu trúc: tên, hướng dẫn, nghiệm thu, bộ phận, nguồn lực, ưu tiên và công việc con. AI chỉ dùng dữ liệu/tiêu chí dự án được gửi, không có quyền phê duyệt hoặc tự chọn người/hạn. Giữ phản hồi gốc/model và lỗi; không thay lỗi bằng phương án giả.

Đầu vào AI có mô tả phát hiện, bối cảnh người dùng khai, tiêu chí và trích đoạn của tối đa sáu nguồn dùng được cùng ID/hash. Trích đoạn tối đa 1.500 ký tự/nguồn có cờ `truncated`; trường bối cảnh tối đa 1.200 ký tự. Không coi đây là phân tích toàn văn hoặc tự xác nhận nguyên nhân. Nguồn/chuẩn/phạm vi thiếu vẫn cần người phụ trách bổ sung và rà đề xuất.
5. **Duyệt/giao:** tư vấn sửa đề xuất còn nháp, chọn thành viên cùng đợt và hạn. Chặn baseline/rubric/phạm vi cũ. Một phát hiện có nhiều hành động, mỗi hành động có nhiều công việc/bằng chứng.
6. **Thực hiện:** người được giao cập nhật công việc theo thứ tự phụ thuộc. Nộp nguồn qua luồng hiện có, rồi gắn evidence ID mới sau baseline vào hành động. Không lấy snapshot/preset làm nguồn thực hiện. Chưa đủ công việc/nguồn thì chưa gửi xác minh.
7. **Xác minh:** tư vấn/người xác minh khác người thực hiện có thể yêu cầu bổ sung, trả làm lại hoặc ghi một phần. Muốn xác minh đạt, chính người đó phải thẩm định từng tiêu chí hiện hành, có kết luận tuân thủ và viện dẫn nguồn sau khắc phục. Nguồn, rubric, bối cảnh hoặc thẩm định thay đổi sẽ chặn/đánh dấu kết quả cũ cần rà.
8. **Báo cáo:** giữ trước–sau, công việc, nguồn, lịch sử và bất đồng; JSON, CSV mở bằng Excel và bản in HTML. Mở HTML, bấm In/Lưu PDF trong trình duyệt. Chưa phải file `.xlsx` hoặc bộ tạo PDF phía server. Không tự cập nhật kết luận control/SoA vì chỉ bấm hoàn thành công việc.

## Vai trò và cách dùng lần đầu

- Quản trị hệ thống có vai trò tư vấn mặc định cho module mới; có thể phân vai từng thành viên **trong đúng đợt**.
- `consultant`: bối cảnh, phát hiện, đề xuất/sửa kế hoạch, duyệt/giao và xác minh nếu không phải người thực hiện.
- `verifier`: đọc và xác minh; không tạo hoặc phê duyệt kế hoạch.
- `business_admin`: sửa bối cảnh doanh nghiệp và theo dõi; không ký thẩm định hoặc xác minh thay tư vấn.
- `operator`: xem phát hiện/công việc được giao, cập nhật công việc, gắn nguồn và gửi xác minh; không tự xác nhận đạt. Vai trò doanh nghiệp được phân rõ trong module cũng bị chặn ký thẩm định 56 qua API cũ. Các tài khoản đánh giá cũ chưa phân vai giữ luồng cũ.

Đầu tiên lưu bối cảnh thật, phân vai phù hợp, mở control cần xử lý. Không dùng tên nhóm để gán xác nhận giả. Nộp nguồn sau thực hiện bằng nút trong hồ sơ control, rồi quay về hành động và chọn nguồn đó. Sau khi gửi, người xác minh mở hồ sơ control, tự thẩm định rồi quay lại xác minh hành động. Hai người có thể dùng hai cửa sổ; sau thao tác người khác bấm **Làm mới khắc phục** để lấy phiên bản mới. Ghi chú thao tác ít nhất 10 ký tự.

`VERIFIED` là hành động được xác minh, `CLOSED` là đã đóng. Quá hạn được tính như cảnh báo riêng, không tự đổi kết luận hoặc tự gia hạn. Báo cáo hiển thị khi xác minh không còn khớp nguồn/thẩm định hiện hành; lịch sử xác minh cũ không xóa.

## Migration và bảo toàn

`backend/remediation_api.py:initialize()` chạy sau khởi tạo teamwork trong lifespan FastAPI, dùng `CREATE TABLE/INDEX IF NOT EXISTS` trong transaction:

- `remediation_roles`: khóa chính `(assessment_id,user_id)`, khóa ngoại tới thành viên đợt; bốn vai trò của module. Đổi vai trò ghi audit event.
- `remediation_records`: khóa chính `(assessment_id,record_id)`, khóa ngoại tới đợt; kind `context`/`finding`, version và JSONB. Một context mỗi đợt bằng unique index. Quan hệ finding → actions → tasks/evidence nằm trong JSONB và được API kiểm tra theo control/đợt trước khi lưu.
- Cập nhật dùng khóa hàng `FOR UPDATE` và expected version; không để hai người ghi đè thay đổi của nhau. Bối cảnh lần đầu và phân tích ứng viên dùng advisory lock theo đợt.
- Không sửa cấu trúc/bản ghi các bảng bằng chứng và kết quả cũ. Không cấp vai trò thật, tạo bối cảnh hoặc phát hiện mẫu trong đợt chính.

Trước triển khai nên sao lưu PostgreSQL và kho `data/` theo chính sách của nhóm. Migration không xóa dữ liệu; nếu cần quay lại mã cũ, giữ hai bảng mới để bảo toàn hồ sơ, không chạy DROP. Khởi động lại API chỉ khi không có Agent/lô đang chạy. [Kiểm tra migration trên đợt chính](a8-results/remediation-main-migration-2026-11-22.json): các bảng theo dõi giữ nguyên số dòng, hai bảng mới không chứa hồ sơ thử.

## API chính

Tiền tố: `/api/assessments/{assessment_id}/remediation`; mọi endpoint yêu cầu token và membership.

| Endpoint | Nội dung |
|---|---|
| `GET /` | Vai trò, thành viên và hồ sơ được phép xem |
| `PUT /roles` | Quản trị phân vai cho thành viên cùng đợt |
| `PUT /context` | Lưu bối cảnh, kiểm phiên bản, giữ lịch sử |
| `POST /findings`, `PUT /findings/{id}` | Tạo baseline/sửa metadata có lịch sử |
| `POST /discover` | Phát hiện ứng viên từ nguồn/kết quả hiện hành; không tạo trùng |
| `POST /findings/{id}/actions` | Đề xuất thủ công, trạng thái chờ duyệt |
| `POST /findings/{id}/ai-proposal` | Qwen đề xuất có cấu trúc; lỗi trả 502 và lưu lịch sử |
| `POST /findings/{id}/actions/{id}/events` | Duyệt, sửa nháp, bắt đầu, cập nhật task, gắn nguồn, gửi, xác minh, trả lại, đóng |
| `GET /report`, `/report.csv`, `/report.html` | Báo cáo trước–sau theo quyền hiện hành |

CSV chặn công thức từ dữ liệu người dùng; HTML escape nội dung để không thực thi script người dùng. Báo cáo không chứa nguyên văn tài liệu nguồn. Các file tải xuống cần bảo quản theo quyền dữ liệu của doanh nghiệp.

## Kiểm chứng thực tế

- [Lần đầu ghi thật bị lỗi](a8-results/remediation-2026-11-22-isolated.json): luồng thủ công đạt đến xuất báo cáo nhưng AI 502. SDK Ollama 0.4 không nhận schema dictionary. Đã dùng HTTP `/api/chat` có JSON Schema, giữ model và lỗi cũ.
- [Chạy lại đạt](a8-results/remediation-2026-11-22-isolated-retry.json), [sau siết nguồn/phạm vi](a8-results/remediation-2026-11-22-isolated-final.json), [có báo cáo CSV/HTML](a8-results/remediation-2026-11-22-isolated-exports.json), [chặn người thực hiện ký thẩm định qua API cũ](a8-results/remediation-2026-11-22-isolated-role-guard.json): backend/PostgreSQL thật trên database tạm, source upload, phân vai, action/task, bằng chứng, trả một phần, thẩm định, xác minh/đóng, Qwen thật tạo nháp. Kiểm dữ liệu qua logout/login và restart; database thử đã dọn, số dòng bảng chính được theo dõi không đổi.
- [Hồi quy 13 giao diện](a8-results/remediation-regression-ui-2026-11-22.json), [UI tải CSV/bản in](a8-results/remediation-workspace-ui-2026-11-22-exports.json). Luồng UI phân vai dùng API mô phỏng; ghi thật được kiểm riêng bằng bộ ở trên. Các lỗi locator label/combobox và checkbox kiểm quá sớm được giữ trong báo cáo UI lần đầu, sửa test theo accessible role và chờ kết quả server.
- [Bộ Python sau xuất báo cáo](a8-results/remediation-2026-11-22-python-release.xml), [mốc kiểm tra cuối](a8-results/remediation-2026-11-22-python-verified.xml): 407 đạt; 14 JavaScript, lint/build đạt. [13 Edge sau cập nhật báo cáo](a8-results/remediation-release-ui-2026-11-22.json) đạt trong một lần. Test kiểm không tự xác minh, stale token/phạm vi, nguồn mới/nguồn preset, phụ thuộc công việc, nháp AI, lỗi AI không fallback, tạo ứng viên idempotent, chống XSS và công thức CSV.
- [Biên nhận chi tiết lưu trước khi dọn database thử](a8-results/remediation-2026-11-22-receipt.json) giữ hồ sơ tổng hợp, lịch sử task/xác minh và phản hồi Qwen nháp, có nhãn rõ không phải đánh giá con người hoặc phê duyệt chuyên môn.

Chạy lại trên môi trường thử riêng:

```powershell
.venv\Scripts\python.exe run_isolated_acceptance.py --execute --remediation --output docs/a8-results/NEW-remediation-check.json
```

Lệnh tự tạo/dọn database có tên giới hạn `iso_acceptance_*`; giữ thư mục log dưới `work/`. Không chạy các nhãn/thẩm định mô phỏng vào đợt doanh nghiệp chính. Lưu sang tên báo cáo mới, không ghi đè mốc cũ.

## Đối chiếu prompt và phần chưa hoàn tất

| Nhóm yêu cầu | Kết quả / giới hạn |
|---|---|
| Tiếp nhận/bối cảnh | Có phiên bản, lịch sử, trường phạm vi/tài sản/nghĩa vụ/rủi ro; dùng chung assessment ID với inventory hiện có. Chưa có bộ quản trị đa tổ chức đầy đủ hoặc danh mục pháp lý được thẩm định |
| Tiêu chuẩn/áp dụng | Giữ catalog 56 và luồng quyết định/SoA hiện có; có tham chiếu phiên bản và nguồn chính thức. Chưa nhập toàn văn tiêu chuẩn, điều khoản ISMS/A.5 hoặc một thư viện pháp lý mới |
| Gap → hành động | Có phát hiện thủ công/ứng viên từ kết quả hiện hành, snapshot, nhiều hành động/công việc, Qwen và phê duyệt con người |
| Triển khai/xác minh | Có phân vai, giao việc, phụ thuộc tuần tự, nguồn sau, trả lại/thẩm định/xác minh và giữ lịch sử. Chưa có sơ đồ phụ thuộc tùy ý/co-assignee, inbox nhận/đọc thông báo hoặc email/scheduler nhắc hạn |
| Bằng chứng | Dùng tài liệu/log/cấu hình và nguồn thu hiện có; không tự tạo hồ sơ doanh nghiệp. Chưa có tiếp nhận ảnh/video/OCR và chữ ký điện tử mới |
| Rủi ro | Có trường rủi ro/nguyên nhân/ưu tiên cần xác nhận, không tự tính thành kết luận chuyên môn. Chưa có risk register định lượng hoặc duyệt risk acceptance riêng |
| Báo cáo | Có trước–sau JSON/CSV/bản in lưu PDF qua trình duyệt; chưa xuất XLSX hoặc PDF server riêng |
| Nghiệm thu thật | Vẫn cần nguồn, người chấm và xác nhận phạm vi/rubric/SoA. Bài thử tổng hợp không phải kết quả audit độc lập hoặc chứng nhận ISO |

Nguồn tham chiếu metadata tiêu chuẩn: [ISO/IEC 27001:2022](https://www.iso.org/standard/27001), [ISO/IEC 27001:2022/Amd 1:2024 — Climate action changes](https://www.iso.org/standard/88435.html). Không sao chép nội dung tiêu chuẩn có bản quyền hoặc coi rubric dự án là toàn văn ISO. Khi mở rộng ngoài 56 control cần nguồn hợp pháp, rubric và xác nhận phạm vi trước; không tự sinh các yêu cầu bắt buộc.

Các file chính: `backend/remediation.py`, `remediation_api.py`, `remediation_export.py`; nối `backend/main.py`, `enterprise_api.py`; `frontend-react/src/RemediationWorkspace.jsx`, `Scope56.jsx`; test engine/API/discovery/export/UI/ghi thật và `run_isolated_acceptance.py --remediation`. Danh sách chi tiết theo commit và các báo cáo dẫn ở trên.
