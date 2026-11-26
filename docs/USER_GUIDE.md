# Trình diễn cục bộ

## Chuẩn bị

Khởi động PostgreSQL, áp dụng migration, tạo dữ liệu ABC và tạo tài khoản mẫu theo README. Mở Streamlit. Dùng cửa sổ riêng hoặc đăng xuất khi đổi vai trò.

## NV015 và xác minh

1. Đăng nhập bằng `abc-auditor`. Chọn ABC, đánh giá NV015 và lưu mã đánh giá.
2. Lập kế hoạch từ H09. Lưu mã hành động rồi đăng nhập `abc-admin`. Mở đánh giá bằng mã đã lưu và mở hành động. Kiểm tra đích, phiên bản và chế độ mô phỏng.
3. Duyệt, thực thi và đọc lại nguồn. Trạng thái `VERIFIED` yêu cầu bằng chứng từ phiên bản mới.
4. Chạy đánh giá mới rồi lập kế hoạch M01 bằng auditor. Lặp bước duyệt và xác minh để thu hồi danh sách quyền mô phỏng.
5. Lập phiếu D02. Phiếu ở `WAITING_EXTERNAL` khi thiếu biên bản trả thiết bị. Xuất báo cáo khoảng cách, khắc phục và nhật ký. Giữ các lần đánh giá cùng mã nhân viên và phiên bản chính sách khi đối chiếu trước/sau.

### Ghi nhận kho đã nhận laptop của NV015

Sau khi admin thực thi phiếu D02, chạy **đánh giá mới** cho NV015. Mở **Căn cứ, điểm và độ bao phủ** và tìm D02. Sao chép `target_id` của thiết bị, `observed.request_id` của phiếu và `observed.revision` của hồ sơ tài sản.

Trong vai người vận hành kho mô phỏng, chạy lệnh sau ở thư mục dự án với ba giá trị vừa đọc.

```powershell
.\.venv\Scripts\python.exe -m compliance_ai.cli demo-asset-receive --employee NV015 --asset <target_id> --ticket <request_id> --revision <revision>
```

Lệnh dùng kết nối quản trị cục bộ của mô phỏng ABC và trả về `receipt_id` cùng thời điểm kho nhận thiết bị. Mở lại hành động D02 bằng tài khoản admin rồi bấm **Đọc lại nguồn để xác minh**. Đối chiếu `verification.receipt_id` với mã kho đã cấp. Xem `due_date` và `return_timing` để biết hạn và kết quả thời gian. Đánh giá mới ghi đạt nếu trả đúng hạn, đạt một phần nếu đã trả trễ và không đạt nếu còn giữ tài sản quá hạn. Khi còn trong hạn mà chưa có biên nhận, hệ thống chờ bằng chứng và vẫn cho phép lập phiếu. Gửi lại đúng lệnh ban đầu trả về cùng biên nhận.

## Đào tạo

1. Đăng nhập `abc-nv001`. Trả lời câu hỏi ban đầu và câu hỏi bổ sung nếu có.
2. Auditor đánh giá NV001 và lập kế hoạch H03. Admin thực thi giao bài. Lần xác minh đầu sẽ chờ.
3. Nhân viên tự xác nhận bài học rồi mở tình huống kiểm tra lại. Khi đạt ngưỡng, admin đọc lại nguồn của hành động để xác minh.
4. Mặc định phỏng vấn dùng rubric theo cụm từ tiếng Việt. Khi đã cấu hình Ollama, có thể chọn chấm ngữ nghĩa cục bộ trên màn hình trả lời. Nội dung nghi vấn, lỗi model hoặc trích dẫn không khớp chuyển sang xem xét. Những sự kiện này là dữ liệu của người tham gia mô phỏng; kết quả chưa được đối chiếu chuyên gia.

## Bản vá, cấu hình và khôi phục mô phỏng

Auditor đánh giá NV015 rồi lập kế hoạch S04 (bản vá) hoặc S05 (khóa màn hình). Admin độc lập duyệt, thực thi và đọc lại nguồn. Hai thao tác có mức rủi ro trung bình, lưu snapshot của các trường thay đổi. Người đã duyệt có thể bấm **Khôi phục cấu hình mô phỏng trước thay đổi**. Sau đó chạy đánh giá mới để thấy sai lệch trở lại; bản báo cáo trước vẫn giữ nguyên.

