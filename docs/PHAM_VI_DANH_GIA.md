# Phạm vi kiểm soát và bằng chứng

Đây là phạm vi kỹ thuật, chưa phải SoA được phê duyệt. Không suy từ chưa hỗ trợ thành không áp dụng. Các màn hình web hiện hành dùng chung snapshot PostgreSQL theo đợt; benchmark/CLI dùng fixture cô lập. Không cộng số kiểm soát của các engine thành tỷ lệ bao phủ toàn ISO.

## Enterprise Lab — hồ sơ lưu trong đợt đánh giá

| Kiểm soát | Nguồn | Tiêu chí healthy của lab |
|---|---|---|
| A.6.1 | Nhân sự & tuyển dụng | employees_total=12, screening_records=12, screening_policy_approved=True, hr_confirmation_available=True |
| A.7.1 | Phòng máy & an ninh vật lý | zones_defined=3, zones_access_restricted=3, perimeter_policy_exists=True, site_inspection_attested=True |
| A.8.5 | IAM / Xác thực | active_accounts=18, mfa_enabled_accounts=18, privileged_accounts=3, privileged_mfa_accounts=3, password_min_length=14 |
| A.8.20 | Gateway / Mạng | network_policy_defined=True, rules_approved=12, rules_total=12, change_log_available=True |
| A.8.13 | SecOps / Sao lưu | scheduled_backups=True, recent_jobs=8, successful_jobs=8, integrity_checks_passed=8, restore_test_passed=True |

Bằng chứng collector JSON: facts, revision, source, ngày tạo, SHA-256. Ngưỡng trên là chính sách mô phỏng, không phải ngưỡng bắt buộc của ISO.

## Bộ mô phỏng con người

| Kiểm soát | Tiêu chí dự án | Chủ trì |
|---|---|---|
| A.6.1 Thẩm tra trước tuyển dụng | screened | HR |
| A.6.2 Điều khoản lao động | terms_signed | HR |
| A.6.3 Nhận thức và đào tạo | training_complete, training_passed | HR / Quản lý |
| A.6.4 Quy trình xử lý vi phạm | disciplinary_informed | HR |
| A.6.5 Trách nhiệm khi nghỉ hoặc đổi việc | post_employment_ack | HR / IT |
| A.6.6 Thỏa thuận bảo mật | nda_signed | HR / Pháp chế |
| A.6.7 Làm việc từ xa | remote_policy_ack | IT / Quản lý |
| A.6.8 Báo cáo sự kiện an toàn thông tin | reporting_trained, event_reported | SecOps / Quản lý |

Nguồn giả lập: hồ sơ nhân sự, tài khoản và thiết bị liên quan.

## Văn phòng tương tác

| Kiểm soát | Dấu hiệu | Bằng chứng |
|---|---|---|
| A.7.7 | Rời máy chưa khóa | sự kiện, nhân viên, máy |
| A.7.10 | USB lạ | sự kiện phương tiện lưu trữ |
| A.8.19 | Cài ứng dụng lạ | sự kiện cài phần mềm |

Các dấu hiệu này chỉ bao phủ một phần kiểm soát. Khắc phục sự cố không đồng nghĩa toàn bộ kiểm soát đáp ứng.

## Kết luận

Đáp ứng / không đáp ứng / chưa đủ bằng chứng theo rubric của từng engine. Không áp dụng phải có lý do và người duyệt. Còn thiếu: nguồn tiêu chuẩn có phiên bản/định vị, thẩm định chuyên gia, dữ liệu doanh nghiệp thật và đánh giá toàn bộ ISMS.

## Cập nhật nguồn doanh nghiệp dùng chung

Collector A.6.1–A.6.8 đọc snapshot chung và đánh giá bằng luật minh bạch; audit trail phân biệt với LLM. Các collector lab A.7.1, A.8.5, A.8.13, A.8.20 liên kết cùng snapshot/định danh; IAM lấy số liệu tài khoản hiện hành. Tổng 12 kiểm soát có collector trong phạm vi này, chưa phải đánh giá đầy đủ mọi yêu cầu của mỗi kiểm soát. Chi tiết tại DOANH_NGHIEP_DUNG_CHUNG.md.
