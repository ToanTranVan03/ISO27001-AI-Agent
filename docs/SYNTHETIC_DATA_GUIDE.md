# Dữ liệu mô phỏng nhiều doanh nghiệp

Dữ liệu sinh là **development fixtures**, không phải nguồn audit thật, bộ kiểm định độc lập hoặc dữ liệu huấn luyện. Không upload `design-key.json` vào Agent. Không dùng các nhãn thiết kế để công bố accuracy chuyên gia.

## Tạo và kiểm tra

```powershell
.venv\Scripts\python.exe generate_enterprise_dataset.py generate --output work/demo-new --sizes 30,100,500 --months 24 --seed 27001 --start 2024-01-01
.venv\Scripts\python.exe generate_enterprise_dataset.py validate --output work/demo-new
```

Mỗi doanh nghiệp có profile và các thư mục tháng, people/accounts/assets/screening CSV, backup và quan sát mâu thuẫn JSON, khóa thiết kế riêng. File có enterprise/period/employee ID liên kết; missing không tự biến thành noncompliant. Cùng tham số tạo cùng nội dung/hash; không ghi đè thư mục cũ. CLI giới hạn 10 doanh nghiệp, 5.000 người/doanh nghiệp, 60 tháng, 300.000 dòng người–kỳ; importer danh mục hiện giới hạn 999 người/doanh nghiệp do schema mã EMP-001..EMP-999.

Trên UI: **Doanh nghiệp → Khách hàng tư vấn → Sinh bộ dữ liệu mô phỏng**, chọn quy mô/tháng rồi tải ZIP. Web giới hạn 3 doanh nghiệp, 500 người/doanh nghiệp, 24 tháng và 20.000 dòng người–kỳ. Gói ZIP không tự nhập vào đợt đang mở.

## Nhập vào khách hàng thử mới

Kiểm tra trước, chưa kết nối API hoặc ghi DB:

```powershell
.venv\Scripts\python.exe import_enterprise_dataset.py --dataset work/demo-new --receipt work/demo-import-receipt.json
```

Nhập thật dùng biến môi trường **ISO_IMPORT_USERNAME**, **ISO_IMPORT_PASSWORD** cho tài khoản quản trị đã được cấp. Không ghi mật khẩu vào script/Git/biên nhận. Sau đó thêm `--execute`; API mặc định `http://127.0.0.1:8000`. Importer chỉ nhận API local, chỉ tạo khách hàng mới; không có tham số ghi vào client/assessment đang có.

```powershell
.venv\Scripts\python.exe import_enterprise_dataset.py --dataset work/demo-new --receipt work/demo-import-receipt.json --execute
```

Receipt giữ từng khách hàng/kỳ/file, lỗi và evidence ID; không chứa token/password. Nếu lỗi giữa chừng, các mục đã lưu vẫn tồn tại và receipt chỉ rõ phần đã làm; không báo cả lô thành công. Chưa có resume tự động theo receipt: không chạy lại một cách mù quáng để tạo trùng khách hàng. Có thể tiếp tục từng nguồn qua UI. Không tự xóa partial client đã có audit.

Import danh mục nhân viên/tài khoản/tài sản là khai báo, không xác minh. Các CSV/JSON liên quan được nộp qua source API đúng control/type với dấu SYNTHETIC, xuất xứ, thời điểm quan sát và hash. Không nạp design key; không gọi model, không nộp review, không tạo quyết định tính áp dụng hoặc phê duyệt. Sau import, quản trị chọn đợt và chủ động chạy batch nguồn hiện hành; nguồn quá input budget có thể cần tách theo phạm vi.

**Bộ 30/100/500 × 24 tháng mới được kiểm sinh/hash, chưa được nạp đầy đủ và suy luận LLM toàn bộ.** Bài ghi thật được kiểm trên bộ nhỏ 6 người × 2 tháng trong database cô lập; hai mức kiểm thử không được đánh tráo.

## Xóa hoặc khởi tạo lại file mô phỏng

```powershell
.venv\Scripts\python.exe generate_enterprise_dataset.py remove --output work/demo-new
```

Chỉ xóa một thư mục con `work/` có manifest đúng protocol, toàn bộ hash khớp và không có file lạ/symlink. Tệp người dùng thêm hoặc dữ liệu bị sửa làm thao tác bị chặn. Không chạm DB, dữ liệu gốc hoặc các thư mục khác. Khởi tạo lại bằng lệnh generate với thư mục mới hoặc sau khi dọn đúng bộ; giữ receipt/benchmark ở nơi khác. Dọn dữ liệu DB demo nên dùng runner database cô lập, không xóa cascade doanh nghiệp chính.
