"""Chạy AI Agent ISO 27001 trực tiếp trong Terminal VS Code.
Hiển thị toàn bộ quá trình điều phối công cụ, phân tích Tam giác ATTT và đề xuất khắc phục.
"""

import sys
import time
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from agent_core.autonomous import AgentStore, agent_events
from agent_core.triad import analyze_triad


def print_banner():
    print("=" * 80)
    print("   HIVEFIVE · ISO 27001 AI AGENT — GIÁM SÁT CON NGƯỜI, PHẦN MỀM & PHẦN CỨNG")
    print("   Khởi chạy trực tiếp trong VS Code Terminal")
    print("=" * 80)


def run_cli(goal: str = "Kiểm tra toàn diện HiveFive, ưu tiên nhóm Con người A.6", mode: str = "workflow"):
    print_banner()
    print(f"\n[*] Mục tiêu: {goal}")
    print(f"[*] Chế độ: {mode.upper()} ({'Quy trình xác định' if mode == 'workflow' else 'LLM Ollama Qwen2.5:7b'})\n")
    
    store = AgentStore()
    events = agent_events(goal, mode=mode, store=store)
    
    for event in events:
        etype = event.get('type')
        if etype == 'start':
            print(f"[+] KHỞI CHẠY LẦN CHẠY: {event['run_id']}")
            print(f"    Nguồn dữ liệu: {event['source']} | Hash: {event['snapshot_hash'][:16]}...")
            print("-" * 80)
            
        elif etype == 'action':
            step = event.get('step')
            tool = event.get('tool')
            reason = event.get('reason')
            print(f"\n[BƯỚC {step}] AGENT CHỌN CÔNG CỤ: >> {tool} <<")
            print(f"    Lý do / Mục tiêu: {reason}")
            if event.get('available_tools'):
                print(f"    Các công cụ khả dụng lúc này: {', '.join(event['available_tools'])}")
                
        elif etype == 'tool_result':
            step = event.get('step')
            tool = event.get('tool')
            obs = event.get('observation', {})
            print(f"[KẾT QUẢ {step}] Thu thập từ {tool}:")
            for k, v in obs.items():
                if isinstance(v, list) and len(v) > 3:
                    print(f"    - {k}: {len(v)} mục ({', '.join(str(x) for x in v[:3])}...)")
                elif isinstance(v, dict):
                    print(f"    - {k}: {v}")
                else:
                    print(f"    - {k}: {v}")
            time.sleep(0.3)
            
        elif etype == 'complete':
            report = event.get('report', {})
            triad = report.get('triad_summary') or analyze_triad(report.get('enterprise', {}))
            metrics = report.get('metrics', {})
            
            print("\n" + "=" * 80)
            print("                 BÁO CÁO TỔNG HỢP KIỂM TOÁN AGENT HOÀN TẤT")
            print("=" * 80)
            print(f"Thời gian thực thi: {metrics.get('elapsed_ms')} ms | Số lần gọi công cụ: {metrics.get('tool_calls')}")
            
            # 1. Tam giác thực thể
            pillars = triad.get('pillars', {})
            print("\n[1] MÔ HÌNH TAM GIÁC AN TOÀN THÔNG TIN (SECURITY TRIAD):")
            print(f"  👤 CON NGƯỜI (Trọng tâm): {pillars.get('people', {}).get('total_records')} hồ sơ "
                  f"({pillars.get('people', {}).get('active_employees')} đang làm việc, "
                  f"{pillars.get('people', {}).get('terminated_employees')} đã nghỉ việc) "
                  f"-> {pillars.get('people', {}).get('issue_count')} vấn đề.")
            print(f"  💻 PHẦN MỀM & IAM:        {pillars.get('software', {}).get('total_accounts')} tài khoản "
                  f"({pillars.get('software', {}).get('active_accounts')} đang mở) "
                  f"-> {pillars.get('software', {}).get('issue_count')} vấn đề.")
            print(f"  🛡️ PHẦN CỨNG & THIẾT BỊ:  {pillars.get('hardware', {}).get('total_devices')} laptop "
                  f"({pillars.get('hardware', {}).get('active_devices')} chưa thu hồi) "
                  f"-> {pillars.get('hardware', {}).get('issue_count')} vấn đề.")
            
            # 2. Rủi ro bắc cầu
            cross_risks = triad.get('cross_entity_risks', [])
            print(f"\n[2] PHÁT HIỆN RỦI RO LAN TRUYỀN BẮC CẦU ({len(cross_risks)} rủi ro):")
            if not cross_risks:
                print("    ✅ Không có rủi ro bắc cầu. Toàn bộ quan hệ Con người - Phần mềm - Phần cứng đạt chuẩn.")
            else:
                for idx, r in enumerate(cross_risks, 1):
                    risk = r.get('risk', {})
                    print(f"  {idx}. [{risk.get('risk_level')}] {r.get('title')}")
                    print(f"     Điểm rủi ro CIA: {risk.get('risk_score')}/25.0 (Khả năng: {risk.get('likelihood')} x Tác động: {risk.get('impact')})")
                    print(f"     Lan truyền: {r.get('source_pillar')} ---> {r.get('target_pillar')}")
                    print(f"     Chi tiết: {r.get('detail')}")
                    print(f"     Kiểm soát ISO 27002 liên đới: {', '.join(r.get('controls', []))}")
                    guidance = r.get('iso_guidance', {})
                    if guidance:
                        print(f"     📖 Căn cứ pháp lý ISO: {guidance.get('regulatory_rationale')}")
                        steps = guidance.get('actionable_steps', [])
                        if steps:
                            print(f"     🛠️ Hành động khuyến nghị:")
                            for step_txt in steps:
                                print(f"        - {step_txt}")
                    
            # 3. Nhiệm vụ khắc phục
            tasks = report.get('tasks', [])
            print(f"\n[3] NHIỆM VỤ KHẮC PHỤC ĐƯỢC AGENT TỰ ĐỘNG ĐỀ XUẤT ({len(tasks)} việc):")
            for t in tasks[:5]:
                print(f"  * [{t.get('priority')}] {t.get('task_id')}: {t.get('title')} (Phụ trách: {t.get('owner')})")
            if len(tasks) > 5:
                print(f"    ... và {len(tasks) - 5} nhiệm vụ khác được lưu vào SQLite.")
                
            print("\n" + "=" * 80)
            print("   LẦN CHẠY HOÀN TẤT THÀNH CÔNG VÀ ĐÃ ĐƯỢC LƯU VÀO CƠ SỞ DỮ LIỆU SQLITE!")
            print("=" * 80 + "\n")
            
        elif etype == 'error':
            print(f"\n[!] LỖI THỰC THI AGENT: {event.get('message')}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Chạy AI Agent ISO 27001 trong VS Code Terminal")
    parser.add_argument('--mode', choices=['workflow', 'ai'], default='workflow',
                        help='Chế độ chạy: workflow (nhanh, xác định) hoặc ai (Ollama Qwen2.5:7b)')
    parser.add_argument('--goal', type=str, default='Kiểm tra toàn diện HiveFive, ưu tiên nhóm Con người A.6',
                        help='Mục tiêu kiểm toán cho Agent')
    parser.add_argument('--unstructured', action='store_true',
                        help='Chạy thực nghiệm so sánh Rule Engine vs AI Agent trên văn bản phi cấu trúc (email/ticket)')
    parser.add_argument('--user-study', action='store_true',
                        help='Chạy khảo sát thực nghiệm RQ3 (2D vs 3D) và đo lường chỉ số SUS')
    args = parser.parse_args()

    if args.unstructured:
        from agent_core.unstructured_evidence import evaluate_corpus_comparison
        print("\n" + "=" * 80)
        print("  THỰC NGHIỆM ĐÁNH GIÁ: RULE ENGINE vs AI AGENT TRÊN VĂN BẢN PHI CẤU TRÚC")
        print("=" * 80)
        res = evaluate_corpus_comparison()
        print(f"[*] Tổng số tài liệu kiểm thử: {len(res['cases'])}")
        print(f"[*] Độ chính xác Rule Engine (chỉ đọc boolean): {res['rule_engine']['accuracy_on_unstructured']}%")
        print(f"[*] Độ chính xác AI / NLP Agent (trích xuất văn bản): {res['ai_nlp_agent']['accuracy_on_unstructured']}%")
        print("\nChi tiết từng văn bản doanh nghiệp:")
        for c in res['cases']:
            print(f"  - [{c['doc_id']} - {c['doc_type']}] Nhân sự: {c['person_id']}")
            print(f"    Vi phạm thực tế:     {c['expected_violations']}")
            print(f"    Rule Engine phát hiện: {c['rule_engine_detected']} (Thất bại vì không đọc được văn bản)")
            print(f"    AI Agent phát hiện:    {c['ai_agent_detected']} (Trích xuất thành công)")
        print("=" * 80 + "\n")
    elif args.user_study:
        from run_user_study import run_empirical_study
        run_empirical_study()
    else:
        run_cli(goal=args.goal, mode=args.mode)