Khôi phục bị chặn nếu endpoint có thêm thay đổi sau hành động đó. Ví dụ thực thi S04 rồi S05 trên cùng endpoint sẽ khiến snapshot S04 cũ; không được dùng nó ghi đè trạng thái mới. Chức năng này chưa khôi phục máy ảo hoặc bản vá hệ điều hành thật.

## Lệnh tham chiếu

Để giữ yêu cầu trước khi đánh giá, chọn **Lưu yêu cầu để chạy sau** và lưu mã hiện trên màn hình. Đăng nhập lại bằng cùng tài khoản, mở yêu cầu rồi chọn **Chạy yêu cầu đã lưu**. Khi hoàn tất, dùng **Xem kết quả yêu cầu** để mở báo cáo.

Trang **Benchmark** trong thanh bên nhận tệp `dashboard.json` do lệnh benchmark xuất. Tệp chứa chế độ thực nghiệm, số ca, số doanh nghiệp và các chỉ số tổng hợp. Chi tiết phân tầng nằm trong `metrics.json`.

### Trình diễn MFA của NV001

1. Dùng `abc-auditor` đánh giá NV001 trong ABC. Mở **Căn cứ, điểm và độ bao phủ**, tìm S02 và lấy `observed.revision` của tài khoản.
2. Nếu hồ sơ đang đạt, người vận hành có thể tạo tình huống thiếu MFA trên hồ sơ demo đã chọn. Chạy lệnh dưới đây từ thư mục dự án, thay `<revision>` bằng số vừa đọc. Hai tham số cuối là trạng thái do nguồn định danh mô phỏng quan sát được.

   ```powershell
   .\.venv\Scripts\python.exe -m compliance_ai.cli demo-mfa-observe --employee NV001 --revision <revision> --registered no --enforced no
   ```

3. Chạy đánh giá mới, lập kế hoạch S02. Dùng `abc-admin` thực thi yêu cầu. Xác minh lúc này trả `WAITING_EXTERNAL`. Đăng nhập `abc-nv001` để thấy mã yêu cầu đăng ký MFA.
4. Lấy revision của tài khoản bằng **lần đánh giá mới** sau khi tạo yêu cầu. Chạy lại lệnh với `--registered yes --enforced no`. S02 đạt một phần và hành động vẫn chờ. Dùng revision được lệnh trả về cho lần tiếp theo với `--registered yes --enforced yes`.
5. Admin đọc lại nguồn để xác minh. Kết quả `VERIFIED` có `identity_event_id` trùng mã sự kiện cuối. Đánh giá mới hiển thị S02 đạt. CLI chỉ nhập quan sát giả lập vào ABC và cần kết nối quản trị DB cục bộ của người vận hành.

### Trình diễn cam kết bảo mật của NV001

1. Dùng `abc-auditor` đánh giá NV001, chọn H06 và lập kế hoạch. Hồ sơ cũ chỉ có cờ đã ký sẽ hiển thị thiếu bằng chứng phiên bản. Lưu mã đánh giá và mã hành động.
2. Dùng `abc-admin` mở đánh giá và hành động trên. Kiểm tra nội dung cam kết, thực thi yêu cầu rồi bấm xác minh. Hành động chờ nhân viên ở trạng thái `WAITING_EXTERNAL`.
3. Dùng `abc-nv001` mở màn hình nhân viên, đọc văn bản rồi chọn **Tôi đã đọc và xác nhận cam kết mô phỏng**. Màn hình hiển thị mã biên nhận.
4. Admin xác minh lại hành động. Đối chiếu `receipt_id` với mã nhân viên đã nhận. Chạy đánh giá mới cho NV001 để xem H06 đạt và mã bằng chứng trong báo cáo. Nếu hồ sơ hiện đã có yêu cầu đang chờ, dùng mã `request_id` trong bằng chứng của H06 để mở yêu cầu đó.

Xem OpenAPI tại `/docs`. Các phản hồi chứa mã bằng chứng và phiên bản nguồn. Đây là rubric nghiên cứu. Đối chiếu tài liệu cấp phép và đánh giá chuyên gia là bước riêng.
