"""Multi-tenant Simulation Execution Adapter operating cleanly on BasePCStore."""
from __future__ import annotations

import copy
from typing import Any

from backend.pc_storage import BasePCStore, DEFAULT_BASELINE_POLICY, sha256_json, utc_now_iso
from lab_adapters.base import ExecutionAdapter


class SimulationExecutionAdapter(ExecutionAdapter):
    """Executes inspect, snapshot, dry-run, apply, and rollback against a multi-tenant PCStore."""

    mode = "simulation"

    def __init__(self, store: BasePCStore) -> None:
        self.store = store

    def _company_or_raise(self, company_id: str) -> dict[str, Any]:
        comp = self.store.get_company(company_id)
        if not comp:
            raise KeyError(f"Company not found: {company_id}")
        return comp

    def inspect_human_records(self, company_id: str, department: str | None = None, employee_id: str | None = None) -> dict[str, Any]:
        self._company_or_raise(company_id)
        employees = self.store.list_employees(company_id, department=department, employee_id=employee_id)
        payload = {"company_id": company_id, "observed_at_utc": utc_now_iso(), "count": len(employees), "employees": employees}
        payload["sha256_hash"] = sha256_json(employees)
        return payload

    def inspect_device_baseline(self, company_id: str, device_ids: list[str] | None = None) -> dict[str, Any]:
        comp = self._company_or_raise(company_id)
        devices = self.store.list_devices(company_id, device_ids=device_ids)
        policy = comp.get("baseline_policy") or DEFAULT_BASELINE_POLICY
        payload = {
            "company_id": company_id,
            "observed_at_utc": utc_now_iso(),
            "baseline_policy": policy,
            "count": len(devices),
            "devices": devices,
        }
        payload["sha256_hash"] = sha256_json(devices)
        return payload

    def inspect_identity_access(self, company_id: str, employee_id: str | None = None, systems: list[str] | None = None) -> dict[str, Any]:
        self._company_or_raise(company_id)
        accounts = self.store.list_accounts(company_id, employee_id=employee_id, systems=systems)
        payload = {"company_id": company_id, "observed_at_utc": utc_now_iso(), "count": len(accounts), "accounts": accounts}
        payload["sha256_hash"] = sha256_json(accounts)
        return payload

    def send_nda_reminder(self, company_id: str, employee_ids: list[str], deadline_days: int, dry_run: bool = False) -> dict[str, Any]:
        self._company_or_raise(company_id)
        existing = {e["employee_id"] for e in self.store.list_employees(company_id)}
        targets = [eid for eid in employee_ids if eid in existing]
        if dry_run:
            return {"dry_run": True, "action": "send_nda_reminder", "targets": targets, "deadline_days": deadline_days}
        sent = []
        for eid in targets:
            if hasattr(self.store, "add_notification"):
                sent.append(
                    self.store.add_notification(
                        company_id,
                        {"kind": "NDA_REMINDER", "employee_id": eid, "deadline_days": deadline_days},
                    )
                )
            else:
                sent.append({"kind": "NDA_REMINDER", "employee_id": eid, "deadline_days": deadline_days})
        return {"dry_run": False, "sent_count": len(sent), "targets": targets, "status": "PENDING_EVIDENCE"}

    def assign_security_training(self, company_id: str, employee_ids: list[str], module_code: str, dry_run: bool = False) -> dict[str, Any]:
        self._company_or_raise(company_id)
        existing = {e["employee_id"] for e in self.store.list_employees(company_id)}
        targets = [eid for eid in employee_ids if eid in existing]
        if dry_run:
            return {"dry_run": True, "action": "assign_security_training", "targets": targets, "module_code": module_code}
        assigned = []
        for eid in targets:
            if hasattr(self.store, "add_notification"):
                assigned.append(
                    self.store.add_notification(
                        company_id,
                        {"kind": "TRAINING_ASSIGNED", "employee_id": eid, "module_code": module_code},
                    )
                )
            else:
                assigned.append({"kind": "TRAINING_ASSIGNED", "employee_id": eid, "module_code": module_code})
        return {"dry_run": False, "assigned_count": len(assigned), "module_code": module_code, "targets": targets, "status": "PENDING_EVIDENCE"}

    def create_it_remediation_ticket(
        self, company_id: str, control_id: str, target_id: str, summary: str, priority: str, dry_run: bool = False
    ) -> dict[str, Any]:
        self._company_or_raise(company_id)
        ticket_payload = {
            "control_id": control_id,
            "target_id": target_id,
            "summary": summary,
            "priority": priority,
            "status": "OPEN",
        }
        if dry_run:
            return {"dry_run": True, "action": "create_it_remediation_ticket", "ticket": ticket_payload}
        if hasattr(self.store, "add_ticket"):
            saved = self.store.add_ticket(company_id, ticket_payload)
        else:
            saved = {**ticket_payload, "ticket_id": f"TKT-{sha256_json(ticket_payload)[:8].upper()}"}
        return {"dry_run": False, "ticket": saved}

    def snapshot_devices(self, company_id: str, device_ids: list[str]) -> dict[str, Any]:
        devices = self.store.list_devices(company_id, device_ids=device_ids)
        return {
            "snapshot_kind": "devices",
            "company_id": company_id,
            "captured_at_utc": utc_now_iso(),
            "devices": copy.deepcopy(devices),
            "sha256_hash": sha256_json(devices),
        }

    def check_patch_compatibility(self, company_id: str, device_ids: list[str], patch_ids: list[str]) -> dict[str, Any]:
        devices = self.store.list_devices(company_id, device_ids=device_ids)
        found = {d["device_id"]: d for d in devices}
        missing_hosts = [did for did in device_ids if did not in found]
        compatible = len(missing_hosts) == 0 and all(d["os_type"] in ("windows11", "windows_server", "ubuntu") for d in devices)
        return {
            "compatible": compatible,
            "checked_devices": sorted(found.keys()),
            "missing_devices": missing_hosts,
            "patch_ids": list(patch_ids),
            "disk_space_ok": True,
        }

    def deploy_security_patches(
        self, company_id: str, device_ids: list[str], patch_ids: list[str], maintenance_window: str, dry_run: bool = False
    ) -> dict[str, Any]:
        devices = self.store.list_devices(company_id, device_ids=device_ids)
        if dry_run:
            return {
                "dry_run": True,
                "action": "deploy_security_patches",
                "target_devices": [d["device_id"] for d in devices],
                "patches_to_apply": list(patch_ids),
                "maintenance_window": maintenance_window,
            }
        applied: list[dict[str, Any]] = []
        apply_set = set(patch_ids)
        for dev in devices:
            remaining = [p for p in dev.get("missing_patches", []) if p not in apply_set]
            updated = {
                **dev,
                "missing_patches": remaining,
                "patch_compliant": len(remaining) == 0,
            }
            self.store.upsert_device(company_id, updated)
            applied.append({"device_id": dev["device_id"], "patch_compliant": updated["patch_compliant"], "remaining_patches": remaining})
        return {"dry_run": False, "maintenance_window": maintenance_window, "results": applied}

    def sync_device_baseline_gpo(
        self, company_id: str, device_id: str, baseline_profile_id: str, dry_run: bool = False
    ) -> dict[str, Any]:
        comp = self._company_or_raise(company_id)
        policy = comp.get("baseline_policy") or DEFAULT_BASELINE_POLICY
        devices = self.store.list_devices(company_id, device_ids=[device_id])
        if not devices:
            raise KeyError(f"Device not found: {device_id}")
        dev = devices[0]
        target_state = {
            "firewall_enabled": bool(policy.get("firewall_enabled", True)),
            "screen_lock_minutes": int(policy.get("screen_lock_minutes_max", 5)),
            "disk_encrypted": bool(policy.get("disk_encrypted", True)),
            "password_policy_ok": bool(policy.get("password_policy_ok", True)),
            "antivirus_active": bool(policy.get("antivirus_active", True)),
            "ntp_synced": bool(policy.get("ntp_synced", True)),
        }
        if dry_run:
            return {
                "dry_run": True,
                "action": "sync_device_baseline_gpo",
                "device_id": device_id,
                "baseline_profile_id": baseline_profile_id,
                "changes": target_state,
            }
        updated = {**dev, **target_state}
        self.store.upsert_device(company_id, updated)
        return {
            "dry_run": False,
            "device_id": device_id,
            "baseline_profile_id": baseline_profile_id,
            "applied_state": target_state,
        }

    def enable_endpoint_antivirus(self, company_id: str, device_id: str, dry_run: bool = False) -> dict[str, Any]:
        devices = self.store.list_devices(company_id, device_ids=[device_id])
        if not devices:
            raise KeyError(f"Device not found: {device_id}")
        if dry_run:
            return {"dry_run": True, "action": "enable_endpoint_antivirus", "device_id": device_id}
        updated = {**devices[0], "antivirus_active": True}
        self.store.upsert_device(company_id, updated)
        return {"dry_run": False, "device_id": device_id, "antivirus_active": True}

    def snapshot_identity_access(self, company_id: str, employee_id: str, systems: list[str]) -> dict[str, Any]:
        accounts = self.store.list_accounts(company_id, employee_id=employee_id, systems=systems)
        return {
            "snapshot_kind": "accounts",
            "company_id": company_id,
            "employee_id": employee_id,
            "captured_at_utc": utc_now_iso(),
            "accounts": copy.deepcopy(accounts),
            "sha256_hash": sha256_json(accounts),
        }

    def disable_ad_and_revoke_access(
        self, company_id: str, employee_id: str, systems: list[str], reason_ticket: str, dry_run: bool = False
    ) -> dict[str, Any]:
        accounts = self.store.list_accounts(company_id, employee_id=employee_id, systems=systems)
        if dry_run:
            return {
                "dry_run": True,
                "action": "disable_ad_and_revoke_access",
                "employee_id": employee_id,
                "accounts_to_disable": [a["account_id"] for a in accounts if a["is_active"]],
                "systems": list(systems),
                "reason_ticket": reason_ticket,
            }
        disabled = []
        for acc in accounts:
            updated = {**acc, "is_active": False, "is_privileged": False, "change_ticket_id": reason_ticket}
            self.store.upsert_account(company_id, updated)
            disabled.append(acc["account_id"])
        return {
            "dry_run": False,
            "employee_id": employee_id,
            "disabled_accounts": disabled,
            "reason_ticket": reason_ticket,
        }

    def enforce_disk_encryption(
        self, company_id: str, device_id: str, recovery_key_vault_ref: str, dry_run: bool = False
    ) -> dict[str, Any]:
        devices = self.store.list_devices(company_id, device_ids=[device_id])
        if not devices:
            raise KeyError(f"Device not found: {device_id}")
        if dry_run:
            return {"dry_run": True, "action": "enforce_disk_encryption", "device_id": device_id, "vault_ref": recovery_key_vault_ref}
        updated = {**devices[0], "disk_encrypted": True}
        self.store.upsert_device(company_id, updated)
        return {"dry_run": False, "device_id": device_id, "disk_encrypted": True, "vault_ref": recovery_key_vault_ref}

    def remove_unauthorized_software(
        self, company_id: str, device_id: str, package_name: str, dry_run: bool = False
    ) -> dict[str, Any]:
        devices = self.store.list_devices(company_id, device_ids=[device_id])
        if not devices:
            raise KeyError(f"Device not found: {device_id}")
        dev = devices[0]
        if dry_run:
            return {"dry_run": True, "action": "remove_unauthorized_software", "device_id": device_id, "package_name": package_name}
        filtered = [pkg for pkg in dev.get("installed_software", []) if pkg != package_name]
        updated = {**dev, "installed_software": filtered}
        self.store.upsert_device(company_id, updated)
        return {"dry_run": False, "device_id": device_id, "removed": package_name, "remaining_software": filtered}

    def rollback_snapshot(self, company_id: str, snapshot: dict[str, Any]) -> dict[str, Any]:
        if snapshot.get("company_id") != company_id:
            raise PermissionError("Snapshot company_id mismatch during rollback.")
        kind = snapshot.get("snapshot_kind")
        if kind == "devices":
            restored = []
            for dev in snapshot.get("devices", []):
                self.store.upsert_device(company_id, dev)
                restored.append(dev["device_id"])
            return {"rolled_back": True, "kind": "devices", "restored_ids": restored}
        if kind == "accounts":
            restored = []
            for acc in snapshot.get("accounts", []):
                self.store.upsert_account(company_id, acc)
                restored.append(acc["account_id"])
            return {"rolled_back": True, "kind": "accounts", "restored_ids": restored}
        raise ValueError(f"Unsupported snapshot_kind for rollback: {kind}")
