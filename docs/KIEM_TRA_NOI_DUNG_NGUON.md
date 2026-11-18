# Kiểm tra nội dung nguồn trước đánh giá — 18/11/2026

Chính sách kỹ thuật `text-usability-v1` chặn tài liệu trích xuất quá ít hoặc chủ yếu là ký tự lặp. Điều kiện tối thiểu: 20 ký tự chữ/số, ít nhất 5 ký tự chữ/số khác nhau và không quá 60% là một ký tự lặp. Đây là ngưỡng xử lý văn bản của dự án, **không phải yêu cầu ISO hoặc xác nhận nguồn đủ tiêu chí**.

- PDF/DOCX mới không đạt điều kiện bị trả lỗi trước khi lưu; người cung cấp cần kiểm tra tài liệu gốc, khả năng trích xuất/OCR và nộp lại. Hệ thống chưa tự OCR tài liệu ảnh.
- Nguồn cũ được giữ trong database/lịch sử. Khi đánh giá ở chế độ không dùng preset, nguồn không đạt điều kiện bị loại khỏi đầu vào Agent; audit trail ghi ID nguồn bị loại. Không còn nguồn thì trả thiếu bằng chứng và không gọi model.
- Màn hình Phạm vi 56 phân biệt số nguồn hiện diện với nguồn qua kiểm tra nội dung tối thiểu. Nguồn lỗi có cảnh báo và việc yêu cầu nộp lại; nút chạy chỉ bật khi có nguồn dùng được.
- Nguồn dài vẫn có thể sai, hết hạn hoặc không liên quan. Độ dài không thay việc kiểm tra hash, xuất xứ, mức bao phủ, thẩm định từng tiêu chí hoặc phê duyệt.
- Kiểm tra thực tế A.6.2: nguồn cũ chỉ có 1 ký tự được giữ nguyên nhưng không đưa vào model. Không sửa kết luận cũ hoặc tự biến hồ sơ thành không tuân thủ.

Kiểm chứng: 253 test Python, 5 test JavaScript, lint/build đạt; 3 cảnh báo deprecation thư viện. Chưa xác nhận toàn bộ thao tác UI. Nguồn cho 37 control, nguồn thay thế A.6.2, bộ kiểm định và xác nhận chuyên môn vẫn cần bổ sung.
