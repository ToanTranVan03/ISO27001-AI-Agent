# Hướng dẫn sử dụng hệ thống đánh giá tuân thủ

Khởi động và đăng nhập theo [CHAY_LOCAL.md](CHAY_LOCAL.md). Giao diện chính: http://127.0.0.1:5173.

## Phạm vi 56 control

1. Xem tiêu chí, nguồn và bước cần làm tiếp của từng control.
2. Thu gói hồ sơ hoặc nộp PDF/DOCX phù hợp, đọc nội dung/nguồn/hash đã thu.
3. Chạy **Agent đánh giá hồ sơ đã thu**; kiểm tra kết luận, viện dẫn và phần thiếu.
4. Người đánh giá thẩm định có căn cứ; người phụ trách xác định tính áp dụng và kế hoạch xử lý.
5. Xuất SoA 56 và chỉ phê duyệt khi đủ điều kiện. Thay đổi nguồn/tiêu chí làm thẩm định cũ không còn hiện hành.

Chi tiết: [thu hồ sơ và thẩm định](docs/THU_HO_SO_VA_THAM_DINH_56.md).

## Thực nghiệm 18 A.8

Admin chọn nguồn raw replay hoặc live, profile và engine rồi tạo lượt. Assessor khác tài khoản mở lượt mới để chấm mù. Lượt cũ trước giao thức `blind-v3-coordinator-only` giữ làm lịch sử, cần admin tạo lại để chấm theo giao thức mới.

- Raw: 18 control, 108 ca cấu hình/log mô phỏng.
- Live: 5 probe đại diện; 13 control chưa hỗ trợ trả thiếu bằng chứng.
- Baseline là đối chứng luật, không phải AI. Không có nhãn người thật thì chưa có độ đúng so với con người.

Chi tiết: [quy trình nghiệm thu](docs/QUY_TRINH_NGHIEM_THU_A8.md), [giới hạn hiện tại](docs/HOAN_THIEN_THEO_GOP_Y_GIANG_VIEN.md).

## Doanh nghiệp và Hồ sơ ISO

Danh bạ, tài khoản và thiết bị đọc từ PostgreSQL theo đợt. Các thay đổi hồ sơ nghiệp vụ làm thay đổi snapshot và có thể yêu cầu đánh giá lại. Hồ sơ ISO theo dõi kết quả dùng chung; chạy xong không đồng nghĩa đáp ứng kiểm soát. Không còn văn phòng nhân vật/bình luận hoặc tác vụ SOC demo.
