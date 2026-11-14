# BẢNG ĐO ĐỘ ĐÚNG AI AGENT THEO TỪNG CONTROL A.8 SO VỚI NGƯỜI ĐÁNH GIÁ

## 1. Tổng quan thực nghiệm
- **Phạm vi đánh giá:** **18 control kỹ thuật nhóm A.8** (ISO/IEC 27001:2022).
- **Doanh nghiệp giả lập:** **6 kịch bản hồ sơ có chủ đích** (`conforming`, `mixed`, `nonconforming`, `incomplete`, `stale`, `conflicting`) × 18 control = **108 hồ sơ bằng chứng gốc**.
- **Người đánh giá độc lập (Ground Truth):** Lê Đăng Khoa & Lê Đoàn Văn Tú (108/108 hồ sơ có nhãn chuẩn).
- **Kết quả Rule-based Agent:** Khớp **108/108** ca (**100.0%**), hệ số đồng thuận `Cohen's Kappa = 1.0`.
- **Kết quả LLM Agent (`qwen2.5:7b`):** Khớp **206/216** lượt (**95.37%**), hệ số đồng thuận `Cohen's Kappa = 0.9318`.

## 2. Kịch bản hồ sơ đúng/sai có chủ đích trong Doanh nghiệp giả lập

| Mã hồ sơ (Profile) | Số control | Mô tả trạng thái thiết kế có chủ đích | Đáp án chuẩn kỳ vọng |
|---|---:|---|---|
| `conforming` | 18 | Cấu hình và nhật ký hệ thống đáp ứng đầy đủ cả 2 tiêu chí kỹ thuật | `Compliant` (18/18) |
| `mixed` | 18 | Đạt tiêu chí thứ nhất nhưng vi phạm tiêu chí thứ hai có chủ đích | `Partially Compliant` (18/18) |
| `nonconforming` | 18 | Cấu hình sai lệch hoàn toàn ở cả 2 tiêu chí kiểm soát | `Non-Compliant` (18/18) |
| `incomplete` | 18 | Thiếu tệp cấu hình/log bắt buộc, không đủ dữ kiện kết luận | `Insufficient Evidence` (18/18) |
| `stale` | 18 | Hồ sơ rà soát/cập nhật chữ ký đã quá hạn hiệu lực chính sách | `Partially Compliant` / `Non-Compliant` |
| `conflicting` | 18 | Chính sách khai báo đạt nhưng log vận hành thực tế ghi nhận vi phạm | `Partially Compliant` / `Non-Compliant` |

## 3. Bảng độ đúng theo từng Control A.8 (18 Control)

