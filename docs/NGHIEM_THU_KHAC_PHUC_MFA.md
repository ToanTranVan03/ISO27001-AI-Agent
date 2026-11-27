# Nghiệm thu khắc phục MFA · A.8.5

Ca mô phỏng trên nhánh ToanTuan7. Phạm vi là tài khoản admin-demo và chính sách ADMIN-MFA trong IAM-LAB. Các tệp TXT là fixture có nhãn mô phỏng; hệ thống chưa kết nối một IAM thực để thay đổi hoặc đo chính sách.

| Bước | Kết quả | Đường đã thử |
|---|---|---|
| Khai phạm vi, nộp nguồn đầu, thẩm định và lưu phát hiện | Đạt. Baseline giữ nguyên ID/hash và thẩm định đầu. | API, PostgreSQL thật |
| Gọi Qwen trên phát hiện | Đạt gọi model và lưu nháp chờ duyệt. Việc duyệt, giao và hoàn thành trong lượt này dùng kế hoạch thủ công riêng. Chưa kiểm tra chất lượng từng mục nháp bằng người dùng. | API, Ollama thật |
| Giao việc có người/hạn, mở việc và hồ sơ nguồn | Đạt. Nhân viên đăng nhập riêng và mở đúng biểu mẫu nộp nguồn A.8.5 bằng nút trên việc được giao. | Giao qua API, nhân viên mở qua React/Edge |
| Tiến độ, gắn nguồn, gửi và kiểm quyền | Đạt bằng API. Thiếu nguồn bị chặn; người thực hiện bị chặn tự xác minh; xác minh trước thẩm định hiện hành bị chặn. | API thật |
| Trả và xác minh lại | Đạt. Giữ hai lần partial và accepted. Tiêu chí đích được ghi đạt trên nguồn sau; kết luận toàn control vẫn thiếu bằng chứng. Nguồn mới làm xác minh cũ cần rà. | API thật |
| Giới hạn quyền theo đợt | Đạt chiều đã chạy. Nhân viên của đợt thử bị chặn đọc, ghi và tải PDF ở một đợt của doanh nghiệp khác. | API thật |
| Xuất báo cáo | Đạt. Tải PDF và Excel từ React, mở bằng pypdf/openpyxl và kiểm chuỗi tiếng Việt, mã control, tài khoản, chính sách, kết luận và lịch sử. Chưa rà bố cục bằng trình xem PDF/Excel desktop. | React/Edge, API thật |
| Lưu dữ liệu | Đạt sau cấp lại phiên đăng nhập và sau restart API. Database thử đã dọn, số dòng chính được theo dõi không đổi. | API thật |

Chưa nghiệm thu xuyên suốt bằng thao tác bấm UI. Tạo đợt/phát hiện, sửa và duyệt nháp Qwen, nộp và gắn lại nguồn, trả lại và xác minh đều còn cần chạy liên tục trên trình duyệt. Bản ghi thử dùng database tạm với hai tài khoản release_admin và remediation_operator. Mật khẩu thử do runner cấp trong phiên chạy. Không dùng mật khẩu tài khoản thật.

## Chạy lại

```powershell
npm --prefix frontend-react run build
.venv\Scripts\python.exe run_isolated_acceptance.py --execute --remediation --remediation-only --output work/mfa-demo-new.json
```

Cần PostgreSQL, Ollama và Edge. Chọn tên JSON mới mỗi lần. Thư mục work/iso_acceptance_* cùng mã database có browser.log và thư mục browser-results chứa hai file xuất. Lượt đầu bộ hồi quy cũ đạt. Lượt ghép có lỗi 422 do ca thử khai sai kết luận khi còn tiêu chí unknown và lỗi 500 tại lượt A.8 ngoài ca; giữ log work/iso_acceptance_f7019f5002a8. Lượt tiếp theo đã sửa kết luận theo rubric nhưng vấp phép kiểm tra vị trí hành động của nhân viên; đã sửa đối chiếu bằng mã hành động. Lượt tập trung đạt ở work/mfa-scoped-final.json.

## Kịch bản demo 5–7 phút

Chuẩn bị trước hai cửa sổ trên một đợt thử riêng còn chạy, tài khoản tư vấn và nhân viên đã phân vai, nguồn trước/sau có nhãn mô phỏng, một phát hiện và bản nháp Qwen. Nếu phải gọi model trực tiếp, chờ ngoài thời lượng hoặc trình bày nháp đã lưu.

1. Phút 0–1. Tư vấn mở Tổng quan 56 control → Tư vấn & khắc phục. Chỉ phạm vi IAM-LAB, admin-demo, ADMIN-MFA, tiêu chí MFA và hồ sơ ban đầu.
2. Phút 1–2. Mở nháp Qwen, chỉ các bước kiểm tra, yêu cầu nguồn và câu hỏi làm rõ. Chỉnh nội dung theo phạm vi, đặt người thực hiện và hạn rồi duyệt giao.
3. Phút 2–3. Nhân viên mở việc. Bấm mở hồ sơ control để nộp nguồn. Quay về phần khắc phục, chọn đúng nguồn sau thực hiện, tích tiến độ và gửi xác minh. Dùng nguồn đầu chỉ có enrolled để minh họa yêu cầu bổ sung.
4. Phút 3–5. Tư vấn trả bổ sung. Nhân viên gửi nguồn thể hiện tài khoản thuộc chính sách và một lần thử xác thực có MFA. Tư vấn thẩm định tiêu chí đích trên nguồn mới rồi xác minh riêng hành động. Chỉ ra các tiêu chí khác vẫn chưa có bằng chứng.
5. Phút 5–7. Tải PDF và Excel. Chỉ baseline, việc đã làm, ID/hash nguồn sau, người xác minh, hai lần xử lý và điểm cần theo dõi.

## Thay đổi và phần cần xác nhận

backend/remediation.py và backend/remediation_api.py lưu criterion_index tùy chọn trong tài liệu JSONB hiện có và kiểm chứng rubric, thẩm định, nguồn viện dẫn. Phát hiện cũ giữ quy tắc toàn control. backend/remediation_document_export.py đưa tiêu chí vào báo cáo. frontend-react/src/RemediationWorkspace.jsx thêm chọn phạm vi và mở nơi nộp nguồn. frontend-react/tests/live-remediation-mfa.spec.js và run_isolated_acceptance.py thêm ca thử. Không cần migration.

Doanh nghiệp thật cần export từ IAM có tài khoản, phạm vi áp dụng, ngoại lệ, thời gian và lần thử xác thực; cần người có quyền phê duyệt thay đổi và người độc lập kiểm tra. Thẩm định một tài khoản chỉ có giá trị trong phạm vi đã khai.
