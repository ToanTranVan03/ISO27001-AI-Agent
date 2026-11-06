# Bình luận điều khiển nhân viên trong lab

## Cách thử

Mở http://127.0.0.1:5173, đăng nhập và chọn **Mô phỏng 3D**.
Bản đồ **Văn phòng tương tác** và bảng **Bình luận → nhân vật của bạn** nằm cạnh nhau ở đầu trang trên màn hình rộng.
Có thể chuyển sang **Toàn cảnh 3D** để dùng mô hình cũ.

Luồng chính là **một bình luận → một nhân vật → một hành động riêng**.
Chọn người trong danh sách hoặc trên bản đồ, nhập `đi làm` rồi gửi để người đó
vào ca và làm việc bằng một lệnh. Những người khác giữ hoạt động riêng;
không cần đưa cả văn phòng vào cùng trạng thái. Các nút ra lệnh đồng loạt đã bỏ
khỏi giao diện chính. Danh sách hiển thị trạng thái từng người; bình luận mới
nổi trên đúng nhân vật trong 12 giây, người đang chọn luôn hiện lệnh gần nhất.

Chọn nhân viên trên bản đồ hoặc trong danh sách; cũng có thể gõ trực tiếp
`@EMP-025 /cai-app-la` để chỉ định người nhận.

| Lệnh | Người nhận | Hoạt động |
|---|---|---|
| `/di-lam` hoặc `đi làm`, `tham gia` | Một nhân viên đang chọn | Vào ca và làm việc bằng một lệnh; máy còn bị bảo vệ vẫn khóa |
| `/vao-ca` hoặc `vào ca` | Một người đang chọn | Nhận ca, về vị trí làm việc |
| `/lam-viec` hoặc `làm việc` | Một người đang chọn | Hoạt động làm việc bình thường |
| `/nghi` hoặc `nghỉ giải lao` | Một người đang chọn | Ghi nhật ký nghỉ theo quy trình, chuyển tới góc nghỉ |
| `/khoa-may` hoặc `khóa màn hình` | Một người đang chọn | Ghi sự kiện khóa màn hình |
| `/roi-may` hoặc `rời máy` | Một người đang chọn | Rời bàn giữ nguyên màn hình; chỉ khi còn mở mới tạo dấu hiệu A.7.7 |
| `/usb-la` hoặc `cắm USB lạ` | Một người đang chọn | USB chưa đăng ký trên máy riêng; Agent kiểm tra A.7.10 |
| `/cai-app-la` hoặc `cài phần mềm chưa duyệt` | Một người đang chọn | Cài ứng dụng chưa duyệt trên máy riêng; Agent kiểm tra A.8.19 |
| `/rut-usb` | Một người đang chọn | Rút USB đang cắm, giữ nguyên lịch sử vi phạm |
| `/go-app` | Một người đang chọn | Gỡ app chưa duyệt hoặc đã bị chặn |
| `/mo-khoa` | Một người đang chọn | Mở lại máy sau khi hết sự kiện chờ xử lý và dấu hiệu đang hoạt động |
| `/tan-ca` | Một người đang chọn | Kết thúc ca khi máy đã khóa, USB đã rút và không còn sự kiện chưa xử lý |

1. Chọn bất kỳ nhân viên, gửi `/vao-ca` rồi `/lam-viec` để vào ca và mở màn hình làm việc.
2. Gửi `/usb-la`. Sự kiện được ghi vào đúng máy riêng `OFFICE-EMP-xxx` của nhân viên đó.
3. Bộ giám sát được bật khi gửi lệnh. Chờ quét và xử lý; dòng bình luận sẽ liên kết hồ sơ A.7.10 khi có kết quả.
4. Có thể thử `/cai-app-la` trên một nhân viên đang làm việc khác để tạo hồ sơ A.8.19; hoặc `/roi-may` khi màn hình mở để thử A.7.7.
5. Nhấn kết quả dưới bình luận để đọc hồ sơ. Lịch sử 30 bình luận gần nhất được lưu trong PostgreSQL, giữ qua tải lại trang.

Chu kỳ chờ giữa các lần quét là 5 giây; thời gian suy luận và xử lý phụ thuộc Ollama.
Không đảm bảo xử lý xong trong 5 giây. Có thể tắt giám sát tại phần Chat với AI Agent.

## Luồng dữ liệu

`Bình luận → kiểm tra lệnh/nhân viên → ghi telemetry → bộ giám sát độc lập → phân tích và công cụ xử lý → xác minh → liên kết hồ sơ về bình luận`.

API nhận lệnh cập nhật trạng thái máy và ghi nhật ký trong cùng transaction; không trực tiếp gọi xử lý sự cố hoặc trả sẵn điều khoản vi phạm.
Luật quét đối chiếu loại sự kiện; Ollama lập phương án xử lý theo các công cụ được phép,
với policy fallback của project khi cần. Giao diện hiển thị tên mô hình/nguồn quyết định.
Không nên gọi toàn bộ hệ thống là nhận diện thuần AI hay nói mô hình tự học luật ISO.

