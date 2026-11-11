# Công việc đánh giá dùng chung và tiếp tục tự động

## Cách dùng

Mở **Hồ sơ ISO** trên ứng dụng hiện tại. Bảng công việc hiển thị trạng thái, người phụ trách và thời điểm cập nhật, tự làm mới khoảng 5 giây. Thành viên cùng đợt đánh giá nhìn cùng kết quả PostgreSQL.

- **Tiếp tục / xem kết quả chung**: nếu đang chạy, theo dõi job có sẵn; nếu kết quả còn mới, dùng lại. Mục chưa đánh giá, lỗi hoặc dữ liệu đổi sẽ chạy đánh giá.
- **Chủ động đánh giá lại**: yêu cầu một lượt mới kể cả khi kết quả còn mới; vẫn không vượt khóa job đang chạy.
- **Agent tiếp tục các việc còn lại**: chọn kiểm soát có collector, ưu tiên kết quả cần tái đánh giá, sau đó mục chưa làm/lỗi theo số kiểm soát. Tối đa 12 mục/lượt; dừng khi lỗi, hết việc hoặc người dùng yêu cầu dừng.
- Mục chờ bằng chứng/duyệt không tự chạy lặp khi dữ liệu chưa đổi. Xem kết luận, bổ sung hồ sơ và xử lý theo quyền tại Phạm vi 56 control.

Ví dụ: người A kiểm tra A.6.1; người B vào cùng đợt thấy kết quả đó và tiếp tục A.6.2. Nếu nguồn thay đổi, A.6.1 được đánh dấu cần đánh giá lại. Kết quả A.6.1 không thay thế hồ sơ từng nhân viên; có tài khoản không tự chứng minh đã thẩm tra tuyển dụng.

## Cơ chế

- GET `/api/assessments/{id}/enterprise/shared-work`: hồ sơ, trạng thái chung, đề xuất công việc tiếp theo.
- POST cùng đường dẫn `/start`: body `{ "control_id": "A.6.1", "force": false }`; bỏ control_id để chọn việc tiếp theo. Kết quả action là started/following/reused/nothing_pending.
- Kiểm tra đăng nhập và thành viên đợt trước khi đọc hoặc tạo việc.
- PostgreSQL advisory transaction lock tuần tự hóa chọn/claim của endpoint chung theo đợt; claim_job sẵn có bảo vệ nguyên tử theo đợt + kiểm soát, kể cả khi người dùng chạy từ Dashboard cũ.
- Sau khi claim, worker hiện hành thực thi, lưu kết quả, bằng chứng và lịch sử. Không tạo thêm bảng tiến độ thứ hai.
- Trạng thái giao diện tách khỏi kết luận tuân thủ: đã kiểm tra vẫn có thể Partially Compliant hoặc Non-Compliant. Chỉ hiển thị chờ duyệt khi workflow backend thực sự NEEDS_REVIEW; không đổi nghĩa COMPLETED thành người đã duyệt.

## Giới hạn

- Bộ chọn việc tiếp theo là chính sách xác định, không gọi LLM để đoán công việc. Engine đánh giá và nguồn thực thi giữ nguyên; A.6 dùng shared-company-rules.
- Lượt tự động được điều phối khi trang Hồ sơ ISO đang mở. Đóng/đổi trang thì không tiếp tục giao bước sau; job đã giao vẫn hoàn tất và lưu trên server. Đây chưa phải scheduler chạy nền bền vững.
- Chống trùng ở mức toàn kiểm soát trong một đợt, không phải hàng đợi theo từng nhân viên. Các nhiệm vụ nhắm nhân viên trong văn phòng giữ luồng riêng; không thay kết quả đánh giá toàn đợt bằng kết quả một người.
- Freshness vẫn dựa trên hash toàn snapshot, có thể yêu cầu kiểm tra lại nhiều kiểm soát khi một trường thay đổi; chưa tái đánh giá tăng dần từng nhân viên.
- Người dùng vẫn có thể chủ động yêu cầu đánh giá lại. Không tự sửa dữ liệu nghiệp vụ, tự phê duyệt hoặc kết luận chứng nhận ISO.

## Kiểm chứng ngày 08/11/2026

- 210 test Python đạt; build frontend và lint không có lỗi chặn, còn cảnh báo cũ và kích thước chunk Three.js.
- Test mới: trạng thái không đồng nhất với tuân thủ, bỏ qua mục thiếu bằng chứng/chờ duyệt, ưu tiên stale, dùng lại kết quả, theo dõi job, xử lý tranh chấp với claim cũ và chặn sai thành viên.
- API thật: bốn yêu cầu đồng thời cùng A.6.1 trả started/following/reused/reused, chỉ một job được tạo; job SUCCEEDED; yêu cầu tiếp theo reused; chưa đăng nhập trả 401. Đây là các yêu cầu cùng tài khoản, chưa phải thử UI hai người dùng riêng.
- Chưa kiểm thử bấm toàn bộ UI có đăng nhập hoặc lượt tự động nhiều bước qua trình duyệt.
