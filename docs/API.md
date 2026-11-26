# API Phase 03

Mở `/docs` trên máy cục bộ để xem schema và dùng giao diện OpenAPI.

| Phương thức | Đường dẫn | Quyền |
| --- | --- | --- |
| GET | `/health` | Kiểm tra tiến trình |
| GET | `/ready` | Kiểm tra PostgreSQL, pgvector và quyền backend |
| POST | `/api/v1/auth/token` | Xác thực tên đăng nhập và mật khẩu |
| GET | `/api/v1/companies` | Doanh nghiệp có membership còn hiệu lực |
| GET | `/api/v1/companies/{company_id}/employees` | Admin, auditor và hồ sơ của chính employee |
| GET | `/api/v1/companies/{company_id}/employees/{employee_id}` | Cùng quy tắc như danh sách |
| PATCH | `/api/v1/companies/{company_id}/employees/{employee_id}` | Admin cùng tenant |

Đăng nhập bằng JSON gồm `username` và `password`. Gửi `access_token` dưới dạng Bearer ở yêu cầu tiếp theo. Danh sách nhân viên hỗ trợ `limit` từ 1–100 và `offset` từ 0. Đổi tên hiển thị cần `display_name` và `expected_revision`. Sửa với phiên bản cũ trả 409. ID tenant hoặc hồ sơ ngoài phạm vi trả 404, và phiên đăng nhập hết hạn trả 401.

Dùng localhost. Kiểm thử tình huống tenant được thực hiện với tài khoản và hồ sơ tổng hợp trên cơ sở dữ liệu test riêng.

## Luồng mô phỏng

Các đường dẫn dưới đây tiếp sau `/api/v1/companies/{company_id}`.

| Phương thức | Đường dẫn | Vai trò |
| --- | --- | --- |
| POST | `/assessments` | Auditor, admin. Dùng Idempotency-Key. |
| POST | `/assessment-jobs` | Auditor, admin. Lưu yêu cầu với Idempotency-Key. Thêm `?start=true` để bắt đầu đánh giá nền sau khi lưu. |
| GET | `/assessment-jobs/{job_id}` | Người tạo yêu cầu trong đúng doanh nghiệp. Trả `PENDING` hoặc `COMPLETED`. |
| POST | `/assessment-jobs/{job_id}/resume` | Người tạo yêu cầu chạy tiếp hoặc đọc kết quả đã gắn. Nếu chính sách đã đổi, tạo yêu cầu mới. |
| GET | `/assessments/{run_id}` | Auditor, admin |
| POST | `/assessments/{run_id}/findings/{finding_id}/plan` | Auditor, admin |
| GET | `/actions/{action_id}` | Auditor, admin |
| POST | `/actions/{action_id}/decision` | Admin khác người lập kế hoạch |
| POST | `/actions/{action_id}/dry-run` | Auditor hoặc admin gửi `plan_hash` để kiểm tra điều kiện hiện tại. Kết quả gồm trạng thái, lý do, đích và revision. |
| POST | `/actions/{action_id}/execute` | Admin. Dùng Idempotency-Key và plan_hash. |
| POST | `/actions/{action_id}/verify` | Admin. Đọc lại nguồn ở giao dịch mới. |
| POST | `/actions/{action_id}/rollback` | Admin đã duyệt hành động medium, gửi plan_hash. Cần snapshot và revision nguồn chưa đổi. |
| GET | `/me/training` | Nhân viên có hồ sơ đào tạo của chính mình |
| POST | `/me/nda/acknowledge` | Nhân viên xác nhận cam kết trong hồ sơ của chính mình. Gửi request_id, document_hash, expected_revision và acknowledged=true từ yêu cầu đang hiển thị. Trả về biên nhận cùng mã bằng chứng. |
| POST | `/me/training/complete` và `/me/interview` | Nhân viên |
| GET | `/assessments/{run_id}/reports/gap` và `/assessments/{run_id}/reports/remediation` | Auditor, admin |
| GET | `/reports/audit` và `/reports/soa` | Auditor, admin |
| GET | `/knowledge/{control_id}?query=...` | Auditor, admin |
| GET | `/knowledge/{control_id}/chunks/{chunk_id}?expected_sha256=...` | Auditor, admin. Mở đúng đoạn trích đã lưu trong báo cáo. Trả 404 nếu không thuộc phạm vi và 409 nếu nội dung đã đổi. |

Đánh giá mới lưu `citations_by_control` với tối đa ba đoạn tham chiếu mỗi mã. Danh sách rỗng cho biết mã đó chỉ có rubric nghiên cứu. Các đoạn tham chiếu bổ sung ngữ cảnh cho báo cáo. Kết luận vẫn lấy từ quy tắc và quan sát nghiệp vụ.

Dùng `GET /assessments/{run_id}/reports/gap.csv` để tải CSV khoảng cách và `GET /assessments/{run_id}/compare?before={older_run_id}` để so sánh hai lần đánh giá cùng phạm vi và phiên bản chính sách.

`POST /me/interview` nhận `kind`, `answer` và `use_local_model` (mặc định false). Khi chọn model, backend cần `LOCAL_INTERVIEW_MODEL`; mất kết nối, sai schema, bằng chứng trích dẫn không nằm trong câu trả lời hoặc model yêu cầu thẩm định đều trả kết quả `HUMAN_REVIEW`. `GET /me/training` công bố `local_model_available`. Cấu hình có tên model không đảm bảo dịch vụ Ollama đang sẵn sàng.

Rollback chỉ hỗ trợ endpoint mô phỏng có snapshot được lưu khi thực thi. Thành công trả `ROLLED_BACK`, có revision và bằng chứng đối chiếu snapshot. Gửi lại cùng yêu cầu không ghi thêm thay đổi. Khác người duyệt, khác hash, nguồn đã có sửa đổi tiếp theo hoặc chính sách đã đổi đều bị từ chối. Đánh giá cũ giữ nguyên; phải tạo đánh giá mới để phản ánh cấu hình đã phục hồi.
