"""
=============================================================================
WEEK 3 BENCHMARK RUNNER — ISO/IEC 27001:2022 AI Agent Compliance Assessment
=============================================================================
Tác giả: Lê Đoàn Văn Tú (ISO/GRC & Ground Truth Lead - Thành viên 2)
Mục đích:
  Chạy 15 kịch bản Ground Truth (docs/week3/ground_truth_testcases.json)
  qua LangGraph AI Agent để đo:
    1. Độ chính xác (Accuracy) — AI chấm đúng bao nhiêu %
    2. Hiệu quả Guardrail      — Bao nhiêu kịch bản "Insufficient Evidence" được chặn đúng
    3. Phát hiện Non-Compliant — AI có bỏ sót vi phạm nào không

Cách chạy:
  py week3_benchmark.py

Yêu cầu:
  - Ollama đang chạy với model qwen2.5:7b  (ollama serve)
  - Đã cài thư viện: pip install -r requirements.txt
=============================================================================
"""

import json
import os
import sys
import re
import time
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any

# ── Thêm thư mục gốc vào sys.path để import agent_core ──────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_core.graph_builder import build_iso_agent_graph

# ════════════════════════════════════════════════════════════════════════════
# 1.  GUARDRAIL SANITIZER (TUẦN 3 — 7 LUẬT BẢO VỆ)
# ════════════════════════════════════════════════════════════════════════════
PROMPT_INJECTION_PATTERNS = [
    r"(?i)ignore\s+previous\s+instructions",
    r"(?i)disregard\s+all\s+prior",
    r"(?i)output\s+['\"]?Compliant['\"]?",
    r"(?i)always\s+return\s+Compliant",
    r"(?i)\[SYSTEM\s+INSTRUCTION:",
    r"(?i)<\|im_start\|>system",
    r"(?i)---BEGIN\s+(ADMIN|OVERRIDE)---",
    r"(?i)act\s+as\s+DAN",
    r"(?i)you\s+are\s+now\s+in\s+debug\s+mode",
    r"(?i)developer\s+mode",
]

TRUSTED_HOST_SUFFIXES = [
    ".vietfintech.local",
    ".vietfintech.corp",
    ".vietfintech.vn",
    "arn:aws:",
    "azure://",
    "gcp://",
    "github.com/vietfintech",
    "gitlab.vietfintech",
]

UNTRUSTED_HOSTS = [
    "pastebin.com", "anonfiles.com", "localhost", "127.0.0.1",
    "temp-mail", "0.0.0.0",
]


def compute_sha256(data: Dict[str, Any]) -> str:
    raw_bytes = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw_bytes).hexdigest()


def sanitize_evidence(evidence: dict) -> tuple:
    """Trả về (is_valid, error_code, reason)"""
    # Luật 4: Schema bắt buộc
    required = ["evidence_id", "evidence_type", "collected_at_utc", "sha256_hash", "content"]
    for f in required:
        if f not in evidence or not evidence[f]:
            return False, "GUARD_ERR_005", f"Thiếu trường bắt buộc: '{f}'"

    # Luật 2: Định dạng hash SHA-256
    hash_val = str(evidence.get("sha256_hash", "")).strip().lower()
    if not re.match(r"^[a-f0-9]{64}$", hash_val):
        return False, "GUARD_ERR_002", f"SHA-256 sai định dạng: '{hash_val[:20]}...'"

    # Luật 1: Timestamp hợp lệ và chưa hết hạn
    try:
        ts = evidence["collected_at_utc"].replace("Z", "+00:00")
        collected_dt = datetime.fromisoformat(ts)
        now_dt = datetime.now(timezone.utc)
        age_days = (now_dt - collected_dt).total_seconds() / 86400.0
        if age_days > 365:
            return False, "GUARD_ERR_001", f"Bằng chứng quá hạn: {age_days:.0f} ngày (> 365)"
        if age_days < -0.1:
            return False, "GUARD_ERR_001", "Tem thời gian ở tương lai — nghi ngờ giả mạo"
    except Exception as e:
        return False, "GUARD_ERR_001", f"Sai định dạng ISO-8601: {e}"

    # Luật 3: Prompt Injection
    content_str = json.dumps(evidence.get("content", {}), ensure_ascii=False)
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, content_str):
            return False, "GUARD_ERR_004", f"Prompt Injection detected: {pattern}"

    # Luật 5: Nguồn thu thập
    source = str(evidence.get("source_host", ""))
    is_trusted = any(suffix in source for suffix in TRUSTED_HOST_SUFFIXES)
    is_untrusted = any(bad in source.lower() for bad in UNTRUSTED_HOSTS)
    if is_untrusted and not is_trusted:
        return False, "GUARD_ERR_006", f"Nguồn không tin cậy: '{source}'"

    # Luật 6: Kích thước payload
    content_bytes = len(content_str.encode("utf-8"))
    if content_bytes < 20:
        return False, "GUARD_ERR_007", "Payload quá nhỏ (< 20 bytes)"
    if content_bytes > 2_000_000:
        return False, "GUARD_ERR_007", f"Payload quá lớn ({content_bytes:,} bytes > 2MB)"

    return True, "OK", "Bằng chứng hợp lệ ✓"


