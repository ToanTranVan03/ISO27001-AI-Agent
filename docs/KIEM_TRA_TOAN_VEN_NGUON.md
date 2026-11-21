# Kiểm tra toàn vẹn nguồn trước đánh giá và thẩm định

Áp dụng cho nguồn web `upload-source://` và bản thu lab `a8-capture://`; cập nhật 21/11/2026.

## Hành vi

- Nguồn web: kiểm tra manifest, control/đợt, định danh nội dung, bản gốc có trong kho và SHA256 khớp. Nội dung trích xuất bị thay mà không khớp định danh cũng bị phát hiện.
- Bản thu A.8: kiểm tra checksum gói, định danh, đợt/control/run và checksum từng artifact.
- Nguồn thiếu/lệch bản lưu bị đánh dấu `failed`, không đưa vào đầu vào Agent và không dùng để xác nhận đạt/không đạt tiêu chí. Vẫn giữ nguyên hồ sơ cũ; có thể ghi tiêu chí chưa rõ và yêu cầu bổ sung nguồn.
- Nếu nguồn lỗi đã được kết quả máy cũ viện dẫn, kết quả chuyển thành **cần tái đánh giá**, ngay cả khi hàng dữ liệu PostgreSQL không được sửa. Kết luận lịch sử không bị ghi đè. Không tự dùng preset thay nguồn lỗi.
- Nguồn cũ/connector chưa có cơ chế kiểm tra bản gốc trả `not_verifiable`, không tự gắn “đã xác minh”. Kiểm tra văn bản và việc người phụ trách rà nguồn vẫn áp dụng.

Các gate dùng cùng hàm cho bảng hồ sơ, đầu vào Agent và kiểm tra nguồn thẩm định. Giao diện tải nguồn hiển thị trạng thái kiểm tra bản lưu.

**Hash khớp chỉ chứng minh tính toàn vẹn bản lưu, không chứng minh tài liệu có thật, người ký đúng, nguồn đủ tiêu chí hoặc control tuân thủ ISO.**

## Rà dữ liệu hiện có

[Audit chỉ đọc](a8-results/source-integrity-audit-2026-11-21.json): 37 bản ghi nguồn thuộc 19 control; 36 bản thu lab khớp kiểm tra, một nguồn cũ chưa kiểm tra được bản gốc và vẫn không qua ngưỡng văn bản. Đây là A.6.2 đã được yêu cầu thay nguồn, không tự sửa thành hồ sơ hợp lệ.

Đã rà 56 manifest trong thư mục gói hồ sơ của đợt chính: chưa có item nguồn được cung cấp để thu. Mẫu trống không được tính là bằng chứng. Vì nhóm chưa cung cấp nguồn mới hoặc xác nhận chuyên môn, 37 control thiếu nguồn và việc rà mức bao phủ vẫn chưa thể đóng.

## Kiểm chứng

- 365 test Python, 14 test JavaScript, lint/build đạt; 11 kịch bản UI theo [ma trận](MA_TRAN_NGHIEM_THU_UI_TUAN_06.md).
- Test bản gốc mất/lệch hash, nội dung lưu bị đổi, sai đợt/metadata/định danh và artifact hỏng; không làm mất lịch sử kết luận.
- Hai kịch bản ghi thật trên PostgreSQL/backend/Edge riêng đạt. Phép thử cố ý làm lệch một bản gốc trong kho riêng trả chất lượng nguồn lỗi, kết quả cũ `stale`, giữ evaluation ID và HTTP 409 khi cố khởi chạy lại nguồn lỗi. Database thử đã dọn, ba bảng chính không đổi.
