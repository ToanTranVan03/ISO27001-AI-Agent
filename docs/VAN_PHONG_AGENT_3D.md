> **Tài liệu lịch sử:** mã và tài nguyên 3D đã được xóa khỏi bản hiện tại ngày 10/11/2026. Nội dung dưới đây chỉ ghi nhận phiên bản trước.

# Văn phòng Agent 3D từ video tham khảo

## Đối chiếu video

Đã đối chiếu hình ảnh xuyên suốt và lời thoại của `D:/doanh nghiep agent.mp4`, dài 05:50.70. Video thể hiện văn phòng nhìn chéo, phòng kính có tên, nhân vật riêng, công việc theo phòng, trạng thái nghỉ và bàn duyệt. Khoảng 00:24–00:40 nói về giao việc/lên lịch; 00:38–03:10 thể hiện duyệt đầu ra; 03:37–04:20 thể hiện khu nghỉ; 04:40–05:00 nhấn mạnh người quản lý quyết định bước cuối.

Ứng dụng lấy phong cách không gian và cách trình bày công việc, rồi áp dụng vào nghiệp vụ ISO. Không thêm chức năng đăng mạng xã hội chỉ vì video có chức năng đó. Không suy framework/API của tác giả từ hình ảnh.

## Những phần đã triển khai

- Văn phòng Three.js thật: góc nhìn isometric, phòng kính, sàn gạch/gỗ sáng, bàn máy riêng, ghế, lễ tân, góc nghỉ và tủ tài sản lab. Có xoay, zoom, nhìn từ trên và theo nhân viên.
- 50 nhân viên được giữ nguyên định danh, chia 4 khu. Bấm người, nhãn hoặc bàn để chọn; có danh sách HTML hỗ trợ bàn phím và thiết bị không thao tác được canvas.
- Di chuyển theo trạng thái backend giữa lễ tân, bàn và khu nghỉ. Lưới tìm đường tránh bàn, sofa và tường kính; SOC đi qua cửa phòng. Khi tải lại không diễn lại các hành động cũ thành công việc đang chạy.
- Bốn phòng: Điều phối, Tài sản & nhân sự, SOC, Kiểm soát nội bộ. Avatar làm việc dựa trên subtask đang chạy; hoàn tất/chờ duyệt/bị chặn được phân biệt. Đây là bốn vai trò dùng chung điều phối, chưa phải bốn LLM độc lập.
- Robot SOC theo target máy và trạng thái quét/xử lý thực. Người đi nghỉ không làm robot đổi sang quét nhầm người khác; máy vẫn được liên kết bằng asset_id. Tài sản lab khác được biểu diễn bằng khu tài sản chung.
- Chọn Agent mở bảng bên phải: bình luận mục tiêu, chọn nhân viên/máy, chọn LLM hoặc workflow và gửi trực tiếp đến API missions. Phản hồi, công việc con, nguồn thực thi và bàn duyệt lấy từ hồ sơ backend.
- Workspace chi tiết đặt dưới văn phòng. Nút mở kết quả/bàn duyệt chuyển đến đúng phần; không tự phê duyệt hồ sơ.
- Giữ sơ đồ 2D và khuôn viên cũ như lựa chọn khác. Nếu không khởi tạo được WebGL, có nút chuyển sơ đồ để tiếp tục thao tác.

## Một bình luận điều khiển nhân viên

Ở Văn phòng 3D, chọn nhân viên rồi gửi `cắm USB lạ`, `cài app lạ` hoặc `rời máy không khóa`. Với `prepare_workstation=true`, backend có thể thực hiện `/di-lam` hoặc `/lam-viec` trước khi làm hành động yêu cầu. Mỗi bước vẫn qua cùng bộ kiểm tra chuyển trạng thái, có receipt/event riêng.

- Kiểm tra cả chuỗi trước khi tạo bước chuẩn bị; lệnh không hiểu hoặc điều kiện cuối không hợp lệ không tự tạo ca.
- Không tự gỡ cô lập, mở máy bị bảo vệ, dùng thiết bị đã thu hồi hoặc vượt sự kiện chưa xử lý.
- Request_id gốc và UUID con ổn định giúp retry không tạo trùng bước chuẩn bị/sự kiện chính.
- Các bước được lưu riêng. Nếu điều kiện thay đổi giữa các bước, chuỗi có thể dừng theo guard hiện hành; không che giấu bước hợp lệ đã thực hiện.
- API cũ mặc định prepare_workstation=false, giữ nguyên cách yêu cầu vào ca trước.

Sau hành động, bộ giám sát độc lập phát hiện nhật ký, xử lý trong lab, xác minh và liên kết incident_id. Không gọi một bình luận vừa nhận là đã được AI xác minh. Đây là nhận diện sự kiện/telemetry mô phỏng, không phải nhận diện người từ camera.

## Cách thử

1. Tải lại ứng dụng, mở Văn phòng 3D. Chọn người/máy còn sẵn sàng trong một khu.
2. Gửi `cắm USB lạ` tại khung bình luận nhân viên. Nhìn trạng thái chờ quét, hoạt động SOC và hồ sơ sau xác minh.
3. Chọn phòng SOC, nhập mục tiêu kiểm tra nhân viên/máy đang chọn và gửi bình luận giao việc.
4. Xem công việc con và nguồn thực thi; mở kết quả/bàn duyệt. Kết quả xử lý sự cố không tự trở thành kết luận tuân thủ toàn ISO.

## Kiểm chứng

- 195 test Python, 25 test JavaScript và build frontend đạt. Test đường đi kiểm tra toàn bộ 14 vị trí mỗi khu và lối ra phòng kính SOC; test định danh kiểm tra EMP-050 ở khu 4.
- API thật trên EMP-045: một bình luận từ ngoài ca tạo bước vào ca và sự kiện USB. Gửi lại request_id không nhân đôi hai event.
- Nhiệm vụ mục tiêu dùng Qwen2.5:7b lập kế hoạch thật, source `ollama_plan_and_execute`, hoàn tất các bước và chờ người duyệt. Sự kiện USB được xác minh. Bước SOC trong lượt này dùng `policy-fallback`; không tính phần đó là model thành công.
- Guard giữ nguyên khi có USB đang cắm hoặc trạng thái bảo vệ; các trường hợp cô lập/thu hồi/pending có unit test riêng.
- Đã dựng và xem ảnh WebGL desktop/mobile bằng Edge headless. Ảnh QA dùng fixture để kiểm tra bố cục, không phải số liệu vận hành hoặc benchmark chất lượng AI.
- Công cụ computer-use không kết nối được native pipe Windows trong lượt này; chưa kiểm thử bấm toàn bộ giao diện có đăng nhập. Build/lint không có lỗi chặn; vẫn có cảnh báo cũ và cảnh báo kích thước chunk Three.js.

Video, transcript, fixture, ảnh QA và script thử được lưu trong work (đã ignore), không đưa vào source Git.
