# Kiểm thử ghi thật trên môi trường cô lập

Ngày triển khai: 21/11/2026. Mục tiêu: kiểm tra luồng phần mềm bằng HTTP, PostgreSQL, tệp gốc và Edge thật; không giả lập phản hồi API. Dữ liệu nghiệp vụ vẫn là **dữ liệu kiểm thử tổng hợp**, không phải hồ sơ thật, chấm độc lập hoặc phê duyệt chuyên môn của nhóm.

## Phạm vi

Runner `run_isolated_acceptance.py` tạo database local có tên `iso_acceptance_<12 ký tự hex>`, mật khẩu tài khoản thử ngẫu nhiên và backend trên cổng trống. Kho A.8, quyết định, thẩm định và tệp nguồn đều chuyển vào thư mục `work/<database>/`; không dùng `data/` của đợt chính.

Tài khoản thử là `release_admin`, `release_rater1`, `release_rater2`. Không đăng nhập hoặc giả danh Khoa/Tú để tạo nhãn nghiên cứu. Tên hiển thị, căn cứ và quyết định trong bài test đều ghi rõ `SYNTHETIC TEST`.

Kịch bản kiểm tra:

1. Tiếp nhận nguồn qua UI, lưu PostgreSQL và tải lại byte bản gốc; chặn form thẩm định dùng token trước khi nguồn đổi.
2. Lưu thẩm định từng tiêu chí và kế hoạch có người nhận/hạn/cách kiểm tra lại.
3. Chuẩn bị phạm vi **cố ý đơn giản chỉ để thử gate**: áp dụng một control và loại trừ 55 control bằng quyết định tổng hợp. Không phải mô hình tính áp dụng của doanh nghiệp chính.
4. Xác nhận rubric và duyệt SoA trong database thử, sau đó thay nguồn để kiểm tra thẩm định/phê duyệt cũ hết hiện hành; fingerprint cũ bị từ chối.
5. Chạy replay A.8 bằng rules (không phải kết quả LLM mới), hai tài khoản thử nộp tổng cộng 36 nhãn; khai có AI hỗ trợ/đã xem. Kiểm tra khóa nhãn, lưu qua tải lại, tách từng người và không tạo người đối chiếu độc lập.

Điều kiện hoàn tất bài thử là toàn bộ assertion đạt. Một lần chạy đi qua nhiều bước nhưng lỗi cuối vẫn được báo `passed=false`; không xóa báo cáo lỗi để chỉ giữ bản đẹp.

## Chạy lại

PostgreSQL local đang chạy, `.env` có `DATABASE_URL`, tài khoản DB được phép tạo database; cài dependencies và Microsoft Edge. Build frontend trước:

```powershell
npm run build --prefix frontend-react
.venv\Scripts\python.exe run_isolated_acceptance.py --execute --output work/isolated-write-new.json
```

Runner từ chối DB không phải localhost, chỉ dọn tên DB kiểm thử đã tạo, không ghi đè báo cáo có sẵn. Kết thúc sẽ dừng backend thử và xóa database thử; log/tệp thử còn trong `work/` để đối chiếu. Không dùng báo cáo test hoặc thư mục này làm bộ kiểm định độc lập.

`main_table_counts_unchanged` chỉ so sánh số dòng các bảng `evidence`, `evaluations`, `team_users` của database chính trước/sau. Đây không phải chứng minh mọi byte của toàn database không đổi; cách ly DB/kho tệp và tài khoản thử là lớp bảo vệ chính.

## Kết quả ngày 21/11/2026

- [Lần 1](a8-results/isolated-write-2026-11-21.json): không đạt do kịch bản đọc tổng hợp bằng token admin đã đăng xuất; không sửa báo cáo thành đạt.
- [Lần 2](a8-results/isolated-write-2026-11-21-r2.json): không đạt do kịch bản chọn thẩm định trước khi UI tải xong snapshot nguồn mới; bổ sung chờ trạng thái tiếp nhận/token, không nới gate backend.
- [Lần 3](a8-results/isolated-write-2026-11-21-r3.json): đạt toàn bộ kịch bản, `api_mocked=false`, `database_dropped=true`, `main_table_counts_unchanged=true`. Nhãn tổng hợp được giữ riêng trong kho thử; không nhập vào đợt chính. Không có kết quả LLM hoặc accuracy nghiên cứu mới.
- 324 test Python đạt, gồm 5 test chặn tên database dọn dẹp không hợp lệ. Database thử được xóa ở cả các lần lỗi; giữ báo cáo và log để đối chiếu.

## Giới hạn nghiệm thu thực tế

Ngay cả khi bài thử đạt, chưa thể tích hoàn tất rubric được thầy chấp nhận, nguồn đủ 56 control, tập kiểm định chưa dùng phát triển, nhãn người đánh giá độc lập hoặc SoA doanh nghiệp được người có trách nhiệm phê duyệt. Các mục đó vẫn cần đầu vào và xác nhận thực tế.
