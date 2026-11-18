# Đánh giá nguồn theo lô trên server

## Sử dụng

Mở **Hồ sơ ISO** bằng tài khoản admin. Trong **Agent đánh giá theo lô trên server**, chọn giới hạn 4/12/18/56 control rồi bấm **Bắt đầu lượt**. Mặc định chỉ chọn control cần kiểm tra/tái kiểm tra hoặc lỗi; chọn **Đánh giá lại cả nguồn hiện hành** khi chủ động muốn chạy lại các control đã có kết quả.

Lô chỉ nhận control có nguồn ngoài preset qua kiểm tra nội dung tối thiểu; không bổ sung nguồn giả để chạy đủ số lượng. Tiến độ và kết quả nằm trong PostgreSQL nên đóng trang, đổi trang hoặc đăng xuất không dừng lô. Mọi thành viên cùng đợt có thể mở lại lịch sử. Chỉ admin được khởi chạy hoặc yêu cầu dừng.

**Dừng sau việc hiện tại** không hủy cưỡng bức lần gọi model đang thực hiện. Các kết quả đã lưu vẫn giữ; không tự duyệt kết luận hoặc SoA. Có thể xuất JSON từng lô và xem lý do lỗi/bỏ qua từng control.

## Kiểm soát

- Một lô hoạt động cho mỗi đợt, bảo vệ bằng khóa và unique index PostgreSQL. Yêu cầu trùng trả về lô đang chạy, không tạo thêm worker.
- Danh sách hữu hạn; mỗi control tối đa một lần/lô. Không tự chạy lặp control lỗi hoặc chờ bằng chứng.
- Chốt token nguồn/tiêu chí/rubric khi lập lô, kiểm tra lại trước và sau khi claim job. Nếu nguồn đổi, bỏ qua và ghi rõ; không gọi model trên một gói đầu vào đã đổi mà vẫn báo là gói cũ.
- Sử dụng khóa job hiện có: control bận được ghi bỏ qua. Lưu kết quả từng control ngay khi hoàn tất.
- Kết thúc lô nghĩa là đã duyệt qua danh sách, không phải mọi job thành công hoặc control tuân thủ. Giao diện tách số kết quả lưu, lỗi và bỏ qua.
- Nếu API khởi động lại, job/lô dở dang được đánh dấu gián đoạn. Không tự tiếp tục hoặc tự đánh giá lại sau restart; admin rà kết quả rồi tạo lô mới.

Đây vẫn là worker trong một tiến trình Uvicorn, chưa phải hệ thống worker phân tán. Giữ giới hạn một API process như cấu hình hiện tại. Dữ liệu tiến độ được lưu bền vững nhưng thực thi không tự sống sót qua việc dừng API/máy.

## Kiểm chứng

302 test Python, 7 test JavaScript và lint/build đạt ở mốc triển khai. Kiểm tra PostgreSQL thật bằng giao dịch rollback xác nhận tạo lô, theo dõi yêu cầu trùng, ghi nhận dừng và khóa worker; không để lại dữ liệu thử. Các test kiểm tra nguồn đổi trước/sau claim, lỗi model/worker, không retry vô hạn và quyền theo đợt.

Lượt đánh giá thực tế trên nguồn lab hiện hành được ghi riêng với kết quả thực thi; không dùng để thay bộ kiểm định mới, nhãn người thật hoặc độ đúng so với người đánh giá độc lập.

## Kiểm soát đầu vào model sau lượt thực tế

Nhánh hồ sơ dùng Qwen2.5:7b được cấu hình context 16384 và phản hồi tối đa 512 token. Đầu vào được kiểm tra tổng byte UTF-8 trước khi gọi model (tối đa 14336 byte cho prompt); quá giới hạn thì báo lỗi rõ ràng và yêu cầu chia nguồn, không cắt bỏ nội dung âm thầm.

Các bản capture chỉ khác thông tin nhập nhưng giống toàn bộ nội dung quan sát có thể được đóng gói chung, giữ mọi evidence ID và provenance. Khác thời điểm quan sát, tài sản, artifact hoặc phạm vi thì không gộp. Bản gốc trong database không đổi. Đây là giảm lặp đầu vào, không sinh dữ kiện hay tóm tắt thay nội dung gốc.

Nếu lần đánh giá mới nhất lỗi, giao diện ghi lỗi và chỉ giữ kết luận cũ trong lịch sử, không tô xanh kết luận cũ thành kết quả hiện hành. Bản sửa qua 308 test Python; kiểm tra lại model thật và các lần lỗi được báo riêng để không trộn thành số liệu độ đúng.
