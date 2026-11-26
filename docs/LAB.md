# Lab máy ảo

Phase 12 đang chờ VM Windows cô lập và quyền thử nghiệm. Tệp `configs/lab.example.yaml` dùng hostname dành cho ví dụ. Kiểm tra cấu hình và xem kế hoạch cục bộ bằng các lệnh dưới đây.

```powershell
python -m compliance_ai.cli lab-check --config configs/lab.example.yaml --read-only
python -m compliance_ai.cli lab-plan --config configs/lab.example.yaml --dry-run
```

Khi có VM, người vận hành cung cấp định danh máy, phạm vi thử, snapshot đã kiểm tra phục hồi và phê duyệt thao tác cụ thể. Ghi bằng chứng trước và sau từ nguồn độc lập. Giữ thông tin đăng nhập ngoài Git. Trạng thái `BLOCKED` từ CLI cho biết kiểm tra này chưa xác minh kết nối hoặc thay đổi nào trên VM.

## Trình xử lý cố định dành cho người vận hành

Sau khi có phê duyệt, chạy `lab/Read-ScreenLock.ps1` trong phiên của tài khoản thử nghiệm đúng máy được duyệt. Lưu kết quả làm ảnh chụp bằng chứng ban đầu. Script `lab/Set-ScreenLockTimeout.ps1` chỉ xử lý giá trị timeout tại một khóa HKCU cố định. Nó yêu cầu đúng máy và người dùng, giá trị trước khi đổi, snapshot và xác nhận. Có thể dùng `-WhatIf` để kiểm tra bước dự kiến.

Một lần đọc lại phải chứng minh giá trị cấu hình và người vận hành phải thử hành vi khóa thực tế. Chính sách nhóm hoặc trạng thái desktop có thể ảnh hưởng kết quả. Dùng snapshot đã duyệt để phục hồi. Hai script dành cho thao tác thủ công trên VM. API và công cụ mô phỏng hoạt động riêng.