| Mã Control | Tên biện pháp kiểm soát (ISO 27001:2022) | Tiêu chí kỹ thuật tự động thu thập | Rule Agent (Đúng/Tổng) | Độ đúng Rule (%) | LLM Agent (Đúng/Tổng) | Độ đúng LLM (%) | Precision LLM (%) | Recall LLM (%) | F1-Score LLM (%) | Thời gian LLM (ms) |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **A.8.1** | User endpoint devices | `edr_active`, `disk_encrypted` | 6/6 | **100.00%** | 10/12 | **83.33%** | 100.00% | 75.00% | 75.00% | 8390 |
| **A.8.2** | Privileged access rights | `privileged_approved`, `privileged_review_current` | 6/6 | **100.00%** | 12/12 | **100.00%** | 100.00% | 100.00% | 100.00% | 7142 |
| **A.8.3** | Information access restriction | `access_default_deny`, `access_review_current` | 6/6 | **100.00%** | 10/12 | **83.33%** | 100.00% | 75.00% | 75.00% | 9023 |
| **A.8.5** | Secure authentication | `mfa_enforced`, `legacy_auth_disabled` | 6/6 | **100.00%** | 10/12 | **83.33%** | 87.50% | 91.67% | 86.67% | 7959 |
| **A.8.7** | Protection against malware | `antimalware_active`, `signatures_current` | 6/6 | **100.00%** | 12/12 | **100.00%** | 100.00% | 100.00% | 100.00% | 8032 |
| **A.8.8** | Management of technical vulnerabilities | `scan_current`, `critical_findings_remediated` | 6/6 | **100.00%** | 12/12 | **100.00%** | 100.00% | 100.00% | 100.00% | 7899 |
| **A.8.9** | Configuration management | `baseline_approved`, `drift_resolved` | 6/6 | **100.00%** | 12/12 | **100.00%** | 100.00% | 100.00% | 100.00% | 7495 |
| **A.8.10** | Information deletion | `deletion_policy_enforced`, `deletion_verified` | 6/6 | **100.00%** | 12/12 | **100.00%** | 100.00% | 100.00% | 100.00% | 7660 |
| **A.8.12** | Data leakage prevention | `dlp_enforced`, `dlp_test_passed` | 6/6 | **100.00%** | 12/12 | **100.00%** | 100.00% | 100.00% | 100.00% | 7650 |
| **A.8.13** | Information backup | `backup_success`, `restore_test_passed` | 6/6 | **100.00%** | 10/12 | **83.33%** | 87.50% | 91.67% | 86.67% | 7883 |
| **A.8.15** | Logging | `audit_logs_enabled`, `logs_integrity_protected` | 6/6 | **100.00%** | 12/12 | **100.00%** | 100.00% | 100.00% | 100.00% | 7970 |
| **A.8.16** | Monitoring activities | `alerts_enabled`, `alert_response_test_passed` | 6/6 | **100.00%** | 12/12 | **100.00%** | 100.00% | 100.00% | 100.00% | 7552 |
| **A.8.17** | Clock synchronization | `trusted_time_configured`, `clock_offset_within_policy` | 6/6 | **100.00%** | 12/12 | **100.00%** | 100.00% | 100.00% | 100.00% | 7778 |
| **A.8.19** | Installation of software on operational systems | `installation_restricted`, `installed_software_approved` | 6/6 | **100.00%** | 12/12 | **100.00%** | 100.00% | 100.00% | 100.00% | 7994 |
| **A.8.20** | Networks security | `firewall_default_deny`, `firewall_rules_reviewed` | 6/6 | **100.00%** | 10/12 | **83.33%** | 87.50% | 91.67% | 86.67% | 7849 |
| **A.8.22** | Segregation of networks | `zones_separated`, `segmentation_test_passed` | 6/6 | **100.00%** | 12/12 | **100.00%** | 100.00% | 100.00% | 100.00% | 7521 |
| **A.8.24** | Use of cryptography | `approved_crypto_configured`, `key_rotation_current` | 6/6 | **100.00%** | 12/12 | **100.00%** | 100.00% | 100.00% | 100.00% | 7777 |
| **A.8.32** | Change management | `change_approved`, `rollback_test_recorded` | 6/6 | **100.00%** | 12/12 | **100.00%** | 100.00% | 100.00% | 100.00% | 7245 |
| **TỔNG HỢP** | **18 Control kỹ thuật A.8** | **36 thuộc tính kỹ thuật** | **108/108** | **100.00%** | **206/216** | **95.37%** | **97.45%** | **95.37%** | **96.28%** | **—** |

## 4. Độ đúng theo từng phân lớp kết luận (LLM Agent vs Người đánh giá)

| Nhãn kết luận tuân thủ | Số mẫu chuẩn (Support) | Precision (%) | Recall (%) | F1-Score (%) |
|---|---:|---:|---:|---:|
| `Compliant` | 36 | 100.00% | 100.00% | 100.00% |
| `Partially Compliant` | 36 | 84.21% | 88.89% | 86.49% |
| `Non-Compliant` | 36 | 100.00% | 100.00% | 100.00% |
| `Insufficient Evidence` | 108 | 100.00% | 94.44% | 97.14% |
