# Bộ kiểm định AI — điều kiện trước khi đo accuracy

Bộ sinh mới là dữ liệu phát triển đã biết, không tự trở thành tập độc lập. Không dùng câu trả lời Agent hoặc design-key của trợ lý làm đáp án chuyên gia.

Mỗi ca kiểm định cần: client/assessment/control, rubric version, bản nguồn gốc/hash/snapshot chốt trước suy luận, điều kiện phạm vi, người cung cấp/xác nhận nguồn, lịch sử sử dụng phát triển, người chấm và mức hỗ trợ/tiếp xúc kết quả, nhãn/căn cứ chuyên gia được khóa. Những thông tin chưa có để trống, không tự tạo tên/chữ ký.

Nhóm cần chuẩn bị và chấm các tình huống:

1. Đủ bằng chứng thực hiện.
2. Có chính sách nhưng chưa có nguồn triển khai.
3. Không có nguồn.
4. Hai nguồn mâu thuẫn.
5. Nguồn không liên quan.
6. Nguồn hết hạn theo tiêu chí được chấp nhận.
7. Nguồn thuộc doanh nghiệp khác.
8. Nguồn sai tiêu chí.
9. Prompt injection hoặc nội dung gây hiểu nhầm.
10. Nhân sự quy mô lớn.
11. Nhiều kỳ.
12. Phát hiện đã khắc phục có nguồn sau.
13. Phát hiện còn mở.
14. Có nguồn mới làm kết quả cũ cần đánh giá lại.

Luồng chấm mù/khóa nhãn/đối chiếu từng người và phân loại hỗ trợ hiện có được dùng lại. Kiểm thử kỹ thuật cho denial/missing/injection/schema không thay nhãn chuyên môn của 14 nhóm ca này.

Khi đủ nhãn hợp lệ: accuracy = số khớp / số ca hợp lệ; precision/recall/F1 cần nêu nhãn dương và xử lý multiclass/missing; số lỗi và missing không bỏ khỏi mẫu để tăng điểm. Nguồn ID đúng có thể đo riêng, nhưng hash/ID đúng không chứng minh kết luận đúng. Tỷ lệ unsupported claims cần người rà căn cứ; không tự coi model confidence là calibration hoặc độ đúng.

Tại mốc 26/11 chưa có bộ held-out mới do chuyên gia xác nhận cho nâng cấp này; các chỉ số độc lập để **chưa có dữ liệu**, không gán 100% từ test phần mềm đạt.
