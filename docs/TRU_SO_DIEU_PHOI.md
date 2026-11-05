# Trụ sở điều phối doanh nghiệp

Tham khảo video người dùng cung cấp `D:\doanh nghiep ai agent.mp4` (38,15 giây).
Đã xem 12 khung hình trải đều video: trụ sở chia phòng, mỗi phòng một nhiệm vụ,
giao một chủ đề, bàn giao kết quả và có bước duyệt. Giao diện video không đủ
để xác minh cách các Agent bên trong thực thi. Không sao chép hình ảnh hoặc logo.

## Cách dùng

Trong **Mô phỏng 3D**, phần **Trụ sở điều phối** nằm trên văn phòng tương tác.
Sơ đồ gồm bốn tòa nhà; đèn và nhãn trạng thái lấy từ tiến độ nhiệm vụ.
Chọn tòa nhà để mở đầu ra phòng tương ứng, không tự tạo nhiệm vụ mới.
Nhập chủ đề kiểm tra, chọn phạm vi con người/phần cứng/phần mềm/toàn bộ rồi
nhấn **Giao nhiệm vụ kiểm tra**. Chủ đề là mô tả cho hồ sơ; các bước thực thi
được giới hạn theo phạm vi đã chọn, chưa phải bộ lập kế hoạch cho mọi yêu cầu doanh nghiệp.

1. **Điều phối** ghi nhận chủ đề và phạm vi.
2. **Tài sản & nhân sự** chụp danh mục từ PostgreSQL của đợt đánh giá.
3. **SOC** đọc telemetry trong phạm vi và gọi chính luồng ứng phó hiện có.
   Khóa quét được dùng chung với bộ giám sát để tránh xử lý trùng.
   Mô hình/công cụ hoặc fallback được ghi trong kết quả khi có sự cố.
4. **Kiểm soát nội bộ** kiểm tra lại dấu hiệu còn mở, kết quả chưa xác minh
   và hồ sơ chưa giải quyết; lập báo cáo chờ người phụ trách duyệt.
5. Người dùng nhập nhận xét rồi **Duyệt hồ sơ kiểm tra** hoặc **Yêu cầu bổ sung**.
   Không duyệt được hồ sơ có hạng mục chặn. Khi duyệt, kiểm tra lại dấu hiệu/hồ sơ
   còn mở để không duyệt dựa vào báo cáo cũ trong khi đã có vấn đề mới.

Đầu ra mỗi phòng mở được ở **Xem đầu ra bàn giao**. **Tải hồ sơ JSON** xuất
chủ đề, phạm vi, danh mục tại thời điểm thu thập, dấu hiệu, ID sự cố, nguồn xử lý,
tiến độ, thời điểm bàn giao và nhận xét. Lưu 10 nhiệm vụ gần nhất trong giao diện;
database giữ toàn bộ. Dữ liệu tách theo đợt đánh giá và API yêu cầu đăng nhập/quyền truy cập.

## Giới hạn và tính đúng đắn

- Các phòng là vai trò của quy trình có giới hạn, không phải bốn mô hình AI độc lập.
  SOC dùng cơ chế nhận diện/AI/công cụ vốn có; đọc danh mục và tổng hợp là mã xử lý xác định.
- Dữ liệu và hành động thuộc doanh nghiệp giả lập. Không kết nối ERP, mạng doanh nghiệp
  thật hoặc tự tạo bài marketing, ảnh, video như ví dụ Content OS.
- Không điều khiển đồng loạt nhân viên; nhiệm vụ liên phòng và bình luận cá nhân
  là hai luồng thao tác riêng, dùng chung dữ liệu doanh nghiệp.
- Không có dấu hiệu mới không đồng nghĩa đạt toàn bộ 56 kiểm soát.
  Duyệt hồ sơ xác nhận lượt kiểm tra này, không phải cấp chứng nhận ISO.
- Mỗi đợt đánh giá chạy một nhiệm vụ liên phòng tại một thời điểm. UUID chống tạo trùng.
  Nếu lỗi, bước sau bị chặn. Sau restart, nhiệm vụ đang chạy được đánh dấu gián đoạn;
  người dùng giao lượt kiểm tra mới từ dữ liệu hiện tại, không hiển thị tiến độ giả.
