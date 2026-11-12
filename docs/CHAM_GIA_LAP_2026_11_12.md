# Chấm giả lập A.8 — 12/11/2026

Chấm giả lập từ facts đã parse và rubric lab dùng chung với guard. Không phải người thật, chấm mù, đọc nguồn độc lập hay accuracy chuyên gia. Không ghi vào nhãn người chấm hoặc phê duyệt SoA.

Lượt nguồn: `67d38694-724e-4cc1-83f8-9df07f5cc3b2`
Report SHA256: `c39d7e9bb0f6030089cc414e4a9a1a1f33f4eab8a68d499f481b5dd3370ed540`

| Control | Giả lập | Agent | Căn cứ từ facts |
|---|---|---|---|
| A.8.1 | Partially Compliant | Partially Compliant | endpoint_record_private=True (met); endpoint_file_encryption_verified=False (not_met) |
| A.8.2 | Partially Compliant | Partially Compliant | privileged_operation_restricted=True (met); privileged_review_current=False (not_met) |
| A.8.3 | Partially Compliant | Partially Compliant | access_default_deny=True (met); access_review_current=False (not_met) |
| A.8.5 | Partially Compliant | Partially Compliant | password_rejection_verified=True (met); second_factor_enforced=False (not_met) |
| A.8.7 | Partially Compliant | Partially Compliant | test_signature_quarantined=True (met); signature_database_fresh=False (not_met) |
| A.8.8 | Partially Compliant | Partially Compliant | inventory_scan_enabled=True (met); no_critical_lab_advisory_match=False (not_met) |
| A.8.9 | Partially Compliant | Partially Compliant | baseline_authorization_present=True (met); configuration_matches_baseline=False (not_met) |
| A.8.10 | Partially Compliant | Partially Compliant | deletion_policy_enforced=True (met); deletion_verified=False (not_met) |
| A.8.12 | Partially Compliant | Partially Compliant | sensitive_transfer_blocked=True (met); blocked_transfer_audited=False (not_met) |
| A.8.13 | Partially Compliant | Partially Compliant | backup_success=True (met); restore_test_passed=False (not_met) |
| A.8.15 | Partially Compliant | Partially Compliant | audit_logs_enabled=True (met); logs_integrity_protected=False (not_met) |
| A.8.16 | Partially Compliant | Partially Compliant | file_change_detected_within_sla=True (met); alert_delivery_receipt_present=False (not_met) |
| A.8.17 | Partially Compliant | Partially Compliant | time_reference_signature_valid=True (met); application_time_offset_within_policy=False (not_met) |
| A.8.19 | Partially Compliant | Partially Compliant | installation_restricted=True (met); installed_software_approved=False (not_met) |
| A.8.20 | Partially Compliant | Partially Compliant | unapproved_source_denied=True (met); approved_network_flow_available=False (not_met) |
| A.8.22 | Partially Compliant | Partially Compliant | cross_zone_service_denied=True (met); business_zone_service_available=False (not_met) |
| A.8.24 | Partially Compliant | Partially Compliant | strong_tls_handshake_verified=True (met); private_key_access_restricted=False (not_met) |
| A.8.32 | Partially Compliant | Partially Compliant | change_bound_to_current_release=True (met); rollback_restores_release=False (not_met) |

18/18 kết luận giả lập là một phần theo rubric đại diện. Khớp kết luận cuối Agent 18/18 trong lượt này. Cùng nguồn facts/rubric với guard nên không suy ra accuracy với con người hoặc đánh giá độc lập. Lỗi lần đầu A.8.3 vẫn giữ trong báo cáo nguồn.

Không sửa kho nhãn người thật, quyết định áp dụng, thẩm định 56 hoặc phê duyệt. Với 37 control thiếu nguồn, kết luận chính thức vẫn giữ chờ bằng chứng.

Thao tác: đăng nhập admin → Thực nghiệm 18 A.8 → chọn lượt 67d38694 → Chấm giả lập lượt này. Có bảng và xuất JSON riêng.
