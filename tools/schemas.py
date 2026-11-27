"""Strict Pydantic v2 schemas for Parameterized Tool Calling.

Rejects extra fields and blocks shell metacharacters across all identifiers.
"""
from __future__ import annotations

import re
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{2,64}$")
SAFE_TEXT_FORBIDDEN = re.compile(r"[;`$|]|\$\(|\brm\s+-rf\b|\bInvoke-Expression\b|\biex\b", re.I)


def _validate_safe_id(value: str) -> str:
    if not SAFE_ID_PATTERN.fullmatch(value):
        raise ValueError(f"Identifier contains disallowed characters: {value!r}")
    return value


def _validate_safe_text(value: str) -> str:
    if SAFE_TEXT_FORBIDDEN.search(value):
        raise ValueError("Suspicious shell syntax rejected in parameter text.")
    return value


class StrictToolParams(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class InspectHumanParams(StrictToolParams):
    department: str | None = Field(default=None, max_length=100)
    employee_id: str | None = Field(default=None, max_length=64)

    @field_validator("employee_id")
    @classmethod
    def check_eid(cls, v: str | None) -> str | None:
        return _validate_safe_id(v) if v is not None else None


class InspectDeviceBaselineParams(StrictToolParams):
    device_ids: list[str] | None = Field(default=None, max_length=100)

    @field_validator("device_ids")
    @classmethod
    def check_ids(cls, v: list[str] | None) -> list[str] | None:
        return [_validate_safe_id(item) for item in v] if v is not None else None


class InspectIdentityAccessParams(StrictToolParams):
    employee_id: str | None = Field(default=None, max_length=64)
    systems: list[Literal["active_directory", "vpn", "email", "accounting_app", "erp", "server_ssh"]] | None = None

    @field_validator("employee_id")
    @classmethod
    def check_eid(cls, v: str | None) -> str | None:
        return _validate_safe_id(v) if v is not None else None


class SendNdaReminderParams(StrictToolParams):
    employee_ids: list[str] = Field(min_length=1, max_length=200)
    deadline_days: int = Field(default=5, ge=1, le=30)

    @field_validator("employee_ids")
    @classmethod
    def check_eids(cls, v: list[str]) -> list[str]:
        return [_validate_safe_id(item) for item in v]


class AssignSecurityTrainingParams(StrictToolParams):
    employee_ids: list[str] = Field(min_length=1, max_length=200)
    module_code: str = Field(min_length=3, max_length=48)

    @field_validator("employee_ids")
    @classmethod
    def check_eids(cls, v: list[str]) -> list[str]:
        return [_validate_safe_id(item) for item in v]

    @field_validator("module_code")
    @classmethod
    def check_mod(cls, v: str) -> str:
        return _validate_safe_id(v)


class CreateItTicketParams(StrictToolParams):
    control_id: str = Field(min_length=3, max_length=20)
    target_id: str = Field(min_length=2, max_length=64)
    summary: str = Field(min_length=5, max_length=300)
    priority: Literal["low", "medium", "high", "critical"] = "medium"

    @field_validator("control_id", "target_id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return _validate_safe_id(v)

    @field_validator("summary")
    @classmethod
    def check_summary(cls, v: str) -> str:
        return _validate_safe_text(v)


class DeployPatchesParams(StrictToolParams):
    device_ids: list[str] = Field(min_length=1, max_length=50)
    patch_ids: list[str] = Field(min_length=1, max_length=50)
    maintenance_window: str = Field(min_length=4, max_length=64)

    @field_validator("device_ids", "patch_ids")
    @classmethod
    def check_list(cls, v: list[str]) -> list[str]:
        return [_validate_safe_id(item) for item in v]

    @field_validator("maintenance_window")
    @classmethod
    def check_window(cls, v: str) -> str:
        return _validate_safe_text(v)


class SyncDeviceBaselineParams(StrictToolParams):
    device_id: str = Field(min_length=2, max_length=64)
    baseline_profile_id: str = Field(default="ISO27001-BASELINE-V1", min_length=3, max_length=64)

    @field_validator("device_id", "baseline_profile_id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return _validate_safe_id(v)


class EnableAntivirusParams(StrictToolParams):
    device_id: str = Field(min_length=2, max_length=64)

    @field_validator("device_id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return _validate_safe_id(v)


class DisableAdRevokeParams(StrictToolParams):
    employee_id: str = Field(min_length=2, max_length=64)
    systems: list[Literal["active_directory", "vpn", "email", "accounting_app", "erp", "server_ssh"]] = Field(min_length=1)
    reason_ticket: str = Field(min_length=3, max_length=64)

    @field_validator("employee_id", "reason_ticket")
    @classmethod
    def check_id(cls, v: str) -> str:
        return _validate_safe_id(v)


class EnforceDiskEncryptionParams(StrictToolParams):
    device_id: str = Field(min_length=2, max_length=64)
    recovery_key_vault_ref: str = Field(min_length=4, max_length=64)

    @field_validator("device_id", "recovery_key_vault_ref")
    @classmethod
    def check_id(cls, v: str) -> str:
        return _validate_safe_id(v)


class RemoveUnauthorizedSoftwareParams(StrictToolParams):
    device_id: str = Field(min_length=2, max_length=64)
    package_name: str = Field(min_length=2, max_length=80)

    @field_validator("device_id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return _validate_safe_id(v)

    @field_validator("package_name")
    @classmethod
    def check_pkg(cls, v: str) -> str:
        return _validate_safe_text(v)