# ════════════════════════════════════════════════════════════════════════════
# 2.  TẢI DỮ LIỆU GROUND TRUTH (TUẦN 3)
# ════════════════════════════════════════════════════════════════════════════
def load_ground_truth(path: str) -> List[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["testcases"]


# ════════════════════════════════════════════════════════════════════════════
# 3.  CHẠY MỘT KỊCH BẢN QUA LANGGRAPH
# ════════════════════════════════════════════════════════════════════════════
def run_one_testcase(graph, tc: dict) -> dict:
    """Chạy 1 test case qua LangGraph Agent và trả kết quả so sánh."""

    # ── 3a. Guardrail: lọc bằng chứng trước ───────────────────────────────
    valid_evidences = []
    blocked = []
    for ev in tc["evidences"]:
        ok, code, reason = sanitize_evidence(ev)
        if ok:
            # Ép content thành string nếu LangGraph cũ cần str
            ev_safe = dict(ev)
            if isinstance(ev_safe.get("content"), dict):
                ev_safe["content"] = json.dumps(ev_safe["content"], ensure_ascii=False)
            valid_evidences.append(ev_safe)
        else:
            blocked.append({"evidence_id": ev.get("evidence_id"), "code": code, "reason": reason})

    # ── 3b. Nếu mọi bằng chứng bị chặn → Insufficient Evidence ngay ───────
    if not valid_evidences:
        return {
            "testcase_id": tc["testcase_id"],
            "control_id": tc["control_id"],
            "scenario_type": tc["scenario_type"],
            "expected_status": tc["expected_status"],
            "ai_status": "Insufficient Evidence",
            "ai_confidence": 1.0,
            "ai_rationale": f"[GUARDRAIL BLOCKED] {blocked[0]['reason'] if blocked else 'No valid evidence'}",
            "match": tc["expected_status"] == "Insufficient Evidence",
            "guardrail_triggered": True,
            "blocked_evidences": blocked,
            "latency_sec": 0.0,
        }

    # ── 3c. Xây dựng State ban đầu cho LangGraph ──────────────────────────
    initial_state = {
        "control_id": tc["control_id"],
        "control_name": tc["control_name"],
        "objective": tc.get("scenario_description", ""),
        "collected_evidences": valid_evidences,
        "deterministic_rule": tc.get("deterministic_rule", {}),
        "compliance_status": "UNKNOWN",
        "confidence": 0.0,
        "rationale": "",
        "audit_trail": [],
    }

    # ── 3d. Gọi LangGraph ─────────────────────────────────────────────────
    t0 = time.time()
    try:
        final_state = graph.invoke(initial_state)
        latency = round(time.time() - t0, 2)

        ai_status = final_state["compliance_status"]
        ai_conf = final_state["confidence"]
        ai_rationale = final_state["rationale"]

    except Exception as e:
        latency = round(time.time() - t0, 2)
        ai_status = "ERROR"
        ai_conf = 0.0
        ai_rationale = f"[EXCEPTION] {e}"

    match = (ai_status == tc["expected_status"])
    return {
        "testcase_id": tc["testcase_id"],
        "control_id": tc["control_id"],
        "scenario_type": tc["scenario_type"],
        "expected_status": tc["expected_status"],
        "ai_status": ai_status,
        "ai_confidence": ai_conf,
        "ai_rationale": ai_rationale,
        "match": match,
        "guardrail_triggered": False,
        "blocked_evidences": blocked,
        "latency_sec": latency,
    }


# ════════════════════════════════════════════════════════════════════════════
# 4.  IN BÁO CÁO TỔNG HỢP
# ════════════════════════════════════════════════════════════════════════════
COLS = {
    "tc_id":     ("Testcase ID",       14),
    "ctrl":      ("Control",            7),
    "scenario":  ("Loại Kịch bản",     22),
    "expected":  ("Expected",          22),
    "ai_result": ("AI Kết quả",        22),
    "match":     ("✓?",                 4),
    "lat":       ("Giây",               5),
}

SEP = "+" + "+".join("-" * (w + 2) for _, w in COLS.values()) + "+"
HEADER_ROW = "|" + "|".join(f" {h:<{w}} " for (h, w) in COLS.values()) + "|"


def truncate(s: str, n: int) -> str:
    return s[:n] if len(s) <= n else s[:n - 1] + "…"


def print_row(r: dict):
    ok_icon = "✓" if r["match"] else "✗"
    cells = [
        truncate(r["testcase_id"], 14),
        truncate(r["control_id"], 7),
        truncate(r["scenario_type"], 22),
        truncate(r["expected_status"], 22),
        truncate(r["ai_status"], 22),
        ok_icon,
        str(r["latency_sec"]),
    ]
    widths = [w for _, w in COLS.values()]
    print("|" + "|".join(f" {c:<{w}} " for c, w in zip(cells, widths)) + "|")


def print_report(results: List[dict]):
    total = len(results)
    correct = sum(1 for r in results if r["match"])
    guardrail_hits = sum(1 for r in results if r["guardrail_triggered"])
    by_type = {"Compliant": 0, "Non-Compliant": 0, "Insufficient Evidence": 0}
    for r in results:
        if r["match"] and r["expected_status"] in by_type:
            by_type[r["expected_status"]] += 1

    print("\n" + "═" * 80)
    print("  WEEK 3 BENCHMARK — KẾT QUẢ ĐÁNH GIÁ LANGGRAPH AI AGENT")
    print("═" * 80)
    print(SEP)
    print(HEADER_ROW)
    print(SEP)

    prev_ctrl = None
    for r in results:
        if prev_ctrl and r["control_id"] != prev_ctrl:
            print(SEP)
        print_row(r)
        prev_ctrl = r["control_id"]
        if r["blocked_evidences"]:
            for b in r["blocked_evidences"]:
                print(f"|   ⚠ GUARDRAIL [{b['code']}]: {b['reason'][:70]}")

    print(SEP)

    # Summary
    accuracy = correct / total * 100 if total > 0 else 0
    print(f"\n{'━'*80}")
    print(f"  📊 TỔNG HỢP KẾT QUẢ")
    print(f"{'━'*80}")
    print(f"  Tổng số kịch bản chạy          : {total}")
    print(f"  ✅ AI chấm đúng (Match)         : {correct}/{total}  →  Độ chính xác = {accuracy:.1f}%")
    print(f"  🛡  Guardrail đã chặn bằng chứng: {guardrail_hits} kịch bản")
    print(f"")
    print(f"  Chi tiết theo loại kịch bản:")
    for stype in ["Compliant", "Non-Compliant", "Insufficient Evidence"]:
        expected_count = sum(1 for r in results if r["expected_status"] == stype)
        correct_count = by_type.get(stype, 0)
        icon = "✓" if correct_count == expected_count else "△"
        print(f"    {icon}  {stype:<25}: {correct_count}/{expected_count} đúng")
    print(f"{'━'*80}\n")

    # Các kịch bản AI sai
    wrong = [r for r in results if not r["match"]]
    if wrong:
        print(f"  ❌ AI CHẤM SAI — CẦN ĐIỀU CHỈNH ({len(wrong)} trường hợp):")
        for r in wrong:
            print(f"    • {r['testcase_id']} [{r['control_id']}] {r['scenario_type']}")
            print(f"      Expected: '{r['expected_status']}' | AI: '{r['ai_status']}'")
            print(f"      Lý giải AI: {r['ai_rationale'][:120]}")
            print()
    else:
        print("  🎉 AI chấm đúng 100% tất cả kịch bản Ground Truth!\n")


# ════════════════════════════════════════════════════════════════════════════
# 5.  MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    print("\n" + "═" * 80)
    print("  WEEK 3 BENCHMARK RUNNER — Tuần 3 ISO 27001 AI Agent")
    print(f"  Bắt đầu lúc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 80)

    # Đường dẫn file
    ground_truth_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "docs", "week3", "ground_truth_testcases.json"
    )
    if not os.path.exists(ground_truth_path):
        print(f"\n[ERROR] Không tìm thấy file: {ground_truth_path}")
        print("  Hãy kiểm tra lại thư mục docs/week3/")
        sys.exit(1)

    print(f"\n[1/3] Đang tải Ground Truth Dataset: {ground_truth_path}")
    testcases = load_ground_truth(ground_truth_path)
    print(f"      → Đã tải {len(testcases)} kịch bản kiểm thử.\n")

    print("[2/3] Đang khởi tạo LangGraph AI Agent...")
    try:
        graph = build_iso_agent_graph()
        print("      → Khởi tạo thành công!\n")
    except Exception as e:
        print(f"\n[ERROR] Không thể khởi tạo LangGraph: {e}")
        print("  Kiểm tra: Ollama có đang chạy không? (lệnh: ollama serve)")
        sys.exit(1)

    print("[3/3] Đang chạy 15 kịch bản qua AI Agent...")
    print("      (Mỗi kịch bản cần 5-30 giây tùy tốc độ Ollama)\n")

    results = []
    for i, tc in enumerate(testcases, 1):
        print(f"  [{i:02d}/{len(testcases)}] {tc['testcase_id']} | {tc['control_id']} | {tc['scenario_type']}")
        result = run_one_testcase(graph, tc)
        results.append(result)
        icon = "✓" if result["match"] else "✗"
        print(f"         {icon} Expected: {result['expected_status']:<22} | AI: {result['ai_status']:<22} | {result['latency_sec']}s")

    # In báo cáo tổng hợp
    print_report(results)

    # Lưu kết quả JSON
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "docs", "week3", "week3_benchmark_results.json"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "run_timestamp": datetime.now().isoformat(),
            "total_testcases": len(results),
            "accuracy_percent": round(sum(1 for r in results if r["match"]) / len(results) * 100, 2),
            "results": results,
        }, f, ensure_ascii=False, indent=2)
    print(f"  💾 Kết quả đã được lưu vào: {output_path}\n")


if __name__ == "__main__":
    main()

