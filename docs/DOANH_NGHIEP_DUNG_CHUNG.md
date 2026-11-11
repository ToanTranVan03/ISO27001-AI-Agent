# Doanh nghiệp dùng chung theo đợt đánh giá

PostgreSQL là nguồn nhân viên, tài khoản, thiết bị và hồ sơ của các màn hình hiện hành. `backend/company_storage.py` khởi tạo kho độc lập với văn phòng/mission/SOC đã gỡ; seed tại `lab_company/inventory_seed.json`. Migration chỉ bổ sung, không ghi đè hoặc xóa dữ liệu cũ.

## Định danh và nguồn

- Nhân viên dùng EMP-xxx; HF-xxx là mã nhập tương thích cùng số thứ tự.
- Thiết bị cá nhân giữ mã OFFICE-EMP-xxx để bảo toàn liên kết bằng chứng, không có nghĩa còn giao diện văn phòng.
- Tài khoản có chủ sở hữu và hệ thống. Quan hệ tài sản nhiều người được giữ trong snapshot.
- Hồ sơ chưa biết giữ null; không suy đã ký NDA, có MFA hoặc mã hóa từ việc tồn tại tài khoản.
- Kiểm tra sau dọn mã ngày 11/11/2026: vẫn 50 nhân viên, 202 tài khoản, 70 thiết bị; hash snapshot trước/sau không đổi. Đây là số liệu lab hiện tại, không phải hằng số giao diện.

## Luồng dùng chung

1. Màn hình Doanh nghiệp đọc và ghi sự kiện hồ sơ lab qua API theo đợt.
2. `agent_core/business_events.py` xử lý thay đổi hồ sơ; không nhận bình luận điều khiển nhân vật hay thao tác máy thật.
3. Collector A.6 dùng `agent_core/people_assessment.py`, audit trail nêu rõ luật đại diện, không nhận là LLM phân loại.
4. Bằng chứng giữ assessment/control, entity_refs, snapshot_hash và SHA256. Hồ sơ ISO nhận diện dữ liệu cũ và giữ lịch sử đánh giá.
5. Chế độ chỉ đánh giá tài liệu không bị preset hoặc snapshot mô phỏng thay thế kết luận.

## API

- GET `/api/assessments/{id}/enterprise/company`
- POST `/api/assessments/{id}/enterprise/company/events`
- GET `/api/assessments/{id}/enterprise/scope56`
- GET `/api/assessments/{id}/enterprise/shared-work`

Các API yêu cầu đăng nhập và quyền thành viên. Chỉ admin xác nhận ngoại lệ giữ tài khoản. API `/api/live`, `/api/simulation`, `/api/agent/*` và API sự cố/nhiệm vụ cũ đã gỡ.

Dữ liệu database lịch sử được giữ nguyên; không drop bảng hoặc sửa hồ sơ sự cố cũ. Không còn worker tạo thêm sự kiện/mission demo. Xem [hướng dẫn 56](THU_HO_SO_VA_THAM_DINH_56.md) và [ma trận năng lực](MA_TRAN_56_CONTROL.md).
