"""Four canonical ISO/IEC 27001:2022 People-Centric scenarios with Ground Truth."""
from __future__ import annotations

from typing import Any
from backend.pc_storage import BasePCStore, DEFAULT_BASELINE_POLICY


def seed_canonical_company(store: BasePCStore, company_id: str = "COMP-CANONICAL-01") -> dict[str, Any]:
    """Seed one complete canonical enterprise embedding ALL 4 required business scenarios:

    - Scenario 1 (A.8.8): 10 PCs (PC-01..PC-10); 7/10 patched, 3/10 (PC-03, PC-06, PC-09) missing patches.
    - Scenario 2 (A.8.9): PC-02 fails 4/6 baseline checks (Firewall OFF, Screen Lock 30m, BitLocker OFF,
      Password Policy FAIL; Antivirus ON & NTP Synced PASS).
    - Scenario 3 (People - 50 employees NV001..NV050):
        * A.6.3 Training: 35/50 compliant (15 missing)
        * A.6.6 NDA: 45/50 compliant (5 missing)
        * A.8.5 MFA: 38/50 compliant (12 missing)
        * A.6.8 Incident process: 30/50 compliant (20 need Adaptive Interview)
        * A.6.3 Phishing simulation: 32/50 passed (18 failed)
    - Scenario 4 (Cross-Domain NV015 - Phòng Kế toán):
        * NV015 is terminated in HR, yet AD, VPN, Email, Accounting App are still active (A.5.18, A.6.5),
          and Laptop LT-NV015 is not returned + badge card active (A.5.11).
    """
    company = store.upsert_company(
        {
            "company_id": company_id,
            "name": "Công ty Cổ phần Công nghệ & Tài chính Minh Việt (Canonical Lab)",
            "industry": "FinTech / Enterprise Services",
            "size_tier": "medium",
            "employee_count": 50,
            "execution_mode": "hybrid_lab",
            "baseline_policy": dict(DEFAULT_BASELINE_POLICY),
            "soa_exclusions": [],
            "lab_config": {
                "ad_server_host": "192.168.56.10",
                "workstation_hosts": {"PC-02": "192.168.56.22", "PC-03": "192.168.56.23"},
            },
        }
    )

    departments = ["Kỹ thuật", "Phòng Kế toán", "Nhân sự", "Kinh doanh", "Vận hành"]

    # 50 employees: NV001..NV050
    for idx in range(1, 51):
        eid = f"NV{idx:03d}"
        is_nv015 = eid == "NV015"
        dept = "Phòng Kế toán" if is_nv015 else departments[(idx - 1) % len(departments)]
        store.upsert_employee(
            company_id,
            {
                "employee_id": eid,
                "full_name": "Nguyễn Thị Lan Anh" if is_nv015 else f"Nhân sự {eid}",
                "department": dept,
                "role_title": "Kế toán tổng hợp" if is_nv015 else "Chuyên viên",
                "employment_status": "terminated" if is_nv015 else "active",
                "terminated_at": "2026-11-20T09:00:00+00:00" if is_nv015 else None,
                "screened": True,
                "contract_signed": True,
                # Exact Scenario 3 counts across 50 employees:
                # 35/50 training, 45/50 NDA, 30/50 incident process, 32/50 phishing
                "training_completed": idx <= 35,
                "training_score": 88.0 if idx <= 35 else 45.0,
                "nda_signed": idx <= 45,
                "incident_process_known": idx <= 30,
                "phishing_passed": idx <= 32,
                "remote_work_compliant": True,
                "offboarding_ack": False if is_nv015 else True,
            },
        )

        # Primary AD account for all 50 employees (38/50 MFA enabled)
        store.upsert_account(
            company_id,
            {
                "account_id": f"AD-{eid}",
                "employee_id": eid,
                "system_type": "active_directory",
                "is_active": True,  # Intentionally still active for NV015 (Scenario 4 fault)
                "mfa_enabled": idx <= 38,
                "is_privileged": idx in (1, 2),
            },
        )

    # Extra active accounts for NV015 (VPN, Email, Accounting App) - Scenario 4
    for sys_type, prefix in (("vpn", "VPN"), ("email", "MAIL"), ("accounting_app", "ACC")):
        store.upsert_account(
            company_id,
            {
                "account_id": f"{prefix}-NV015",
                "employee_id": "NV015",
                "system_type": sys_type,
                "is_active": True,
                "mfa_enabled": True,
                "is_privileged": sys_type == "accounting_app",
            },
        )

    # Scenario 1 & 2 Devices: PC-01..PC-10
    missing_patch_pcs = {
        "PC-03": ["KB5044285", "KB5043076"],
        "PC-06": ["KB5044285"],
        "PC-09": ["KB5044285", "CVE-2026-1102-FIX"],
    }
    for num in range(1, 11):
        did = f"PC-{num:02d}"
        is_pc02 = did == "PC-02"
        patches = missing_patch_pcs.get(did, [])
        store.upsert_device(
            company_id,
            {
                "device_id": did,
                "hostname": f"{did.lower()}.minhviet.local",
                "os_type": "windows11",
                "assigned_employee_id": f"NV{num:03d}",
                "badge_card_active": True,
                "returned_to_it": False,
                # Scenario 2: PC-02 fails 4/6 baseline criteria; Antivirus & NTP pass
                "firewall_enabled": False if is_pc02 else True,
                "screen_lock_minutes": 30 if is_pc02 else 5,
                "disk_encrypted": False if is_pc02 else True,
                "password_policy_ok": False if is_pc02 else True,
                "antivirus_active": True,
                "ntp_synced": True,
                # Scenario 1: PC-03, PC-06, PC-09 missing security patches
                "patch_compliant": len(patches) == 0,
                "missing_patches": patches,
                "usb_unauthorized_events": 0,
                "disposal_verified": None,
                "installed_software": ["Microsoft Office", "Google Chrome", "CrowdStrike Falcon"],
                "audit_logging_enabled": True,
            },
        )

    # Scenario 4 Hardware Asset for NV015: Laptop not returned + Badge active
    store.upsert_device(
        company_id,
        {
            "device_id": "LT-NV015",
            "hostname": "lt-nv015.minhviet.local",
            "os_type": "windows11",
            "assigned_employee_id": "NV015",
            "badge_card_active": True,
            "returned_to_it": False,
            "firewall_enabled": True,
            "screen_lock_minutes": 5,
            "disk_encrypted": True,
            "password_policy_ok": True,
            "antivirus_active": True,
            "ntp_synced": True,
            "patch_compliant": True,
            "missing_patches": [],
            "usb_unauthorized_events": 0,
            "disposal_verified": False,
            "installed_software": ["Microsoft Office", "MISA Accounting"],
            "audit_logging_enabled": True,
        },
    )

    # Isolated Ground Truth for all 4 scenarios
    store.save_ground_truth(
        company_id,
        "A.8.8",
        "Partial",
        [{"device_id": d, "missing_patches": p} for d, p in missing_patch_pcs.items()],
        ["deploy_security_patches"],
    )
    store.save_ground_truth(
        company_id,
        "A.8.9",
        "Partial",
        [
            {
                "device_id": "PC-02",
                "failed_checks": ["firewall_enabled", "screen_lock_minutes", "disk_encrypted", "password_policy_ok"],
                "passed_checks": ["antivirus_active", "ntp_synced"],
            }
        ],
        ["sync_device_baseline_gpo"],
    )
    store.save_ground_truth(
        company_id,
        "A.6.3",
        "Partial",
        [{"missing_training_count": 15, "failed_phishing_count": 18}],
        ["assign_security_training"],
    )
    store.save_ground_truth(
        company_id,
        "A.6.6",
        "Partial",
        [{"unsigned_nda_count": 5}],
        ["send_nda_reminder"],
    )
    store.save_ground_truth(
        company_id,
        "A.8.5",
        "Partial",
        [{"mfa_disabled_count": 12}],
        ["create_it_remediation_ticket"],
    )
    store.save_ground_truth(
        company_id,
        "A.6.8",
        "Partial",
        [{"unknown_incident_process_count": 20}],
        ["assign_security_training"],
    )
    store.save_ground_truth(
        company_id,
        "A.6.5",
        "Non-compliant",
        [{"employee_id": "NV015", "department": "Phòng Kế toán", "active_systems": ["active_directory", "vpn", "email", "accounting_app"]}],
        ["disable_ad_and_revoke_access", "create_it_remediation_ticket"],
    )
    store.save_ground_truth(
        company_id,
        "A.5.18",
        "Non-compliant",
        [{"employee_id": "NV015", "active_systems": ["active_directory", "vpn", "email", "accounting_app"]}],
        ["disable_ad_and_revoke_access"],
    )
    store.save_ground_truth(
        company_id,
        "A.5.11",
        "Non-compliant",
        [{"employee_id": "NV015", "device_id": "LT-NV015", "returned_to_it": False, "badge_card_active": True}],
        ["create_it_remediation_ticket"],
    )
    return company
