import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from typing import Dict, Any, List
from pydantic import BaseModel, Field

# =====================================================================
# 1. KHUNG CHUẨN HÓA BẰNG CHỨNG ĐẦU RA (GỬI CHO AGENT CORE CỦA TOÀN)
# =====================================================================
class StandardizedEvidenceRecord(BaseModel):
    evidence_id: str = Field(..., description="Mã định danh bằng chứng duy nhất")
    evidence_type: str = Field(..., description="Mã loại bằng chứng theo evidence_taxonomy.json")
    related_controls: List[str] = Field(..., description="Các mã control ISO 27001 liên quan")
    source_host: str = Field(..., description="Tên thiết bị hoặc đường dẫn file nguồn")
    collection_method: str = Field(default="READ_ONLY_COLLECTOR", description="Phương thức thu thập")
    collected_at_utc: str = Field(..., description="Thời gian thu thập chuẩn ISO-8601 UTC")
    sha256_hash: str = Field(..., description="Mã băm SHA-256 đảm bảo tính toàn vẹn của bằng chứng")
    content: Dict[str, Any] = Field(..., description="Nội dung bằng chứng đã chuẩn hóa")

def compute_sha256(data: Dict[str, Any]) -> str:
    """Tính mã băm SHA-256 cho nội dung bằng chứng để chống chỉnh sửa."""
    raw_bytes = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw_bytes).hexdigest()

def run_readonly_command(cmd: List[str]) -> str:
    """Thực thi lệnh hệ thống ở chế độ chỉ đọc (Read-only) với timeout an toàn."""
    try:
        output = subprocess.check_output(
            cmd,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace",
            timeout=10
        )
        return output.strip()
    except Exception as e:
        return f"READ_ONLY_CHECK_ERROR: {str(e)}"

# =====================================================================
# 2. BỘ THU THẬP BẰNG CHỨNG KỸ THUẬT THỬ NGHIỆM (TUẦN 1 POC)
# =====================================================================
def collect_local_technical_evidence() -> List[StandardizedEvidenceRecord]:
    os_type = platform.system()
    hostname = platform.node()
    now_utc = datetime.now(timezone.utc).isoformat()
    records: List[StandardizedEvidenceRecord] = []

    # --- 1. Thu thập bằng chứng A.8.5 (Chính sách xác thực / tài khoản) ---
    if os_type == "Windows":
        auth_raw = run_readonly_command(["net", "accounts"])
    else:
        auth_raw = run_readonly_command(["grep", "-E", "^(PASS_MAX_DAYS|PASS_MIN_LEN)", "/etc/login.defs"])

    auth_content = {
        "os_platform": os_type,
        "check_item": "Account & Password Policy (Read-only snapshot)",
        "raw_output": auth_raw
    }
    records.append(
        StandardizedEvidenceRecord(
            evidence_id="EVID-TECH-A85-001",
            evidence_type="EVID_TECH_IAM_AUTH",
            related_controls=["A.8.5"],
            source_host=hostname,
            collected_at_utc=now_utc,
            sha256_hash=compute_sha256(auth_content),
            content=auth_content
        )
    )

    # --- 2. Thu thập bằng chứng A.8.20 (Trạng thái Firewall) ---
    if os_type == "Windows":
        fw_raw = run_readonly_command(["netsh", "advfirewall", "show", "allprofiles", "state"])
    else:
        fw_raw = run_readonly_command(["ufw", "status"])

    fw_content = {
        "os_platform": os_type,
        "check_item": "Host Firewall Status (Read-only snapshot)",
        "raw_output": fw_raw
    }
    records.append(
        StandardizedEvidenceRecord(
            evidence_id="EVID-TECH-A820-001",
            evidence_type="EVID_TECH_NET_FIREWALL",
            related_controls=["A.8.20"],
            source_host=hostname,
            collected_at_utc=now_utc,
            sha256_hash=compute_sha256(fw_content),
            content=fw_content
        )
    )

    # --- 3. Thu thập bằng chứng A.8.17 (Đồng bộ thời gian NTP / W32Time) ---
    if os_type == "Windows":
        ntp_raw = run_readonly_command(["w32tm", "/query", "/status"])
    else:
        ntp_raw = run_readonly_command(["timedatectl", "status"])

    ntp_content = {
        "os_platform": os_type,
        "check_item": "Clock Synchronization Status (Read-only snapshot)",
        "raw_output": ntp_raw
    }
    records.append(
        StandardizedEvidenceRecord(
            evidence_id="EVID-TECH-A817-001",
            evidence_type="EVID_TECH_BACKUP_LOG",
            related_controls=["A.8.17"],
            source_host=hostname,
            collected_at_utc=now_utc,
            sha256_hash=compute_sha256(ntp_content),
            content=ntp_content
        )
    )

    return records

if __name__ == "__main__":
    print("=== CHẠY THỬ BỘ THU THẬP BẰNG CHỨNG READ-ONLY (TUẦN 1 - LÊ ĐĂNG KHOA) ===")
    collected = collect_local_technical_evidence()
    output_json = [item.model_dump() for item in collected]
    print(json.dumps(output_json, ensure_ascii=False, indent=2))