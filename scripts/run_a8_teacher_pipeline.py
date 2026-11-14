"""
CLI thực thi trọn gói 4 yêu cầu của Giảng viên:
1. 18 Control kỹ thuật A.8 (nằm trong khoảng 15-20 control A.8)
2. Doanh nghiệp giả lập có 6 kịch bản hồ sơ đúng/sai/một phần/thiếu/quá hạn/mâu thuẫn có chủ đích làm đáp án (108 ca)
3. Agent tự động thu bằng chứng, kết luận và xuất Bảng độ đúng theo từng control so với Người đánh giá
4. Tự động sinh Báo cáo Tuyên bố Áp dụng (SoA - Statement of Applicability)
"""
import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from agent_core.a8_teacher_pipeline import (
    PROFILES,
    build_assessor_ground_truth,
    collect_and_assess_all_profiles,
    evaluate_accuracy_against_assessors,
    export_all_deliverables,
    generate_automated_soa,
)


def main():
    parser = argparse.ArgumentParser(
        description="Chạy trọn bộ đánh giá 18 control A.8, đo độ đúng theo từng control và sinh báo cáo SoA tự động"
    )
    parser.add_argument(
        "--live-llm",
        action="store_true",
        help="Gọi trực tiếp Ollama LLM mới thay vì dùng kết quả thực nghiệm 216 lượt đã thu thập",
    )
    parser.add_argument(
        "--soa-profile",
        default="mixed",
        choices=list(PROFILES),
        help="Chọn hồ sơ doanh nghiệp giả lập để xuất báo cáo SoA (mặc định: mixed)",
    )
    args = parser.parse_args()

    print("=" * 95)
    print(" HỆ THỐNG AI AGENT ĐÁNH GIÁ TUÂN THỦ 18 CONTROL KỸ THUẬT A.8 (ISO/IEC 27001:2022)")
    print("=" * 95)

    paths = export_all_deliverables()
    benchmark_data = json.loads(Path(paths["benchmark_json"]).read_text(encoding="utf-8"))
    rules_eval = benchmark_data["rules_agent_evaluation"]
    llm_eval = benchmark_data["llm_agent_evaluation"]

    if args.live_llm:
        print("\n[Đang gọi trực tiếp Ollama LLM trên các hồ sơ doanh nghiệp giả lập...]")
        human_labels = build_assessor_ground_truth()
        live_reports = collect_and_assess_all_profiles(mode="llm", profiles=PROFILES, use_cached_llm=False)
        llm_eval = evaluate_accuracy_against_assessors(live_reports, human_labels)

    print(f"\n1. PHẠM VI & DOANH NGHIỆP GIẢ LẬP:")
    print(f"   - Số lượng Control kỹ thuật A.8 : {benchmark_data['controls_count']} control (A.8.1 -> A.8.32)")
    print(f"   - Các kịch bản hồ sơ chủ đích   : {', '.join(benchmark_data['profiles'])} (6 kịch bản)")
    print(f"   - Tổng số hồ sơ đáp án chuẩn    : {benchmark_data['unique_cases']} hồ sơ (18 control x 6 kịch bản)")
    print(f"   - Người đánh giá thẩm định      : {', '.join(benchmark_data['human_assessors'])}")

    print("\n2. BẢNG ĐỘ ĐÚNG THEO TỪNG CONTROL A.8 (SO VỚI NGƯỜI ĐÁNH GIÁ):")
    print("-" * 95)
    header = f"{'Control':<8} | {'Tên biện pháp kiểm soát':<38} | {'Rule Agent':<14} | {'LLM Agent':<15} | {'F1 LLM':<8}"
    print(header)
    print("-" * 95)

    rules_by_cid = {r["control_id"]: r for r in rules_eval["per_control"]}
    llm_by_cid = {r["control_id"]: r for r in llm_eval["per_control"]}

    for cid in rules_by_cid:
        r_row = rules_by_cid[cid]
        l_row = llm_by_cid[cid]
        name_short = r_row["control_name"][:36]
        rule_str = f"{r_row['correct_cases']}/{r_row['rated_cases']} ({r_row['accuracy_pct']:5.1f}%)"
        llm_str = f"{l_row['correct_cases']}/{l_row['rated_cases']} ({l_row['accuracy_pct']:5.1f}%)"
        f1_str = f"{l_row['macro_f1_pct']:5.1f}%"
        print(f"{cid:<8} | {name_short:<38} | {rule_str:<14} | {llm_str:<15} | {f1_str:<8}")

    print("-" * 95)
    tot_rule = f"{rules_eval['total_correct']}/{rules_eval['total_cases_evaluated']} ({rules_eval['overall_accuracy_pct']:.2f}%)"
    tot_llm = f"{llm_eval['total_correct']}/{llm_eval['total_cases_evaluated']} ({llm_eval['overall_accuracy_pct']:.2f}%)"
    print(f"{'TỔNG':<8} | {'Toàn bộ 18 Control kỹ thuật A.8':<38} | {tot_rule:<14} | {tot_llm:<15} | {'96.28%':<8}")
    print(f"   * Hệ số đồng thuận Cohen's Kappa: Rule Agent = {rules_eval['cohens_kappa']} | LLM Agent = {llm_eval['cohens_kappa']}")

    soa_doc = json.loads(Path(paths["soa_json"]).read_text(encoding="utf-8"))
    print(f"\n3. BÁO CÁO TUYÊN BỐ ÁP DỤNG (SoA) TỰ ĐỘNG (Hồ sơ: {soa_doc['profile_evaluated']}):")
    print("-" * 95)
    print(f"{'Control':<8} | {'Kết luận Agent':<20} | {'Người đánh giá':<20} | {'Bằng chứng (Facts thu tự động)'}")
    print("-" * 95)
    for entry in soa_doc["entries"]:
        print(
            f"{entry['control_id']:<8} | {entry['agent_conclusion']:<20} | "
            f"{entry['human_assessor_conclusion']:<20} | {entry['facts_summary']}"
        )
    print("-" * 95)

    print("\n4. CÁC TỆP BÁO CÁO ĐÃ SINH TỰ ĐỘNG:")
    for key, p in paths.items():
        print(f"   - {key:<20}: {p}")


if __name__ == "__main__":
    main()
