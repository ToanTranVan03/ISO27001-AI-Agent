from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Target(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,50}$")
    hostname: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9.-]{1,100}$")
    snapshot: str = Field(min_length=1, max_length=160)


class LabConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    network: Literal["isolated"]
    targets: list[Target] = Field(max_length=10)


def preview(path: Path, *, dry_run: bool) -> dict[str, object]:
    config = LabConfig.model_validate_json(path.read_bytes())
    if len({target.id for target in config.targets}) != len(config.targets):
        raise ValueError("Mã máy trong allowlist phải duy nhất.")
    return {
        "mode": "DRY_RUN" if dry_run else "CONFIG_CHECK",
        "status": "BLOCKED",
        "connected": False,
        "executed": False,
        "targets": [target.id for target in config.targets],
        "required": [
            "VM Windows cô lập dùng cho thử nghiệm",
            "Chủ lab duyệt allowlist, snapshot và tài khoản giới hạn",
            "Thu bằng chứng nguồn trước và sau thao tác được duyệt",
        ],
    }
