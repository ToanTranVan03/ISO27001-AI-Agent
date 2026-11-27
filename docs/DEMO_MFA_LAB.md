# Demo hành động khắc phục MFA trong lab

Ca React/khắc phục trước đây dùng các tệp TXT tự soạn với enrolled/enforced, có lưu phát hiện, nháp Qwen, giao việc, thẩm định theo tiêu chí và báo cáo. Kho doanh nghiệp cũng có số liệu IAM mô phỏng. Hai nguồn này không truy vấn chính sách một IAM thực. Probe A.8.5 hiện tại dùng dịch vụ TCP loopback với mật khẩu PBKDF2 và mã HMAC theo thời gian, đọc file auth.json nội bộ. Compose chạy container không có mạng ngoài và không có API quản trị IAM.

## Ca thực thi dùng một lần

```powershell
.venv\Scripts\python.exe -m lab_a8.mfa_remediation_demo --output work/mfa-demo-new.json
```

1. Đọc trạng thái và thực hiện phép thử đăng nhập cho tài khoản labadmin-mfa-demo. Quan sát đồng thời có mốc thời gian, nguồn, chính sách LAB-ADMIN-MFA và tiêu chí second_factor_enforced.
2. Xem nháp thao tác và mã đề xuất in ra. Người vận hành nhập tên và gõ APPROVE theo sau bởi mã đề xuất. Để trống nếu từ chối. Tên ghi trong CLI là khai báo của người vận hành.
3. Tool chỉ đổi require_otp trong file chính sách riêng của lần chạy. Không nhận địa chỉ, tài khoản, đường dẫn chính sách hoặc lệnh tùy ý. Thu lại chính sách và thực hiện các kết nối riêng có/không có yếu tố thứ hai.
4. Xem receipt JSON. Kết quả VERIFIED_MET chỉ áp dụng tiêu chí hành vi của dịch vụ tổng hợp. Các trạng thái EXECUTION_FAILED, VERIFIED_NOT_MET và VERIFICATION_UNAVAILABLE được giữ riêng. File chính sách tạm dọn sau khi kết thúc.

## Cách chuyển biên nhận thủ công của bản CLI

Trong đợt mô phỏng riêng, nộp phần before làm nguồn A.8.5 rồi lập phát hiện và duyệt giao việc qua hệ thống. Chạy CLI ở máy lab, nộp receipt JSON gồm approval, execution, before, after qua hồ sơ A.8.5, gắn mã nguồn vào hành động rồi thẩm định và xác minh theo tiêu chí. Báo cáo khắc phục hiện có dẫn ID/hash nguồn; mở bản gốc để xem chi tiết thực thi và lần đọc lại. Đây là luồng chuyển nguồn thủ công. CLI có cổng duyệt riêng; chưa có cầu nối để lấy người duyệt đã xác thực từ React hoặc tự ghi biên nhận vào báo cáo.

Minh chứng chạy trên máy: [receipt tổng hợp](../work/mfa-active-lab.json). Phê duyệt trong receipt này là callback của bài kiểm tra tự động. Trước thay đổi đăng nhập thiếu yếu tố thứ hai trả 200. Sau thay đổi trả 403, đăng nhập đủ yếu tố vẫn trả 200. Kiểm thử nhắm vào bốn ca: chưa duyệt, thành công, tool lỗi và tool báo thành công khi đọc lại vẫn trượt. Hai ca lỗi dùng thay thế hàm ghi chính sách trong test, giữ phép đọc/thử loopback thật. Chưa chạy lại React/PostgreSQL/PDF/Excel cho receipt mới.

Muốn tự động hóa trên IAM lab chuyên dụng cần API đọc và ghi cho đối tượng thử, thông tin nhận diện môi trường, tài khoản dịch vụ có quyền tối thiểu, phê duyệt gắn với phiên bản đề xuất và lưu biên nhận thực thi. Ca CLI hiện không cần Docker hoặc IAM bên ngoài.

## Chạy từ giao diện khắc phục

Dùng một đợt thử riêng và bật ISO_MFA_DEMO_ENABLED=1 trong tiến trình backend lab. Mở A.8.5, lập phát hiện và đầu việc với đích labadmin-mfa-demo / LAB-ADMIN-MFA, rồi duyệt giao việc. Tư vấn mở đầu việc đã duyệt và chọn **Xác nhận chạy công cụ MFA lab**. Server kiểm quyền, phiên bản, lịch sử duyệt, rubric và bối cảnh. Đích và thao tác được cố định trong mã. Khi tắt cờ, giao diện chỉ hướng dẫn người phụ trách thực hiện và nộp nguồn.

Đầu việc giữ biên nhận trước/sau, người duyệt, người bấm chạy, công cụ và kết quả đọc lại. JSON báo cáo chứa biên nhận; Excel có sheet MFA lab và PDF có mục tương ứng. Biên nhận kỹ thuật không tự cập nhật kết luận. Trong ca thử, người thực hiện nộp bản sao biên nhận làm nguồn, sau đó tư vấn thẩm định và xác minh bằng luồng hiện có. Lần đo ban đầu trong biên nhận chạy ngay trước khi ghi chính sách, còn hồ sơ để mở phát hiện vẫn dùng dữ liệu mô phỏng chuẩn bị trước.

Chạy nghiệm thu với database tạm:

```powershell
npm --prefix frontend-react run build
.venv\Scripts\python.exe run_isolated_acceptance.py --execute --remediation --remediation-only --output work/mfa-ui-tool-new.json
```

Runner bật cờ trên backend thử. Trong test trình duyệt chỉ thao tác chạy công cụ và tải báo cáo qua React; tạo/duyệt đầu việc, nộp nguồn và thẩm định chạy qua API thật. Môi trường chưa có connector IAM bên ngoài. Ca bàn giao laptop tiếp tục theo quy trình người thực hiện và người xác minh riêng.

Kết quả bản React: [Biên nhận nghiệm thu](../work/mfa-ui-tool.json), [PDF](../work/mfa-ui-delivery/mfa-before-after.pdf) và [Excel](../work/mfa-ui-delivery/mfa-before-after.xlsx). Lượt thử chặn chạy trước duyệt, chặn vai trò nhân viên và chặn chạy lặp. Edge gọi công cụ, hiện VERIFIED_MET và tải cả hai báo cáo. Kiểm nội dung PDF/XLSX có đối tượng, kết quả 403 khi thiếu yếu tố và người duyệt. Dữ liệu giữ sau restart backend. Database thử đã dọn và số dòng các bảng chính được theo dõi giữ nguyên.
