# Tích hợp luồng nhân viên từ Tu/Tuan7 — 27/11/2026

Triển khai trên kiến trúc main FastAPI/PostgreSQL/React, giữ phạm vi 56 control. Không chuyển sang ứng dụng Streamlit hoặc catalog 26 của nhánh Tú.

## Cách sử dụng

1. Mở **Doanh nghiệp → Nhân viên thực hiện**. Quản trị gán rõ tài khoản thành viên với mã nhân viên trong cùng đợt. Không tự suy tên tài khoản thành nhân viên; không cho đổi danh tính đã gán.
2. Tư vấn tạo yêu cầu có nội dung và phiên bản. Đào tạo liên kết A.6.3; NDA A.6.6; MFA A.8.5; bàn giao A.6.5. Đây là liên kết nghiệp vụ đại diện, không bao phủ toàn bộ control.
3. Nhân viên đăng nhập bằng tài khoản được gán, tự trả lời/xác nhận. Người khác không nộp thay.
4. MFA/bàn giao cần người quan sát chọn nguồn gốc dùng được của đúng control và đúng tài khoản/thiết bị. Người xác minh phải khác nhân viên và người quan sát.
5. Người xác minh chấp nhận, yêu cầu làm lại hoặc bổ sung. Có thể mở kiểm tra lại, giữ nguyên lịch sử. Bấm làm mới để nhận cập nhật của tài khoản khác.
6. Dùng nút mở hồ sơ control để chạy quy trình đánh giá/thẩm định hiện có. Có thể xuất JSON yêu cầu; nếu dùng làm hồ sơ bổ sung cần nộp qua luồng nguồn và thẩm định như các nguồn khác. Chưa tự xuất bản phản hồi thành bằng chứng đạt chuẩn cho Agent.

## Giới hạn từng luồng

- **Đào tạo:** phản hồi từ khóa theo rubric nghiên cứu về nhận diện lừa đảo, xử lý an toàn và báo cáo; gợi câu hỏi tiếp theo, lưu lần làm lại. Không phải chấm ngữ nghĩa bằng LLM, không tự cấp chứng nhận đào tạo hoặc đánh giá năng lực nhân sự.
- **NDA:** xác nhận đã đọc đúng nội dung/hash/phiên bản; không phải chữ ký điện tử hoặc xác nhận hiệu lực pháp lý. Phiên bản mới thay thế bản cũ nhưng giữ toàn bộ lịch sử; không khôi phục phiên bản cũ thành hiện hành.
- **MFA:** phân biệt đã đăng ký với đã bắt buộc sử dụng. Không tự đăng ký MFA hoặc thay đổi IAM; cần bằng chứng và xác minh riêng.
- **Bàn giao:** đối chiếu mã thiết bị đang được giao trách nhiệm và tham chiếu biên nhận. Không tự xác nhận nhận vật lý hoặc đổi cờ returned trong kho.

## Dữ liệu, quyền và API

Prefix `/api/assessments/{assessment_id}/employee-workflows`: GET bảng, PUT `/bindings`, POST tạo yêu cầu, POST `/{request_id}/events` với expected_version và command respond/observe/review/reopen. Đọc kiểm tra thành viên/đợt; operator chỉ thấy yêu cầu của mình. Quan hệ tài khoản/thiết bị được kiểm tra lại trước khi quan sát/xác minh.

Hai bảng mới: `employee_identity_bindings`, `employee_workflow_requests`. Khởi tạo bổ sung, không xóa bảng/kết quả cũ. Các sự kiện và phiên bản tài liệu được giữ; khóa phiên bản chặn nộp lại dữ liệu cũ. Thông báo dùng hàng đợi trong ứng dụng hiện có, không thay cấu hình gửi email ngoài.

`WAITING_EMPLOYEE → WAITING_SOURCE/AWAITING_REVIEW → REVIEWED`; yêu cầu làm lại về REWORK; phiên bản cũ SUPERSEDED. REVIEWED chỉ là thẩm định yêu cầu. ID/hash nguồn và review_token gắn với lần xác minh; khi nguồn/rubric thay đổi, verification_current trở thành false. Không sửa kết luận control, nhãn người chấm, trạng thái đào tạo/NDA, MFA hoặc SoA.

Nguồn phải đúng đợt/control, không phải preset tự sinh và không bị đánh dấu không dùng được. Hash/quyền truy cập không chứng minh tính xác thực ngoài đời. JSON xuất có câu trả lời nhân viên: chỉ chia sẻ với người được phép.

## Kiểm chứng

- [481 test Python](a8-results/employee-workflows-python-release-2026-11-27.xml); 14 test JavaScript; lint/build đạt.
- [Ghi thật cô lập](a8-results/employee-workflows-isolated-verified-2026-11-27.json): API/PostgreSQL, bốn luồng, quyền nhân viên, phiên bản NDA, MFA chưa enforced bị chặn, nguồn thay đổi làm hết hiệu lực xác minh; thao tác trả lời NDA trên UI; giữ dữ liệu sau restart. Database thử đã xóa, số dòng chính không đổi. Đây là dữ liệu synthetic, không phải chấm/phê duyệt thật.
- [Lần đầu](a8-results/employee-workflows-isolated-first-2026-11-27.json) có lỗi so sánh sau restart khi đang bổ sung trường projection; giữ báo cáo lỗi, đã chạy lại đạt. Không sửa nhãn để làm xanh.

Nhóm vẫn cần gán tài khoản đúng người, cung cấp nội dung chính sách và bằng chứng thực tế, thực hiện/xác minh bằng người có trách nhiệm. Không tạo sẵn xác nhận thật trên đợt chính.

[Kiểm tra main sau nạp API](a8-results/employee-workflows-main-smoke-2026-11-27.json): API 200, chưa tạo binding/yêu cầu trên đợt chính; giữ 110 bằng chứng, 282 kết quả, 3 tài khoản và 22 hồ sơ khắc phục.
