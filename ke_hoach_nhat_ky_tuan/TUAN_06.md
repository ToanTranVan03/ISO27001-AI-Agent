# Tuần 6 — Hoàn thiện bằng chứng, kiểm định và hồ sơ đánh giá tuân thủ

- Thời gian: **16/11/2026–22/11/2026 (thứ Hai–Chủ nhật).**
- Trạng thái: **Đang thực hiện.**
- Lập kế hoạch: **15/11/2026**.
- Cập nhật: **18/11/2026**.

## Mục tiêu và kế hoạch

Giữ phạm vi 56 control (8 A.6, 14 A.7, 34 A.8), ưu tiên kiểm định sâu 18 A.8 theo góp ý giảng viên. Tuần 6 tập trung bổ sung nguồn, nâng chất lượng kết luận và hoàn thiện hồ sơ nghiệm thu; không mở rộng văn phòng 3D.

- [ ] Thống nhất với giảng viên/người phụ trách rubric, phạm vi nguồn và người đánh giá được chấp nhận; ghi nhận phiên bản và căn cứ xác nhận.
- [ ] Thu nguồn có nội dung cho 37 control còn thiếu; rà mức bao phủ của 19 control đã có nguồn, đặc biệt kiểm tra lại A.6.2 chỉ trích xuất được 1 ký tự.
- [ ] Chuẩn bị bộ nguồn kiểm định mới, xác nhận lịch sử tiếp xúc và chốt snapshot trước khi chạy/chấm; không dùng lại fixture đã biết rồi gọi là tập độc lập.
- [ ] Tổ chức người đánh giá đọc và chấm trên cùng mã lượt/bằng chứng; khai đúng mức hỗ trợ, giữ riêng kết quả có AI hỗ trợ và nhãn luyện tập.
- [ ] Phân tích bất đồng và chất lượng căn cứ; lưu xử lý riêng, không sửa nhãn khóa hoặc thay đổi báo cáo cũ để tăng điểm.
- [ ] Chạy Agent trên hồ sơ hiện hành; báo cáo từng control, lỗi lần đầu/sau sửa và độ đúng so với bộ nhãn đủ điều kiện.
- [ ] Kiểm thử đầy đủ giao diện bằng các tài khoản: đọc/thu nguồn, chấm, khóa nhãn, cập nhật tiến độ, xuất báo cáo và các trường hợp bị chặn.
- [ ] Người phụ trách ghi 56 quyết định tính áp dụng, lý do và kế hoạch xử lý/duy trì; bổ sung người nhận, hạn và cách kiểm tra lại.
- [ ] Thẩm định từng tiêu chí trên nguồn hiện hành, hoàn thiện và trình người có trách nhiệm phê duyệt SoA khi đủ điều kiện.

Chỉ đánh dấu hoàn thành khi có kết quả và minh chứng. Hoàn thành phần mềm, có nguồn hoặc chạy xong không đồng nghĩa control tuân thủ hay đã nghiệm thu chuyên môn.

## Công việc chuyển tiếp từ tuần 5

- Phần mềm đã có luồng đánh giá 56 control, probe đại diện 18 A.8, chấm mù, báo cáo, SoA dự thảo và công cụ nhập gói nguồn ngoài đã chốt.
- Còn 37 control thiếu nguồn ngoài preset; nguồn A.6.2 cần kiểm tra nội dung. Chưa có bộ kiểm định mới được xác nhận trong project.
- Hai tài khoản đã nộp đủ trên cùng lượt nhưng có AI hỗ trợ/chưa khai đủ; phát hiện 9 căn cứ cần rà. Giữ kết quả này làm lịch sử đối chiếu có hỗ trợ, không coi là bộ nhãn độc lập.
- Rubric, quyết định áp dụng, thẩm định hiện hành, kiểm thử toàn UI và phê duyệt SoA chưa hoàn tất.

Các thông tin trên là **trạng thái bàn giao từ tuần 5**, không phải kết quả thực hiện tuần 6.

## Nhật ký công việc chính

| Ngày | Công việc | Kết quả / minh chứng |
|---|---|---|
| 18/11/2026 | Củng cố kiểm tra nội dung nguồn và đầu vào Agent | Chặn tài liệu quá ít/ký tự lặp khi nạp mới, lọc nguồn cũ trước suy luận, giữ lịch sử; thêm cảnh báo và việc yêu cầu nộp lại trên Phạm vi 56 |
| 18/11/2026 | Kiểm chứng và rà nguồn A.6.2 | Nguồn 1 ký tự không đưa vào model; 253 test Python, 5 test JavaScript, lint/build đạt. Không coi ngưỡng văn bản là đủ bằng chứng tuân thủ |

## Kết quả và minh chứng

- [Kiểm tra nội dung nguồn trước đánh giá](../docs/KIEM_TRA_NOI_DUNG_NGUON.md): chính sách kỹ thuật, hành vi và giới hạn.

Tài liệu bàn giao từ tuần trước:

- [Nhật ký tuần 5](TUAN_05.md).
- [Bàn giao nghiệm thu, phiếu xác nhận và checklist UI](../docs/HOAN_THIEN_NGHIEM_THU_2026_11_15.md).
- [Rà soát nguồn kiểm định trong project](../docs/RA_SOAT_NGUON_KIEM_DINH_2026_11_15.md).
- [Hướng dẫn chấm tương tác](../docs/HUONG_DAN_CHAM_THAT_A8.md).

## Vướng mắc và giới hạn

- Thiếu nguồn và xác nhận chuyên môn thực tế; công cụ không thể tự tạo phê duyệt hoặc nhãn độc lập thay con người.
- Probe lab chỉ kiểm tra tiêu chí đại diện, chưa chứng minh đầy đủ nội dung từng control hoặc toàn bộ ISMS.
- Công cụ điều khiển trình duyệt chưa kết nối ở cuối tuần 5; cần kiểm tra lại hoặc tổ chức thao tác thủ công có ghi kết quả.

Cập nhật thêm khi phát sinh, kèm hướng xử lý và phần còn chờ.

## Việc chuyển tiếp sang tuần 7

Chưa xác định. Rà kết quả cuối tuần 6 rồi chốt; chưa tạo file tuần 7–10.

## Đồng bộ GitHub

Ghi gọn theo ngày/nhánh; người push: Trần Văn Toàn. Không ghi thao tác chạy/dừng hoặc chuyển nhánh.

| Ngày | Giờ (UTC+7) | Người push | Nhánh | Nội dung chính |
|---|---|---|---|---|
| 18/11/2026 | 10:32 | Trần Văn Toàn | `Tuan6` | Kiểm tra chất lượng nguồn bằng chứng, trực quan hóa đánh giá tuân thủ và cập nhật tài liệu tuần 6 |
