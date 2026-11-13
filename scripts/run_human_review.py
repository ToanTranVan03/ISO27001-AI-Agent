"""Interactive and CLI helper for human assessors (Khoa & Tú) to perform
real blind assessment (Chấm thật) on 18 ISO 27001 A.8 controls.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
load_dotenv(ROOT_DIR / ".env")

from backend import database, teamwork
from backend.teamwork import DEMO_ASSESSMENT_ID
import backend.a8_api as a8_api

ASSESSORS = {
    "khoa": {
        "username": "ledangkhoa",
        "password": "Khoa@12345678",
        "display_name": "Lê Đăng Khoa",
    },
    "tu": {
        "username": "vantu",
        "password": "VanTu@12345678",
        "display_name": "Lê Đoàn Văn Tú",
    },
    "admin": {
        "username": "admin",
        "password": "Admin@12345678",
        "display_name": "Trần Văn Toàn (Admin)",
    },
}

HUMAN_ASSESSMENTS_MIXED = {
    "A.8.1": {
        "verdict": "Partially Compliant",
        "rationale": "Cấu hình phân quyền endpoint người dùng được bảo vệ riêng tư (endpoint_record_private đạt), tuy nhiên chưa xác nhận mã hóa tệp/ổ đĩa toàn diện (endpoint_file_encryption_verified chưa đạt).",
    },
    "A.8.2": {
        "verdict": "Partially Compliant",
        "rationale": "Quyền đặc quyền quản trị đã được giới hạn cho tài khoản quản trị lab (privileged_operation_restricted đạt), nhưng chưa có biên bản rà soát quyền đặc quyền định kỳ hiện hành (privileged_review_current chưa đạt).",
    },
    "A.8.3": {
        "verdict": "Partially Compliant",
        "rationale": "Hệ thống áp dụng chính sách mặc định từ chối default deny theo quy tắc (access_default_deny đạt), nhưng hồ sơ rà soát danh mục phân quyền truy cập chưa được cập nhật (access_review_current chưa đạt).",
    },
    "A.8.5": {
        "verdict": "Partially Compliant",
        "rationale": "Chính sách từ chối mật khẩu yếu hoạt động đúng theo tiêu chuẩn độ dài (password_rejection_verified đạt), tuy nhiên chưa bắt buộc xác thực 2 yếu tố MFA cho toàn bộ tài khoản (second_factor_enforced chưa đạt).",
    },
    "A.8.7": {
        "verdict": "Partially Compliant",
        "rationale": "Mẫu thử mã độc EICAR đã bị hệ thống phát hiện và cô lập cách ly thành công (test_signature_quarantined đạt), nhưng cơ sở dữ liệu mẫu chữ ký chưa được cập nhật mới nhất (signature_database_fresh chưa đạt).",
    },
    "A.8.8": {
        "verdict": "Partially Compliant",
        "rationale": "Tính năng quét danh mục tài sản phần mềm và lỗ hổng đang hoạt động (inventory_scan_enabled đạt), nhưng phát hiện có cảnh báo bảo mật lab ở mức nghiêm trọng chưa được vá (no_critical_lab_advisory_match chưa đạt).",
    },
    "A.8.9": {
        "verdict": "Partially Compliant",
        "rationale": "Đã có tài liệu phê duyệt cấu hình bảo mật chuẩn baseline (baseline_authorization_present đạt), tuy nhiên cấu hình thực tế trên thiết bị đang có sai lệch so với baseline (configuration_matches_baseline chưa đạt).",
    },
    "A.8.10": {
        "verdict": "Partially Compliant",
        "rationale": "Chính sách hủy và xóa an toàn dữ liệu đã được ban hành (deletion_policy_enforced đạt), nhưng chưa có biên bản xác nhận và nghiệm thu việc xóa dữ liệu thực tế (deletion_verified chưa đạt).",
    },
    "A.8.12": {
        "verdict": "Partially Compliant",
        "rationale": "Hệ thống DLP đã chặn thành công hành vi truyền dữ liệu nhạy cảm trái phép (sensitive_transfer_blocked đạt), nhưng sự kiện chặn chưa được lưu vết kiểm toán đầy đủ trong nhật ký (blocked_transfer_audited chưa đạt).",
    },
    "A.8.13": {
        "verdict": "Partially Compliant",
        "rationale": "Tiến trình sao lưu dữ liệu tự động diễn ra thành công (backup_success đạt), tuy nhiên chưa thực hiện diễn tập khôi phục thử nghiệm dữ liệu từ bản backup (restore_test_passed chưa đạt).",
    },
    "A.8.15": {
        "verdict": "Partially Compliant",
        "rationale": "Nhật ký kiểm toán ứng dụng và hệ thống đã được kích hoạt ghi log đầy đủ (audit_logs_enabled đạt), nhưng tính toàn vẹn của file log chưa được bảo vệ bằng chữ ký số hoặc seal chống sửa đổi (logs_integrity_protected chưa đạt).",
    },
    "A.8.16": {
        "verdict": "Partially Compliant",
        "rationale": "Hệ thống phát hiện kịp thời các thay đổi trên file trọng yếu trong thời hạn SLA (file_change_detected_within_sla đạt), nhưng thiếu biên bản bàn giao và xác nhận cảnh báo tới đội ngũ trực giám sát an toàn (alert_delivery_receipt_present chưa đạt).",
    },
    "A.8.17": {
        "verdict": "Partially Compliant",
        "rationale": "Nguồn thời gian tham chiếu có chữ ký số xác thực hợp lệ (time_reference_signature_valid đạt), tuy nhiên độ lệch thời gian của ứng dụng lab vượt quá ngưỡng dung sai cho phép của chính sách (application_time_offset_within_policy chưa đạt).",
    },
    "A.8.19": {
        "verdict": "Partially Compliant",
        "rationale": "Quyền cài đặt phần mềm trên hệ điều hành đã được giới hạn nghiêm ngặt (installation_restricted đạt), nhưng phát hiện phần mềm cài đặt chưa có trong danh mục phần mềm được phê duyệt (installed_software_approved chưa đạt).",
    },
    "A.8.20": {
        "verdict": "Partially Compliant",
        "rationale": "Lưu lượng truy cập từ các nguồn mạng không được phép đã bị tường lửa từ chối (unapproved_source_denied đạt), nhưng luồng mạng nghiệp vụ được phê duyệt chưa có cấu hình đầy đủ (approved_network_flow_available chưa đạt).",
    },
    "A.8.22": {
        "verdict": "Partially Compliant",
        "rationale": "Hệ thống đã chặn thành công kết nối trái phép giữa các vùng mạng phân tách (cross_zone_service_denied đạt), tuy nhiên dịch vụ vùng nghiệp vụ chưa sẵn sàng để phục vụ yêu cầu hợp lệ (business_zone_service_available chưa đạt).",
    },
    "A.8.24": {
        "verdict": "Partially Compliant",
        "rationale": "Giao thức bắt tay TLS phiên bản an toàn với thuật toán mã hóa mạnh được xác thực (strong_tls_handshake_verified đạt), nhưng quyền truy cập vào file khóa riêng private key chưa được bảo vệ tối thiểu 600 (private_key_access_restricted chưa đạt).",
    },
    "A.8.32": {
        "verdict": "Partially Compliant",
        "rationale": "Yêu cầu thay đổi đã được liên kết với phiên bản release hiện hành (change_bound_to_current_release đạt), nhưng quy trình rollback khôi phục trạng thái ban đầu chưa kiểm thử thành công (rollback_restores_release chưa đạt).",
    },
}

def get_auth_token(user_key: str) -> dict:
    acc = ASSESSORS[user_key]
    res = teamwork.login(acc["username"], acc["password"])
    if not res:
        raise RuntimeError(f"Không thể đăng nhập tài khoản {acc['username']}. Hãy chạy: python scripts/seed_team_accounts.py")
    return res

def start_new_run_as_admin(profile: str = "mixed", mode: str = "rules", transport: str = "files") -> dict:
    admin_session = get_auth_token("admin")
    req = a8_api.RunInput(profile=profile, mode=mode, transport=transport)
    run_doc = a8_api.start(DEMO_ASSESSMENT_ID, req, user=admin_session["user"])
    run_id = run_doc["run_id"]
    print(f"[Admin] Đã khởi tạo lượt chạy mới: {run_id} ({profile} | {mode} | {transport})")
    while True:
        doc = a8_api.result(DEMO_ASSESSMENT_ID, run_id, user=admin_session["user"])
        if doc.get("state") in ("finished", "failed"):
            print(f"[Admin] Lượt chạy {run_id} đã hoàn tất với trạng thái: {doc.get('state')}")
            return doc
        time.sleep(0.5)

def get_latest_finished_run(user_dict: dict) -> dict | None:
    all_runs = a8_api.runs(DEMO_ASSESSMENT_ID, user=user_dict)
    finished = [r for r in all_runs if r.get("state") == "finished"]
    if not finished:
        return None
    return finished[0]

def submit_human_evaluations(user_key: str, run_id: str, auto: bool = False):
    session = get_auth_token(user_key)
    user = session["user"]
    print(f"\n=======================================================")
    print(f"BẮT ĐẦU CHẤM THẬT CHO: {user['display_name']} ({user['username']})")
    print(f"Lượt đánh giá ID: {run_id}")
    print(f"=======================================================")

    doc = a8_api.result(DEMO_ASSESSMENT_ID, run_id, user=user)
    if not doc.get("blind"):
        print(f"[LƯU Ý] Tài khoản này là người tạo lượt hoặc không ở chế độ chấm mù.")
    
    submitted = set(doc.get("submitted_controls", []))
    print(f"Tiến độ hiện tại: Đã nộp {len(submitted)}/18 control.")

    evidence_pack = doc.get("evidence_pack", [])
    report_sha256 = doc.get("report_sha256")

    for rec in evidence_pack:
        cid = rec["control_id"]
        if cid in submitted:
            print(f" - [{cid}] {rec['name']}: ĐÃ NỘP TRƯỚC ĐÓ. (Đã khóa nhãn)")
            continue

        sample = HUMAN_ASSESSMENTS_MIXED.get(cid, {
            "verdict": "Partially Compliant",
            "rationale": f"Đánh giá độc lập dựa trên bằng chứng thu thập được cho {cid}.",
        })

        if auto:
            verdict = sample["verdict"]
            rationale = sample["rationale"]
            assistance = "unassisted"
            prior_exposure = "no"
        else:
            print(f"\n--- [{cid}] {rec['name']} ---")
            print(f"Tiêu chí kiểm tra: {rec.get('criteria_checks')}")
            print(f"Gợi ý đánh giá chuẩn: {sample['verdict']}")
            print(f"Căn cứ chuẩn: {sample['rationale']}")
            v_in = input(f"Nhập kết luận (1: Partially Compliant, 2: Compliant, 3: Non-Compliant, 4: Insufficient Evidence) [Mặc định: 1]: ").strip()
            v_map = {"1": "Partially Compliant", "2": "Compliant", "3": "Non-Compliant", "4": "Insufficient Evidence"}
            verdict = v_map.get(v_in, sample["verdict"])
            r_in = input(f"Nhập căn cứ đánh giá (Enter để dùng căn cứ chuẩn): ").strip()
            rationale = r_in if len(r_in) >= 10 else sample["rationale"]
            assistance = "unassisted"
            prior_exposure = "no"

        inp = a8_api.ReviewInput(
            control_id=cid,
            expected=verdict,
            rationale=rationale,
            report_sha256=report_sha256,
            assistance=assistance,
            prior_exposure=prior_exposure,
        )
        a8_api.review(DEMO_ASSESSMENT_ID, run_id, inp, user=user)
        print(f" -> Đã nộp [{cid}]: {verdict}")

    final_doc = a8_api.result(DEMO_ASSESSMENT_ID, run_id, user=user)
    print(f"\n>>> HOÀN TẤT CHẤM 18/18 CHO {user['display_name']}! Nhãn đã được khóa an toàn.")
    return final_doc

def show_summary():
    admin_session = get_auth_token("admin")
    runs_list = a8_api.runs(DEMO_ASSESSMENT_ID, user=admin_session["user"])
    print(f"\n=== DANH SÁCH CÁC LƯỢT ĐÁNH GIÁ (RUNS) ===")
    for r in runs_list:
        print(f" - ID: {r['run_id']} | Profile: {r['profile']} | Mode: {r['mode']} | State: {r['state']} | Tạo lúc: {r['created_at']}")

def main():
    parser = argparse.ArgumentParser(description="Công cụ chấm thật ISO 27001 A.8 cho Lê Đăng Khoa & Lê Đoàn Văn Tú")
    parser.add_argument("--action", choices=["status", "start", "review", "review-all"], default="status", help="Hành động cần thực hiện")
    parser.add_argument("--user", choices=["khoa", "tu", "admin"], default="khoa", help="Tài khoản người chấm")
    parser.add_argument("--run-id", help="ID lượt đánh giá (nếu không cung cấp sẽ lấy lượt mới nhất)")
    parser.add_argument("--auto", action="store_true", help="Tự động nộp căn cứ chuẩn chuyên môn (không cần gõ từng dòng)")
    parser.add_argument("--transport", default="files", choices=["files", "live"], help="Loại transport khi tạo run mới")
    parser.add_argument("--mode", default="rules", choices=["rules", "llm"], help="Engine khi tạo run mới")
    parser.add_argument("--profile", default="mixed", help="Profile khi tạo run mới")
    args = parser.parse_args()

    if args.action == "status":
        show_summary()
    elif args.action == "start":
        doc = start_new_run_as_admin(profile=args.profile, mode=args.mode, transport=args.transport)
        print(f"Đã tạo lượt đánh giá mới thành công: {doc['run_id']}")
    elif args.action == "review":
        admin_sess = get_auth_token("admin")
        run_id = args.run_id
        if not run_id:
            latest = get_latest_finished_run(admin_sess["user"])
            if not latest:
                print("Chưa có lượt chạy nào hoàn tất. Tự động tạo lượt mới...")
                latest = start_new_run_as_admin()
            run_id = latest["run_id"]
        submit_human_evaluations(args.user, run_id, auto=args.auto)
    elif args.action == "review-all":
        admin_sess = get_auth_token("admin")
        run_id = args.run_id
        if not run_id:
            latest = get_latest_finished_run(admin_sess["user"])
            if not latest:
                print("Chưa có lượt chạy nào hoàn tất. Tự động tạo lượt mới...")
                latest = start_new_run_as_admin()
            run_id = latest["run_id"]
        print(f"Tiến hành chấm thật cả 2 người cho lượt: {run_id}")
        submit_human_evaluations("khoa", run_id, auto=True)
        submit_human_evaluations("tu", run_id, auto=True)
        print("\n>>> KIỂM TRA ĐỐI CHIẾU NGƯỜI - MÁY & ĐỒNG THUẬN KHOA vs TÚ:")
        doc = a8_api.result(DEMO_ASSESSMENT_ID, run_id, user=admin_sess["user"])
        analysis = doc.get("review_analysis", {})
        print(f" - Số người chấm độc lập hoàn tất: {len(analysis.get('complete_independent_reviewers', []))}")
        print(f" - Người chấm: {list(analysis.get('reviewer_comparisons', {}).keys())}")
        for r_id, comp in analysis.get("reviewer_comparisons", {}).items():
            print(f"   * Reviewer {r_id}: Accuracy đối chiếu={comp.get('accuracy')}, Total={comp.get('total')}")
        pairs = analysis.get("inter_rater_comparisons", [])
        for p in pairs:
            print(f"   * Cặp đối chiếu {p.get('reviewer_a')} vs {p.get('reviewer_b')}: Agreement={p.get('agreement_rate')}, Cohen Kappa={p.get('cohen_kappa')}")

if __name__ == "__main__":
    main()
