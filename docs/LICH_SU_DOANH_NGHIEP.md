# Theo dõi thay đổi doanh nghiệp giả lập

Trang **Doanh nghiệp** hỗ trợ chọn nhân viên → chọn sự kiện nghiệp vụ → **Xem trước thay đổi** → đọc giá trị trước/sau → **Xác nhận lưu thay đổi**. Xem trước không ghi database. Nếu dữ liệu đã đổi ở phiên khác, cần xem trước lại; API kiểm tra snapshot bên trong giao dịch lưu. Hủy hoặc thay sự kiện không áp dụng bản xem trước cũ. Yêu cầu không tạo thay đổi được thông báo riêng.

Lịch sử hiển thị tối đa 30 thay đổi gần nhất, có thể lọc theo nhân viên, kèm người cập nhật, thời điểm và các trường trước/sau. Bản ghi cũ chưa có người cập nhật được ghi rõ; không tự gán tên. Trạng thái chưa ghi nhận, chưa xác minh và giá trị không được phân biệt.

API cùng kiểm tra phiên đăng nhập và quyền truy cập đợt đánh giá:

- `POST /api/assessments/{id}/enterprise/company/events/preview`: tính bản xem trước từ snapshot hiện hành.
- `POST /api/assessments/{id}/enterprise/company/events`: giao diện gửi thêm `expected_snapshot_hash` để chặn dữ liệu cũ (HTTP 409). Trường này còn tùy chọn để tương thích client cũ; client muốn kiểm soát xung đột phải gửi hash.
- `GET /api/assessments/{id}/enterprise/company/history?employee_id=EMP-001&limit=30`: chỉ đọc, lọc trong đúng đợt; `limit` từ 1 đến 100.

Thay đổi là dữ liệu nghiệp vụ giả lập, không phải bằng chứng độc lập, phê duyệt chuyên môn hay kết luận control. Cần thu/đánh giá lại nguồn hiện hành theo luồng đánh giá; lịch sử đánh giá cũ được giữ nguyên. Không sử dụng chức năng này để tự tạo nhãn người chấm.

Kiểm chứng: 260 test Python đạt, lint/build frontend đạt; kiểm tra render thẻ thay đổi. Chưa xác nhận đầy đủ thao tác bằng trình duyệt.
