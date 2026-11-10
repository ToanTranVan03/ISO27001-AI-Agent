# Ma trận tiêu chí raw A.8 — phiên bản v2

Trạng thái: chờ người phụ trách rà soát/phê duyệt. Đây là các kiểm tra đại diện trong phạm vi lab, không phải toàn bộ yêu cầu kiểm soát ISO.

| Control | Tiêu chí | Nguồn gốc | Điều kiện đạt | Loại kiểm chứng |
|---|---|---|---|---|
| A.8.1 | edr_active | edr.status | Dịch vụ EDR báo active (running) | raw configuration/log fixture interpretation |
| A.8.1 | disk_encrypted | lsblk.json | Thiết bị mount / có type crypt | raw configuration/log fixture interpretation |
| A.8.2 | privileged_approved | sudoers | Chỉ labadmin có mẫu cấp sudo đã phê duyệt | raw configuration/log fixture interpretation |
| A.8.2 | privileged_review_current | access-review.csv | Tất cả quyết định approved, ngày review trong 90 ngày | raw configuration/log fixture interpretation |
| A.8.3 | access_default_deny | acl.csv | Không có everyone; quyền trong phạm vi kiểm tra là read | raw configuration/log fixture interpretation |
| A.8.3 | access_review_current | access-review.csv | Review approved trong 90 ngày | raw configuration/log fixture interpretation |
| A.8.5 | mfa_enforced | sshd_config | SSH yêu cầu publickey cùng keyboard-interactive | raw configuration/log fixture interpretation |
| A.8.5 | legacy_auth_disabled | legacy-auth.conf | PasswordAuthentication no | raw configuration/log fixture interpretation |
| A.8.7 | antimalware_active | clamd.status | clamd active (running) | raw configuration/log fixture interpretation |
| A.8.7 | signatures_current | freshclam.log | Chữ ký cập nhật không quá 2 ngày | raw configuration/log fixture interpretation |
| A.8.8 | scan_current | scanner.log | Scan không quá 7 ngày | raw configuration/log fixture interpretation |
| A.8.8 | critical_findings_remediated | vulnerabilities.csv | Không còn finding critical trạng thái khác fixed | raw configuration/log fixture interpretation |
| A.8.9 | baseline_approved | baseline.conf | Baseline có mã CAB phê duyệt | raw configuration/log fixture interpretation |
| A.8.9 | drift_resolved | drift.diff | Không có nội dung drift chưa xử lý | raw configuration/log fixture interpretation |
| A.8.10 | deletion_policy_enforced | retention.conf | Retention trong khoảng 1–30 ngày theo chính sách lab | executed-container-file-probe + raw configuration |
| A.8.10 | deletion_verified | deletion.log | Log kiểm chứng đối tượng đã absent | executed-container-file-probe + raw configuration |
| A.8.12 | dlp_enforced | dlp.conf | DLP mode block | raw configuration/log fixture interpretation |
| A.8.12 | dlp_test_passed | dlp.log | Probe PII bị blocked | raw configuration/log fixture interpretation |
| A.8.13 | backup_success | backup.dat + backup.sha256 | SHA256 backup khớp manifest | executed-container-file-probe + raw configuration |
| A.8.13 | restore_test_passed | backup.dat + restored.dat | Nội dung restore khớp backup | executed-container-file-probe + raw configuration |
| A.8.15 | audit_logs_enabled | auditd.conf | auditd write_logs yes | raw configuration/log fixture interpretation |
| A.8.15 | logs_integrity_protected | audit.log + audit.sha256 | SHA256 audit log khớp manifest | raw configuration/log fixture interpretation |
| A.8.16 | alerts_enabled | alerts.conf | Ngưỡng cảnh báo failed login trong 1–5 | raw configuration/log fixture interpretation |
| A.8.16 | alert_response_test_passed | alert-delivery.log | Log có bằng chứng delivery received | raw configuration/log fixture interpretation |
| A.8.17 | trusted_time_configured | chrony.conf | Chrony dùng time.lab.internal trong allowlist | raw configuration/log fixture interpretation |
| A.8.17 | clock_offset_within_policy | tracking.txt | Trị tuyệt đối clock offset không quá 0,1 giây | raw configuration/log fixture interpretation |
| A.8.19 | installation_restricted | installer-permissions.csv | User thường không có quyền cài; inventory phải có user | executed-container-file-probe + raw configuration |
| A.8.19 | installed_software_approved | packages.tsv | Mỗi gói có approval CAB | executed-container-file-probe + raw configuration |
| A.8.20 | firewall_default_deny | nftables.conf | Policy input drop, không có policy accept trong bản lab | raw configuration/log fixture interpretation |
| A.8.20 | firewall_rules_reviewed | firewall-review.csv | Các rule có review approved | raw configuration/log fixture interpretation |
| A.8.22 | zones_separated | zones.csv | Ít nhất hai subnet và không overlap | raw configuration/log fixture interpretation |
| A.8.22 | segmentation_test_passed | connectivity.log | Probe dev → prod:5432 có kết quả DENY | raw configuration/log fixture interpretation |
| A.8.24 | approved_crypto_configured | nginx.conf | Chỉ TLSv1.2 và TLSv1.3 trong cấu hình lab | raw configuration/log fixture interpretation |
| A.8.24 | key_rotation_current | key-rotation.csv | Rotation khóa trong 90 ngày | raw configuration/log fixture interpretation |
| A.8.32 | change_approved | changes.csv | Các change có mã CAB phê duyệt | raw configuration/log fixture interpretation |
| A.8.32 | rollback_test_recorded | rollback.log | Rollback có log restore verified | raw configuration/log fixture interpretation |

Có dữ liệu hợp lệ nhưng vi phạm điều kiện → fail. Thiếu/sai định dạng/hết hạn/capture mâu thuẫn → unknown. Kết luận rubric: có unknown → Insufficient Evidence; tất cả pass → Compliant; hỗn hợp pass/fail → Partially Compliant; tất cả fail → Non-Compliant.

Hai trạng thái Compliant/Non-Compliant ở đây chỉ có nghĩa theo phạm vi và rubric đại diện của lab. Tính áp dụng, phê duyệt chính sách và các phần yêu cầu khác vẫn cần người đánh giá xác nhận.