Lệnh được giới hạn bằng danh sách và các cách viết tiếng Việt có/không dấu.
Phủ định (`không cắm USB lạ`), ghép nhiều lệnh, lệnh không hỗ trợ và chọn sai nhân viên bị từ chối.
Mỗi yêu cầu có UUID chống thực thi trùng khi retry. API kiểm tra đăng nhập và quyền thành viên đợt đánh giá.
Hành động chỉ cập nhật dữ liệu doanh nghiệp giả lập, không cắm USB/cài phần mềm trên máy thật.

## Quy tắc tương tác

- Mỗi người có một máy `OFFICE-EMP-xxx`; trạng thái ca, vị trí, màn hình, USB, phần mềm và cô lập được lưu bền trong PostgreSQL.
- Chưa vào ca không thể thao tác máy. Đang nghỉ phải quay lại bàn. Máy bị cô lập/khóa không thể cài app hoặc cắm USB mới.
- `/nghi` khóa màn hình trước khi rời bàn; `/roi-may` giữ nguyên trạng thái. Rời máy đã khóa không bị tạo vi phạm giả.
- Quay lại bàn không tự gỡ cô lập do Agent đặt. Lệnh bình thường không xóa dấu hiệu hay sự kiện cũ.
- Agent dùng đúng employee ID và máy quan sát được, không dùng nhân viên mẫu trong catalog.
- Cùng một người chỉ được cập nhật máy tuần tự. Khi Agent đang xử lý, yêu cầu mới bị từ chối kèm lý do; người khác vẫn có thể thao tác.
- API trạng thái trả danh sách lệnh khả dụng và lý do chặn. Giao diện vô hiệu hóa các nút không hợp lệ, nhưng backend luôn kiểm tra lại.
- Vị trí nhân vật lấy từ trạng thái bền, không phụ thuộc 30 bình luận gần nhất. Cảnh báo còn mở không biến mất khi gửi một lệnh bình thường.
- Nút khu vực điền lệnh vào ô bình luận; nhấn Gửi để thực hiện.

## Phạm vi

- Có 14 nhân viên trên bản đồ; 12 loại lệnh dùng riêng cho bất kỳ người nào trong 14 người. Phạm vi tương tác này gồm ba hành vi vi phạm; không đồng nghĩa toàn bộ 56 điều khoản đều đã có lệnh hành vi riêng.
- Bình luận trong ứng dụng, chưa kết nối bình luận livestream TikTok.
- Bản đồ văn phòng minh họa gồm bàn làm việc, khu giám sát, lễ tân, góc nghỉ; nhân viên có tên và lời thoại, Agent có đường tuần tra. Bản đồ 3D được giữ ở chế độ riêng.
- Lệnh tạo hoạt động bình thường không được dùng như bằng chứng chứng nhận tuân thủ toàn bộ ISO.
- Bộ giám sát nằm trong tiến trình FastAPI, cần gửi lệnh hoặc bật giám sát lại sau khi restart.
- Kết quả từ lịch sử được đối chiếu bằng event ID, không gắn cảnh báo theo nội dung bình luận đoán trước.

## Kiểm tra

Đã kiểm tra unit test về cú pháp, phủ định, nhân viên, đăng nhập và quyền truy cập.
Đã chạy trên PostgreSQL/Ollama local: lệnh thường không có sự cố liên kết; USB/app có hồ sơ
A.7.10/A.8.19 và xác minh thành công; retry không tạo trùng; lệnh sai bị từ chối.
Đợt bổ sung đã kiểm tra cả 14 người nhận lệnh vào ca, lệnh nghỉ/khóa máy không có cảnh báo liên kết,
và rời máy không khóa được phát hiện A.7.7, xử lý và xác minh bằng Qwen2.5:7b.
136 test Python và 6 test JavaScript về văn phòng đạt. Đã chạy luồng trạng thái trên ba nhân viên khác nhau: điều kiện trước lệnh,
rời máy đã khóa không vi phạm, cả ba loại vi phạm được xử lý đúng máy, sau đó dọn dẹp và tan ca.
Đã kiểm tra ảnh SVG dựng từ chính component và dữ liệu local;
chưa xác minh toàn bộ thao tác trực tiếp trên trình duyệt.

## Tham khảo

Ý tưởng sử dụng tương tác để nhân vật hành động trong không gian chung được tham khảo từ
[hướng dẫn Chùa Sen](https://chuasen.com/huong-dan-di-chua-online/).
Ngày 05/11/2026 đã trích và xem các khung hình ở nhiều mốc của bốn MP4 local người dùng gửi:
`D:\đi chùa onl.mp4` (33,3 giây), `D:\đi học onl.mp4` (60 giây),
`D:\đi lễ onl.mp4` (103,33 giây), `D:\đi tù onl.mp4` (36,37 giây).
Điểm áp dụng: nhiều nhân vật mang tên, lệnh ngắn, lời thoại nổi, khu vực hoạt động và nhật ký phản hồi.
Hình ảnh trong video không chứng minh phần mềm đó sử dụng mô hình AI; cơ chế xử lý lệnh có thể là luật.
Bản bổ sung dùng cảnh văn phòng và nhân vật tự vẽ bằng SVG, không sao chép tài sản hình ảnh từ video.
