"""Registers all 12 parameterized playbooks across LOW, MEDIUM, and HIGH risk tiers."""
from __future__ import annotations

from backend.pc_storage import BasePCStore
from lab_adapters.base import ExecutionAdapter
from tools.registry import ToolDefinition, ToolRegistry
from tools.schemas import (
    AssignSecurityTrainingParams,
    CreateItTicketParams,
    DeployPatchesParams,
    DisableAdRevokeParams,
    EnableAntivirusParams,
    EnforceDiskEncryptionParams,
    InspectDeviceBaselineParams,
    InspectHumanParams,
    InspectIdentityAccessParams,
    RemoveUnauthorizedSoftwareParams,
    SendNdaReminderParams,
    SyncDeviceBaselineParams,
)


def build_default_tool_registry(store: BasePCStore, adapter: ExecutionAdapter) -> ToolRegistry:
    registry = ToolRegistry(store=store, adapter=adapter)

    # --- LOW RISK (Read-only & non-destructive workflows) ---
    registry.register(
        ToolDefinition(
            name="inspect_human_records",
            risk_level="LOW",
            param_schema=InspectHumanParams,
            description="Đọc trạng thái hồ sơ nhân sự (A.6.1-A.6.8) theo company_id.",
            handler=lambda ad, cid, p, dry: ad.inspect_human_records(cid, department=p.department, employee_id=p.employee_id),
        )
    )
    registry.register(
        ToolDefinition(
            name="inspect_device_baseline",
            risk_level="LOW",
            param_schema=InspectDeviceBaselineParams,
            description="Đọc trạng thái baseline & bản vá máy trạm/server (A.7.7, A.8.1, A.8.8, A.8.9, A.8.24).",
            handler=lambda ad, cid, p, dry: ad.inspect_device_baseline(cid, device_ids=p.device_ids),
        )
    )
    registry.register(
        ToolDefinition(
            name="inspect_identity_access",
            risk_level="LOW",
            param_schema=InspectIdentityAccessParams,
            description="Đọc trạng thái tài khoản AD/VPN/Email/Ứng dụng và MFA (A.5.16, A.5.18, A.8.2, A.8.5).",
            handler=lambda ad, cid, p, dry: ad.inspect_identity_access(cid, employee_id=p.employee_id, systems=p.systems),
        )
    )
    registry.register(
        ToolDefinition(
            name="send_nda_reminder",
            risk_level="LOW",
            param_schema=SendNdaReminderParams,
            description="Tự động gửi nhắc nhở ký NDA cho nhân sự còn thiếu (A.6.6).",
            handler=lambda ad, cid, p, dry: ad.send_nda_reminder(cid, p.employee_ids, p.deadline_days, dry_run=dry),
        )
    )
    registry.register(
        ToolDefinition(
            name="assign_security_training",
            risk_level="LOW",
            param_schema=AssignSecurityTrainingParams,
            description="Tự động giao khóa đào tạo ATTT / chống phishing bổ sung (A.6.3, A.6.8).",
            handler=lambda ad, cid, p, dry: ad.assign_security_training(cid, p.employee_ids, p.module_code, dry_run=dry),
        )
    )
    registry.register(
        ToolDefinition(
            name="create_it_remediation_ticket",
            risk_level="LOW",
            param_schema=CreateItTicketParams,
            description="Tạo ticket IT / phiếu thu hồi tài sản phần cứng (A.5.11, A.8.5).",
            handler=lambda ad, cid, p, dry: ad.create_it_remediation_ticket(cid, p.control_id, p.target_id, p.summary, p.priority, dry_run=dry),
        )
    )

    # --- MEDIUM RISK (Compatibility Check + Snapshot before execution + Rollback) ---
    registry.register(
        ToolDefinition(
            name="deploy_security_patches",
            risk_level="MEDIUM",
            param_schema=DeployPatchesParams,
            description="Cập nhật bản vá bảo mật cho danh sách máy trạm (A.8.8) kèm kiểm tra tương thích & snapshot.",
            handler=lambda ad, cid, p, dry: ad.deploy_security_patches(cid, p.device_ids, p.patch_ids, p.maintenance_window, dry_run=dry),
            snapshot_fn=lambda ad, cid, p: ad.snapshot_devices(cid, p.device_ids),
            compatibility_fn=lambda ad, cid, p: ad.check_patch_compatibility(cid, p.device_ids, p.patch_ids),
        )
    )
    registry.register(
        ToolDefinition(
            name="sync_device_baseline_gpo",
            risk_level="MEDIUM",
            param_schema=SyncDeviceBaselineParams,
            description="Đồng bộ Security Baseline GPO/PowerShell (A.8.9) kèm snapshot cấu hình cũ & rollback.",
            handler=lambda ad, cid, p, dry: ad.sync_device_baseline_gpo(cid, p.device_id, p.baseline_profile_id, dry_run=dry),
            snapshot_fn=lambda ad, cid, p: ad.snapshot_devices(cid, [p.device_id]),
        )
    )
    registry.register(
        ToolDefinition(
            name="enable_endpoint_antivirus",
            risk_level="MEDIUM",
            param_schema=EnableAntivirusParams,
            description="Bật lại dịch vụ Antivirus/EDR trên máy trạm (A.8.7) kèm snapshot.",
            handler=lambda ad, cid, p, dry: ad.enable_endpoint_antivirus(cid, p.device_id, dry_run=dry),
            snapshot_fn=lambda ad, cid, p: ad.snapshot_devices(cid, [p.device_id]),
        )
    )

    # --- HIGH RISK (Mandatory Human-in-the-loop Approval + Snapshot + Rollback) ---
    registry.register(
        ToolDefinition(
            name="disable_ad_and_revoke_access",
            risk_level="HIGH",
            param_schema=DisableAdRevokeParams,
            description="Khóa tài khoản Active Directory và thu hồi quyền VPN/Email/Ứng dụng (A.5.18, A.6.5) - bắt buộc Admin duyệt.",
            handler=lambda ad, cid, p, dry: ad.disable_ad_and_revoke_access(cid, p.employee_id, list(p.systems), p.reason_ticket, dry_run=dry),
            snapshot_fn=lambda ad, cid, p: ad.snapshot_identity_access(cid, p.employee_id, list(p.systems)),
        )
    )
    registry.register(
        ToolDefinition(
            name="enforce_disk_encryption",
            risk_level="HIGH",
            param_schema=EnforceDiskEncryptionParams,
            description="Ép kích hoạt mã hóa ổ đĩa BitLocker/LUKS (A.8.24) - bắt buộc Admin duyệt.",
            handler=lambda ad, cid, p, dry: ad.enforce_disk_encryption(cid, p.device_id, p.recovery_key_vault_ref, dry_run=dry),
            snapshot_fn=lambda ad, cid, p: ad.snapshot_devices(cid, [p.device_id]),
        )
    )
    registry.register(
        ToolDefinition(
            name="remove_unauthorized_software",
            risk_level="HIGH",
            param_schema=RemoveUnauthorizedSoftwareParams,
            description="Gỡ bỏ phần mềm ngoài Whitelist (A.8.19) - bắt buộc Admin duyệt.",
            handler=lambda ad, cid, p, dry: ad.remove_unauthorized_software(cid, p.device_id, p.package_name, dry_run=dry),
            snapshot_fn=lambda ad, cid, p: ad.snapshot_devices(cid, [p.device_id]),
        )
    )

    return registry
