# Hoàn thiện hồ sơ và trình duyệt SoA 56 control

## Sử dụng trên giao diện

Trong **Tổng quan 56 control**, bấm **Báo cáo & xuất SoA**. Bảng **Hồ sơ nào còn chặn trình duyệt?** cho biết từng control còn thiếu điều kiện gì. Lọc theo hồ sơ còn thiếu, hồ sơ đủ điều kiện, hạn kế hoạch đã qua hoặc tìm theo control/người nhận. Xuất JSON/Markdown để giao việc.

Bấm **Bổ sung** để mở đúng control:

1. **Đọc tiêu chí & bổ sung bằng chứng**: nộp nguồn gốc có nội dung, đọc phạm vi/giới hạn và chạy đánh giá lại khi cần.
2. **Thẩm định kết luận trên nguồn hiện hành**: người đánh giá đọc từng tiêu chí, ghi kết quả/căn cứ và viện dẫn đúng nguồn. Không xác nhận đạt/không đạt từ nguồn đã bị đánh dấu không dùng được; có thể ghi chưa rõ và mô tả phần chưa xác minh.
3. **Tính áp dụng & kế hoạch xử lý**: người phụ trách tự quyết định, ghi lý do và kế hoạch. Với control áp dụng, cần người chịu trách nhiệm, hạn hoặc kỳ rà tiếp theo và cách thu lại nguồn/kiểm tra kết quả. Được lưu bản nháp thiếu trường; chưa được trình duyệt khi thiếu điều kiện.

Sau khi rà rubric và đủ hồ sơ hiện hành, người phụ trách mới thực hiện **phê duyệt SoA toàn phạm vi**. Công cụ không tự quyết định thay người phụ trách.

## Điều kiện và cách hiểu

- Phải có xác nhận rubric đúng phiên bản; mỗi control có quyết định áp dụng/loại trừ kèm căn cứ. Control áp dụng cần thẩm định tiêu chí hiện hành và kế hoạch có đủ thông tin theo chính sách dự án.
- Control loại trừ không tự phát sinh hồ sơ, thẩm định hay hạn xử lý giả; vẫn phải có căn cứ loại trừ để người phụ trách rà.
- Đủ điều kiện **hồ sơ** không phải đạt control. SoA có thể ghi nhận không tuân thủ/chưa đủ bằng chứng kèm kế hoạch trung thực; phê duyệt không thay chứng nhận ISO hoặc chứng minh đã khắc phục xong.
- Hạn đã qua chỉ là cảnh báo cần rà, không đủ căn cứ kết luận công việc chưa hoàn thành. Không tự gia hạn, đổi nhãn hoặc đóng công việc. Ngày rà dùng múi giờ Asia/Bangkok (UTC+7).
- Dùng `scope56-approval-v2-followup` trong fingerprint phê duyệt. Bản duyệt cũ được giữ nhưng không tự chuyển thành phê duyệt theo chính sách mới. Thay nguồn/quyết định/thẩm định thì phải kiểm tra lại tính hiện hành.
- Thẩm định cũ dùng nguồn không còn phù hợp vẫn giữ trong lịch sử; không được dùng làm thẩm định hiện hành để thông qua điều kiện duyệt.

Đây là chính sách kiểm tra hồ sơ của đồ án, không khẳng định ISO bắt buộc đúng các trường hoặc ngưỡng kỹ thuật này cho mọi doanh nghiệp.

## Kiểm chứng ngày 18/11/2026

295 test Python, 7 test JavaScript, lint/build và render thành công. API đang chạy trả HTTP 409 khi cố duyệt hồ sơ còn thiếu, HTTP 422 khi kết luận đạt từ nguồn A.6.2 không dùng được; đã xác nhận không phát sinh thẩm định/phê duyệt thử. Chưa kiểm thử toàn bộ thao tác trình duyệt do công cụ chưa kết nối.

Hồ sơ thực tế vẫn còn thiếu: rubric chưa xác nhận; 56 quyết định tính áp dụng và thẩm định hiện hành chưa hoàn tất; 37 control thiếu nguồn ngoài preset, A.6.2 cần thay nguồn. Nguồn kiểm định mới và nhãn người đánh giá đủ điều kiện phải do nhóm cung cấp/xác nhận; không tích hoàn tất bằng kết quả giả định.
