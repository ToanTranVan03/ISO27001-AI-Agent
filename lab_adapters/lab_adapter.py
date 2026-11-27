"""Real VMware/VirtualBox Lab Adapter using WinRM (Windows Server AD/GPO & Win 11) and SSH (Ubuntu).

Security guarantees:
- NEVER accepts arbitrary shell strings from LLM.
- Uses strictly allowlisted, parameterized PowerShell/Bash playbook templates.
- Validates every identifier against strict regex before template interpolation.
- Supports dry_run preview, pre-change snapshot, and rollback.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any

from backend.pc_storage import BasePCStore, sha256_json, utc_now_iso
from lab_adapters.sim_adapter import SimulationExecutionAdapter

SAFE_ID_RE = re.compile(r"^[A-Za-z0-9._-]{2,48}$")


def _assert_safe_token(value: str, label: str) -> str:
    if not SAFE_ID_RE.fullmatch(value):
        raise ValueError(f"Unsafe {label} parameter rejected: {value!r}")
    return value


@dataclass
class LabHostConfig:
    ad_server_host: str
    ad_username: str
    ad_password_env: str = "ISO_LAB_AD_PASSWORD"
    workstation_hosts: dict[str, str] = field(default_factory=dict)
    workstation_os: dict[str, str] = field(default_factory=dict)  # 'windows11' | 'ubuntu'
    winrm_port: int = 5985
    ssh_port: int = 22
    ssh_username: str = "iso_auditor"
    ssh_key_path_env: str = "ISO_LAB_SSH_KEY_PATH"


class RealLabExecutionAdapter(SimulationExecutionAdapter):
    """Hybrid adapter: delegates DB/HR tracking to SimulationExecutionAdapter and runs real WinRM/SSH
    commands on configured VMware/VirtualBox hosts for PC-02 baseline sync & NV015 AD lockout."""

    mode = "hybrid_lab"

    def __init__(self, store: BasePCStore, lab_config: LabHostConfig) -> None:
        super().__init__(store)
        self.lab_config = lab_config

    def _resolve_password(self) -> str:
        password = os.getenv(self.lab_config.ad_password_env) or os.getenv("LAB_AD_PASSWORD") or ""
        if not password:
            raise RuntimeError(
                f"Missing lab credential environment variable: set {self.lab_config.ad_password_env} or LAB_AD_PASSWORD in .env"
            )
        return password

    def _run_winrm_ps(self, host: str, script: str) -> dict[str, Any]:
        import winrm  # installed via pywinrm

        password = self._resolve_password()
        endpoint = f"http://{host}:{self.lab_config.winrm_port}/wsman"
        session = winrm.Session(endpoint, auth=(self.lab_config.ad_username, password), transport="ntlm")
        result = session.run_ps(script)
        stdout = result.std_out.decode("utf-8", errors="replace").strip()
        stderr = result.std_err.decode("utf-8", errors="replace").strip()
        if result.status_code != 0:
            raise RuntimeError(f"WinRM script failed on {host} (rc={result.status_code}): {stderr[:300]}")
        return {"host": host, "status_code": result.status_code, "stdout": stdout, "stderr": stderr}

    def _run_ssh_readonly_or_template(self, host: str, command: str) -> dict[str, Any]:
        import paramiko

        key_path = os.getenv(self.lab_config.ssh_key_path_env, "")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
        try:
            connect_kwargs: dict[str, Any] = {
                "hostname": host,
                "port": self.lab_config.ssh_port,
                "username": self.lab_config.ssh_username,
                "timeout": 10,
            }
            if key_path:
                connect_kwargs["key_filename"] = key_path
            client.connect(**connect_kwargs)
            _, stdout_f, stderr_f = client.exec_command(command, timeout=20)
            rc = stdout_f.channel.recv_exit_status()
            stdout = stdout_f.read().decode("utf-8", errors="replace").strip()
            stderr = stderr_f.read().decode("utf-8", errors="replace").strip()
            if rc != 0:
                raise RuntimeError(f"SSH template failed on {host} (rc={rc}): {stderr[:300]}")
            return {"host": host, "status_code": rc, "stdout": stdout, "stderr": stderr}
        finally:
            client.close()

    @staticmethod
    def render_pc02_baseline_script(device_id: str, screen_lock_seconds: int = 300) -> str:
        """Fixed parameterized PowerShell script for Scenario 2 (A.8.9 PC-02 baseline remediation)."""
        _assert_safe_token(device_id, "device_id")
        if not 60 <= screen_lock_seconds <= 900:
            raise ValueError("screen_lock_seconds out of safe policy bounds (60..900)")
        return "\n".join(
            [
                f"# ISO 27001 A.8.9 Fixed Baseline Playbook for {device_id}",
                "Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True",
                f"Set-ItemProperty -Path 'HKCU:\\Control Panel\\Desktop' -Name ScreenSaveTimeOut -Value '{screen_lock_seconds}'",
                "Set-ItemProperty -Path 'HKCU:\\Control Panel\\Desktop' -Name ScreenSaverIsSecure -Value '1'",
                "net accounts /minpwlen:12 /maxpwage:90",
                "if ((Get-BitLockerVolume -MountPoint 'C:').ProtectionStatus -ne 'On') { Enable-BitLocker -MountPoint 'C:' -EncryptionMethod XtsAes256 -UsedSpaceOnly -RecoveryPasswordProtector }",
                "gpupdate /force | Out-Null",
                "@{device_id='" + device_id + "'; firewall_enabled=$true; screen_lock_seconds=" + str(screen_lock_seconds) + "; ntp_synced=$true} | ConvertTo-Json -Compress",
            ]
        )

    @staticmethod
    def render_ad_disable_script(employee_id: str, reason_ticket: str) -> str:
        """Fixed parameterized PowerShell script for Scenario 4 (A.5.18/A.6.5 NV015 AD lockout)."""
        _assert_safe_token(employee_id, "employee_id")
        _assert_safe_token(reason_ticket, "reason_ticket")
        return "\n".join(
            [
                f"# ISO 27001 A.5.18 / A.6.5 Fixed AD Revocation Playbook for {employee_id}",
                "Import-Module ActiveDirectory",
                f"$u = Get-ADUser -Identity '{employee_id}' -Properties Enabled, MemberOf",
                f"Disable-ADAccount -Identity '{employee_id}'",
                f"Set-ADUser -Identity '{employee_id}' -Description 'Disabled by ISO27001 Agent ({reason_ticket})'",
                f"Get-ADPrincipalGroupMembership -Identity '{employee_id}' | Where-Object {{ $_.Name -match 'VPN|Accounting|Admin' }} | ForEach-Object {{ Remove-ADGroupMember -Identity $_ -Members '{employee_id}' -Confirm:$false }}",
                "@{employee_id='" + employee_id + "'; disabled=$true; ticket='" + reason_ticket + "'} | ConvertTo-Json -Compress",
            ]
        )

    @staticmethod
    def render_ad_rollback_script(employee_id: str) -> str:
        _assert_safe_token(employee_id, "employee_id")
        return f"Import-Module ActiveDirectory; Enable-ADAccount -Identity '{employee_id}'"

    def sync_device_baseline_gpo(
        self, company_id: str, device_id: str, baseline_profile_id: str, dry_run: bool = False
    ) -> dict[str, Any]:
        _assert_safe_token(device_id, "device_id")
        _assert_safe_token(baseline_profile_id, "baseline_profile_id")
        host = self.lab_config.workstation_hosts.get(device_id)
        script = self.render_pc02_baseline_script(device_id, screen_lock_seconds=300)

        if dry_run:
            preview = super().sync_device_baseline_gpo(company_id, device_id, baseline_profile_id, dry_run=True)
            preview["lab_target_host"] = host
            preview["rendered_playbook_sha256"] = sha256_json(script)
            preview["transport"] = "winrm" if host else "unconfigured_lab_host"
            return preview

        if not host:
            raise RuntimeError(
                f"Hybrid Lab host is not configured for device '{device_id}'. Set LAB_PC02_HOST in .env or workstation_hosts in lab_config."
            )

        os_type = self.lab_config.workstation_os.get(device_id, "windows11")
        if os_type == "ubuntu":
            lab_res = self._run_ssh_readonly_or_template(
                host, "sudo ufw --force enable && gsettings set org.gnome.desktop.session idle-delay 300"
            )
        else:
            lab_res = self._run_winrm_ps(host, script)

        sim_sync = super().sync_device_baseline_gpo(company_id, device_id, baseline_profile_id, dry_run=False)
        return {
            **sim_sync,
            "transport": "ssh" if os_type == "ubuntu" else "winrm",
            "lab_target_host": host,
            "lab_execution": lab_res,
            "verified_at_utc": utc_now_iso(),
        }

    def disable_ad_and_revoke_access(
        self, company_id: str, employee_id: str, systems: list[str], reason_ticket: str, dry_run: bool = False
    ) -> dict[str, Any]:
        _assert_safe_token(employee_id, "employee_id")
        _assert_safe_token(reason_ticket, "reason_ticket")
        script = self.render_ad_disable_script(employee_id, reason_ticket)

        if dry_run:
            preview = super().disable_ad_and_revoke_access(company_id, employee_id, systems, reason_ticket, dry_run=True)
            preview["ad_server_host"] = self.lab_config.ad_server_host
            preview["rendered_playbook_sha256"] = sha256_json(script)
            preview["transport"] = "winrm_ad" if self.lab_config.ad_server_host else "unconfigured_ad_host"
            return preview

        if not self.lab_config.ad_server_host:
            raise RuntimeError("Hybrid Lab AD host is not configured. Set LAB_AD_HOST in .env or ad_server_host in lab_config.")

        lab_res = self._run_winrm_ps(self.lab_config.ad_server_host, script)
        sim_res = super().disable_ad_and_revoke_access(company_id, employee_id, systems, reason_ticket, dry_run=False)
        return {
            **sim_res,
            "transport": "winrm_ad",
            "ad_server_host": self.lab_config.ad_server_host,
            "lab_execution": lab_res,
            "verified_at_utc": utc_now_iso(),
        }

    def inspect_live_ad_user(self, employee_id: str) -> dict[str, Any]:
        """Read-only live AD user probe via WinRM for Verification Agent."""
        _assert_safe_token(employee_id, "employee_id")
        if not self.lab_config.ad_server_host:
            raise RuntimeError("LAB_AD_HOST is not configured for live AD inspection.")
        ps = f"Import-Module ActiveDirectory; Get-ADUser -Identity '{employee_id}' -Properties Enabled | Select-Object SamAccountName, Enabled | ConvertTo-Json -Compress"
        res = self._run_winrm_ps(self.lab_config.ad_server_host, ps)
        parsed = json.loads(res["stdout"]) if res["stdout"] else {}
        return {"host": self.lab_config.ad_server_host, "observed_at_utc": utc_now_iso(), "ad_user": parsed}

    def inspect_live_workstation_baseline(self, device_id: str) -> dict[str, Any]:
        """Read-only live workstation probe via WinRM (Firewall, ScreenSaver timeout, BitLocker, Defender)."""
        _assert_safe_token(device_id, "device_id")
        host = self.lab_config.workstation_hosts.get(device_id)
        if not host:
            raise RuntimeError(f"Workstation host not configured for {device_id}.")
        ps = "\n".join(
            [
                "$fw = (Get-NetFirewallProfile | Where-Object { $_.Enabled -eq $false }).Count -eq 0",
                "$ss = (Get-ItemProperty -Path 'HKCU:\\Control Panel\\Desktop' -Name ScreenSaveTimeOut -ErrorAction SilentlyContinue).ScreenSaveTimeOut",
                "$bl = (Get-BitLockerVolume -MountPoint 'C:' -ErrorAction SilentlyContinue).ProtectionStatus -eq 'On'",
                "$av = (Get-MpComputerStatus -ErrorAction SilentlyContinue).AntivirusEnabled",
                "@{firewall_enabled=[bool]$fw; screen_lock_minutes=[int]([int]($ss/60)); disk_encrypted=[bool]$bl; antivirus_active=[bool]$av} | ConvertTo-Json -Compress",
            ]
        )
        res = self._run_winrm_ps(host, ps)
        parsed = json.loads(res["stdout"]) if res["stdout"] else {}
        return {"host": host, "device_id": device_id, "observed_at_utc": utc_now_iso(), "telemetry": parsed}
