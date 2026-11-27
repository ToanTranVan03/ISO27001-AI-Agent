"""Multi-tenant Enterprise Generator (Python + Faker) with controlled Fault Injection & Ground Truth."""
from __future__ import annotations

import random
from typing import Any

from faker import Faker

from backend.pc_storage import BasePCStore, DEFAULT_BASELINE_POLICY
from simulation.scenarios import seed_canonical_company

INDUSTRIES = (
    "FinTech",
    "E-Commerce",
    "Healthcare SaaS",
    "Logistics & Supply Chain",
    "Manufacturing",
    "Banking & Insurance",
    "EdTech",
)

DEPARTMENTS = ("Kỹ thuật", "Phòng Kế toán", "Nhân sự", "Kinh doanh", "Vận hành", "Pháp chế")

SIZE_CONFIG = {
    "small": (15, 25, 6),
    "medium": (35, 55, 10),
    "enterprise": (60, 85, 14),
}


def generate_multi_enterprise_dataset(
    store: BasePCStore,
    count: int = 25,
    seed: int = 2026,
    include_canonical: bool = True,
) -> list[dict[str, Any]]:
    """Generate 20-30+ multi-size synthetic companies with controlled Fault Injection & Ground Truth.

    Every company receives a deterministic mix of compliance profiles:
    - Clean compliant controls
    - Partial faults (missing patches, baseline drift, partial NDA/training/MFA)
    - Non-compliant cross-domain terminated-employee faults
    - Insufficient Evidence (missing/null records so Agent must NOT guess)
    - Not Applicable (SoA exclusions on specific controls)
    """
    if count < 1:
        raise ValueError("count must be >= 1")

    rng = random.Random(seed)
    fake = Faker(["vi_VN", "en_US"])
    Faker.seed(seed)

    created: list[dict[str, Any]] = []
    if include_canonical:
        created.append(seed_canonical_company(store, company_id="COMP-CANONICAL-01"))

    remaining = count - len(created)
    tiers = ("small", "medium", "enterprise")

    for i in range(1, remaining + 1):
        tier = tiers[(i - 1) % len(tiers)]
        min_emp, max_emp, dev_count = SIZE_CONFIG[tier]
        emp_count = rng.randint(min_emp, max_emp)
        cid = f"COMP-{i:03d}"

        # Controlled SoA exclusions on ~20% of companies (e.g., A.7.9 Not Applicable for on-site only)
        soa_exclusions = []
        if i % 5 == 0:
            soa_exclusions.append({"control_id": "A.7.9", "reason": "Nhân sự không mang thiết bị ra ngoài văn phòng."})

        company = store.upsert_company(
            {
                "company_id": cid,
                "name": f"{fake.company()} ({tier.upper()})",
                "industry": INDUSTRIES[(i - 1) % len(INDUSTRIES)],
                "size_tier": tier,
                "employee_count": emp_count,
                "execution_mode": "simulation",
                "baseline_policy": dict(DEFAULT_BASELINE_POLICY),
                "soa_exclusions": soa_exclusions,
            }
        )

        # Pick deterministic fault profile per company to cover all 6 compliance states across corpus
        profile_mode = i % 5
        # 0: mostly healthy | 1: patch + baseline drift | 2: people gaps | 3: cross-domain offboarding | 4: insufficient evidence (nulls)

        terminated_eid = f"NV{min(15, emp_count):03d}"
        inject_offboarding_fault = profile_mode in (2, 3)
        inject_null_evidence = profile_mode == 4
        inject_patch_fault = profile_mode in (1, 3)
        inject_baseline_fault = profile_mode in (1, 2)
        inject_people_fault = profile_mode in (1, 2, 3)

        missing_training, missing_nda, missing_mfa, missing_incident, failed_phishing = 0, 0, 0, 0, 0
        for idx in range(1, emp_count + 1):
            eid = f"NV{idx:03d}"
            is_term = inject_offboarding_fault and eid == terminated_eid
            dept = "Phòng Kế toán" if is_term else DEPARTMENTS[(idx - 1) % len(DEPARTMENTS)]

            if inject_null_evidence and idx <= 3:
                training_done = None
                nda_done = None
                incident_known = None
                phishing_ok = None
                mfa_on = None
            else:
                training_done = not (inject_people_fault and idx % 4 == 0)
                nda_done = not (inject_people_fault and idx % 7 == 0)
                incident_known = not (inject_people_fault and idx % 3 == 0)
                phishing_ok = not (inject_people_fault and idx % 5 == 0)
                mfa_on = not (inject_people_fault and idx % 4 == 1)

            if training_done is False:
                missing_training += 1
            if nda_done is False:
                missing_nda += 1
            if incident_known is False:
                missing_incident += 1
            if phishing_ok is False:
                failed_phishing += 1
            if mfa_on is False:
                missing_mfa += 1

            store.upsert_employee(
                cid,
                {
                    "employee_id": eid,
                    "full_name": fake.name(),
                    "department": dept,
                    "role_title": "Kế toán" if dept == "Phòng Kế toán" else "Chuyên viên",
                    "employment_status": "terminated" if is_term else "active",
                    "terminated_at": "2026-11-18T10:00:00+00:00" if is_term else None,
                    "screened": True,
                    "contract_signed": True,
                    "training_completed": training_done,
                    "training_score": 90.0 if training_done else (None if training_done is None else 42.0),
                    "nda_signed": nda_done,
                    "phishing_passed": phishing_ok,
                    "incident_process_known": incident_known,
                    "remote_work_compliant": True,
                    "offboarding_ack": False if is_term else True,
                },
            )
            store.upsert_account(
                cid,
                {
                    "account_id": f"AD-{eid}",
                    "employee_id": eid,
                    "system_type": "active_directory",
                    "is_active": True,
                    "mfa_enabled": mfa_on,
                    "is_privileged": idx == 1,
                },
            )
            if is_term:
                for sys_type, prefix in (("vpn", "VPN"), ("email", "MAIL"), ("accounting_app", "ACC")):
                    store.upsert_account(
                        cid,
                        {
                            "account_id": f"{prefix}-{eid}",
                            "employee_id": eid,
                            "system_type": sys_type,
                            "is_active": True,
                            "mfa_enabled": True,
                            "is_privileged": sys_type == "accounting_app",
                        },
                    )

        # Devices
        unpatched_devices: list[str] = []
        drifted_devices: list[str] = []
        for d in range(1, dev_count + 1):
            did = f"PC-{d:02d}"
            is_unpatched = inject_patch_fault and d in (3, 6)
            is_drifted = inject_baseline_fault and d == 2
            is_null_dev = inject_null_evidence and d == 1
            if is_unpatched:
                unpatched_devices.append(did)
            if is_drifted:
                drifted_devices.append(did)

            store.upsert_device(
                cid,
                {
                    "device_id": did,
                    "hostname": f"{did.lower()}.{cid.lower()}.local",
                    "os_type": "ubuntu" if d == dev_count else "windows11",
                    "assigned_employee_id": f"NV{d:03d}",
                    "badge_card_active": True,
                    "returned_to_it": False,
                    "firewall_enabled": None if is_null_dev else (False if is_drifted else True),
                    "screen_lock_minutes": None if is_null_dev else (30 if is_drifted else 5),
                    "disk_encrypted": None if is_null_dev else (False if is_drifted else True),
                    "password_policy_ok": None if is_null_dev else (False if is_drifted else True),
                    "antivirus_active": True,
                    "ntp_synced": True,
                    "patch_compliant": None if is_null_dev else (not is_unpatched),
                    "missing_patches": ["KB5044285"] if is_unpatched else [],
                    "usb_unauthorized_events": 1 if (profile_mode == 3 and d == 4) else 0,
                    "disposal_verified": None,
                    "installed_software": (
                        ["Microsoft Office", "TorrentClient-Unauthorized"]
                        if (profile_mode == 2 and d == 5)
                        else ["Microsoft Office", "Google Chrome", "CrowdStrike Falcon"]
                    ),
                    "audit_logging_enabled": True,
                },
            )

        if inject_offboarding_fault:
            store.upsert_device(
                cid,
                {
                    "device_id": f"LT-{terminated_eid}",
                    "hostname": f"lt-{terminated_eid.lower()}.{cid.lower()}.local",
                    "os_type": "windows11",
                    "assigned_employee_id": terminated_eid,
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

        # Record Ground Truth per control for Benchmark evaluation
        if inject_null_evidence:
            store.save_ground_truth(cid, "A.8.8", "Insufficient Evidence", [{"reason": "null_patch_telemetry"}], [])
            store.save_ground_truth(cid, "A.8.9", "Insufficient Evidence", [{"reason": "null_baseline_telemetry"}], [])
            store.save_ground_truth(cid, "A.6.3", "Insufficient Evidence", [{"reason": "missing_training_records"}], [])
            store.save_ground_truth(cid, "A.6.6", "Insufficient Evidence", [{"reason": "missing_nda_records"}], [])
            store.save_ground_truth(cid, "A.8.5", "Insufficient Evidence", [{"reason": "missing_mfa_records"}], [])
            store.save_ground_truth(cid, "A.6.8", "Insufficient Evidence", [{"reason": "missing_incident_records"}], [])
        else:
            store.save_ground_truth(
                cid,
                "A.8.8",
                "Partial" if unpatched_devices else "Compliant",
                [{"device_id": d} for d in unpatched_devices],
                ["deploy_security_patches"] if unpatched_devices else [],
            )
            store.save_ground_truth(
                cid,
                "A.8.9",
                "Partial" if drifted_devices else "Compliant",
                [{"device_id": d} for d in drifted_devices],
                ["sync_device_baseline_gpo"] if drifted_devices else [],
            )
            store.save_ground_truth(
                cid,
                "A.6.3",
                "Partial" if (missing_training or failed_phishing) else "Compliant",
                [{"missing_training": missing_training, "failed_phishing": failed_phishing}] if (missing_training or failed_phishing) else [],
                ["assign_security_training"] if (missing_training or failed_phishing) else [],
            )
            store.save_ground_truth(
                cid,
                "A.6.6",
                "Partial" if missing_nda else "Compliant",
                [{"missing_nda": missing_nda}] if missing_nda else [],
                ["send_nda_reminder"] if missing_nda else [],
            )
            store.save_ground_truth(
                cid,
                "A.8.5",
                "Partial" if missing_mfa else "Compliant",
                [{"missing_mfa": missing_mfa}] if missing_mfa else [],
                ["create_it_remediation_ticket"] if missing_mfa else [],
            )
            store.save_ground_truth(
                cid,
                "A.6.8",
                "Partial" if missing_incident else "Compliant",
                [{"missing_incident": missing_incident}] if missing_incident else [],
                ["assign_security_training"] if missing_incident else [],
            )

        store.save_ground_truth(
            cid,
            "A.6.5",
            "Non-compliant" if inject_offboarding_fault else "Compliant",
            [{"employee_id": terminated_eid}] if inject_offboarding_fault else [],
            ["disable_ad_and_revoke_access", "create_it_remediation_ticket"] if inject_offboarding_fault else [],
        )
        store.save_ground_truth(
            cid,
            "A.5.18",
            "Non-compliant" if inject_offboarding_fault else "Compliant",
            [{"employee_id": terminated_eid}] if inject_offboarding_fault else [],
            ["disable_ad_and_revoke_access"] if inject_offboarding_fault else [],
        )
        store.save_ground_truth(
            cid,
            "A.5.11",
            "Non-compliant" if inject_offboarding_fault else "Compliant",
            [{"employee_id": terminated_eid, "device_id": f"LT-{terminated_eid}"}] if inject_offboarding_fault else [],
            ["create_it_remediation_ticket"] if inject_offboarding_fault else [],
        )
        if soa_exclusions:
            store.save_ground_truth(cid, "A.7.9", "Not Applicable", [], [])

        created.append(company)

    return created
