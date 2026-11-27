"""Abstract execution adapter shared by Simulation DB and Real VMware/VirtualBox Lab (WinRM/SSH)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ExecutionAdapter(ABC):
    """Fixed parameterized operations only. Raw shell execution from LLM is forbidden."""

    mode: str = "simulation"

    @abstractmethod
    def inspect_human_records(self, company_id: str, department: str | None = None, employee_id: str | None = None) -> dict[str, Any]: ...

    @abstractmethod
    def inspect_device_baseline(self, company_id: str, device_ids: list[str] | None = None) -> dict[str, Any]: ...

    @abstractmethod
    def inspect_identity_access(self, company_id: str, employee_id: str | None = None, systems: list[str] | None = None) -> dict[str, Any]: ...

    @abstractmethod
    def send_nda_reminder(self, company_id: str, employee_ids: list[str], deadline_days: int, dry_run: bool = False) -> dict[str, Any]: ...

    @abstractmethod
    def assign_security_training(self, company_id: str, employee_ids: list[str], module_code: str, dry_run: bool = False) -> dict[str, Any]: ...

    @abstractmethod
    def create_it_remediation_ticket(
        self, company_id: str, control_id: str, target_id: str, summary: str, priority: str, dry_run: bool = False
    ) -> dict[str, Any]: ...

    @abstractmethod
    def snapshot_devices(self, company_id: str, device_ids: list[str]) -> dict[str, Any]: ...

    @abstractmethod
    def check_patch_compatibility(self, company_id: str, device_ids: list[str], patch_ids: list[str]) -> dict[str, Any]: ...

    @abstractmethod
    def deploy_security_patches(
        self, company_id: str, device_ids: list[str], patch_ids: list[str], maintenance_window: str, dry_run: bool = False
    ) -> dict[str, Any]: ...

    @abstractmethod
    def sync_device_baseline_gpo(
        self, company_id: str, device_id: str, baseline_profile_id: str, dry_run: bool = False
    ) -> dict[str, Any]: ...

    @abstractmethod
    def enable_endpoint_antivirus(self, company_id: str, device_id: str, dry_run: bool = False) -> dict[str, Any]: ...

    @abstractmethod
    def snapshot_identity_access(self, company_id: str, employee_id: str, systems: list[str]) -> dict[str, Any]: ...

    @abstractmethod
    def disable_ad_and_revoke_access(
        self, company_id: str, employee_id: str, systems: list[str], reason_ticket: str, dry_run: bool = False
    ) -> dict[str, Any]: ...

    @abstractmethod
    def enforce_disk_encryption(
        self, company_id: str, device_id: str, recovery_key_vault_ref: str, dry_run: bool = False
    ) -> dict[str, Any]: ...

    @abstractmethod
    def remove_unauthorized_software(
        self, company_id: str, device_id: str, package_name: str, dry_run: bool = False
    ) -> dict[str, Any]: ...

    @abstractmethod
    def rollback_snapshot(self, company_id: str, snapshot: dict[str, Any]) -> dict[str, Any]: ...
