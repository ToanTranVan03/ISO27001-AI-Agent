# Dọn project theo hướng đánh giá tuân thủ — 11/11/2026

Đã xóa **111 tệp cũ** không còn phục vụ luồng hiện hành, đồng thời tách phần nghiệp vụ dùng chung khỏi các demo bị gỡ. Không xóa dữ liệu database, bằng chứng/nhãn A.8, hồ sơ trong `data/`, `.env` hoặc nhật ký tuần 1–4.

## Phần đã gỡ

- Frontend văn phòng, nhân vật, bình luận, bộ điều phối mission/SOC và CSS/helper chỉ dùng cho chúng.
- Backend API và worker mô phỏng sự cố, nhận lệnh nhân viên, nhiệm vụ/định tuyến hoạt động và live monitor demo.
- Ba giao diện HTML cũ và JavaScript static đi kèm. Trang cũ chuyển về React; API demo không còn đăng ký.
- Engine/CLI nghiên cứu cũ, benchmark tuần đầu, khảo sát tổng hợp, risk/RAG demo không dùng trong pipeline hiện hành; bỏ import benchmark và seed mẫu khỏi startup database.
- Tài liệu video/3D, slide và kết quả khảo sát/biểu đồ cũ, hướng dẫn giai đoạn không còn khớp hệ thống, checklist nhiệm vụ cũ.
- Preview, ảnh kiểm tra văn phòng, công cụ/frame/cache phiên âm video cũ trong `work/` và các thư mục trống; không đụng tới video gốc ngoài project.
- Test chỉ kiểm tra tính năng đã gỡ; thay bằng test kho doanh nghiệp, A.6 đang dùng, API hiện hành và xác nhận route cũ không còn.
- Ba dịch vụ Docker demo IAM/gateway/log không được sử dụng trong compose; giữ PostgreSQL và lab A.8. Bỏ dependency Python psutil/pandas/matplotlib chỉ phục vụ benchmark/biểu đồ đã gỡ.

## Phần được giữ và tách lại

| Phần | Lý do |
|---|---|
| Phạm vi 56, graph, tiêu chí, tài liệu/parser, chấm mù và SoA | Luồng chính của đề tài |
| Bộ ca/nhãn/kết quả A.8 v1, raw v2, live và log lỗi | Có liên quan trực tiếp tới bằng chứng nghiên cứu; không xóa ca sai để làm đẹp số liệu |
| `backend/company_storage.py` + `lab_company/inventory_seed.json` | Khởi tạo danh bạ/tài sản độc lập với incident/office demo |
| `agent_core/people_assessment.py` | Kiểm tra A.6 đại diện trên hồ sơ nghiệp vụ |
| `agent_core/business_events.py` | Cập nhật hồ sơ đào tạo/NDA/nghỉ việc, không điều khiển nhân vật |
| Kho tiêu chí JSON và workbook rubric | Tài liệu nền thuộc phạm vi 56; workbook không phải dependency runtime |
| Nhật ký tuần và dữ liệu database lịch sử | Bảo toàn quá trình thực hiện, không viết lại lịch sử hoặc drop bảng |

`run_agent_cli.py` nay trỏ vào CLI A.8 hiện hành. README, hướng dẫn thao tác, phạm vi và tài liệu doanh nghiệp đã được cập nhật. Mã OFFICE-EMP trong database giữ để liên kết bằng chứng, không có nghĩa còn văn phòng tương tác.

## Kiểm chứng sau dọn

- 140 test Python, 5 test JavaScript hiện hành đạt; build đạt và lint không còn cảnh báo.
- Số test thấp hơn trước do đã xóa test của module bị gỡ, không phải bỏ qua test đang thất bại.
- Kiểm tra initializer mới trên PostgreSQL: hash snapshot trước/sau không đổi; vẫn 50 nhân viên, 202 tài khoản, 70 thiết bị. Không drop/xóa bảng hoặc lịch sử cũ.
- Bộ test kiểm tra initializer chỉ bổ sung và không khởi tạo lại incident/mission; route demo đã gỡ trả 404, trang cũ chuyển hướng 307.
- Kiểm tra API thật sau khởi động: progress, phạm vi 56, kho doanh nghiệp, công việc chung, catalog/summary A.8 trả 200; API demo trả 404, hash doanh nghiệp không đổi. CLI baseline mới xử lý 18 control không lỗi. Không còn import nội bộ hoặc liên kết tài liệu hiện hành bị gãy.
- Chưa thay thế kiểm thử bấm toàn bộ UI, thẩm định độc lập hay phê duyệt chuyên môn. Phạm vi vẫn 56; live mới có 5 probe đại diện.

Lịch sử Git lưu các tệp bị xóa. Liên kết/file được nhắc trong nhật ký tuần cũ phản ánh thời điểm đã làm, không phải danh mục mã hiện hành.

## Danh sách tệp đã xóa

- `HUONG_DAN_GIAI_DOAN_1.md`
- `HUONG_DAN_GIAI_DOAN_2.md`
- `agent_core/autonomous.py`
- `agent_core/benchmark_provenance.py`
- `agent_core/enterprise_eval_and_charts.py`
- `agent_core/iso_rag.py`
- `agent_core/live.py`
- `agent_core/research_benchmark.py`
- `agent_core/simulation.py`
- `agent_core/tool_excel_to_json.py`
- `agent_core/triad.py`
- `agent_core/unstructured_evidence.py`
- `backend/company_monitor.py`
- `backend/employee_commands.py`
- `backend/enterprise_missions.py`
- `backend/incident_api.py`
- `backend/incident_catalog.py`
- `backend/incident_simulation.py`
- `backend/mission_activity.py`
- `backend/mission_planner.py`
- `backend/mission_targets.py`
- `backend/office_logic.py`
- `backend/static/mission.js`
- `docs/BAO-VE-VA-KHAO-SAT.md`
- `docs/BINH_LUAN_DIEU_KHIEN.md`
- `docs/KET-QUA-KHAO-SAT-RQ3.md`
- `docs/KICH-BAN-BAO-VE-HOI-DONG.md`
- `docs/KIEM_CHUNG_DANH_GIA.md`
- `docs/KIEN_TRUC_AGENT_TU_VIDEO.md`
- `docs/MAU-KHAO-SAT.tsv`
- `docs/NGHIEN-CUU-VA-DANH-GIA.md`
- `docs/SLIDE-THUYET-TRINH.md`
- `docs/SOA-MO-PHONG.md`
- `docs/SPEC-people-simulation.md`
- `docs/THIET-KE-DO-AN.md`
- `docs/TRIAD-ARCHITECTURE.md`
- `docs/TRU_SO_DIEU_PHOI.md`
- `docs/VALIDATION.md`
- `docs/VAN_PHONG_AGENT_3D.md`
- `docs/benchmark-2026-11-06.json`
- `docs/benchmark-provenance-2026-11-06.json`
- `docs/charts/chart1_model_benchmark.png`
- `docs/charts/chart2_enterprise_profiles_score.png`
- `docs/charts/chart3_compliance_status_distribution.png`
- `docs/charts/chart4_automation_coverage_by_group.png`
- `docs/charts/enterprise_benchmark_detail.json`
- `docs/charts/enterprise_benchmark_summary.csv`
- `docs/charts/hivefive-3d.png`
- `docs/charts/hivefive-agent-result.jpg`
- `docs/charts/hivefive-case-verified.jpg`
- `docs/charts/hivefive-connection-restored.jpg`
- `docs/charts/hivefive-final-verified.jpg`
- `docs/charts/hivefive-live-3d.jpg`
- `docs/charts/hivefive-live-overview.jpg`
- `docs/charts/hivefive-office-guided.png`
- `docs/charts/hivefive-simulation.png`
- `docs/charts/hivefive-source-conflict.jpg`
- `docs/research-baseline-results.json`
- `docs/research-paired-v1-results.json`
- `docs/research-results.json`
- `docs/week3/ground_truth_testcases.json`
- `docs/week3/guardrail_rules.md`
- `docs/week3/iso27002_rag_knowledge.json`
- `docs/week3/week3_benchmark_results.json`
- `evidence_collectors/week1_collector_poc.py`
- `frontend-react/src/AgentOfficeConsole.jsx`
- `frontend-react/src/AgentOfficeScene.jsx`
- `frontend-react/src/App.css`
- `frontend-react/src/DepartmentHeadquarters.jsx`
- `frontend-react/src/EmployeeCommandConsole.jsx`
- `frontend-react/src/EnterpriseIncidentLab.jsx`
- `frontend-react/src/EnterpriseMissionControl.jsx`
- `frontend-react/src/MissionRoleInspector.jsx`
- `frontend-react/src/OfficeLiveScene.jsx`
- `frontend-react/src/OfficeRoster.jsx`
- `frontend-react/src/agentCommand.js`
- `frontend-react/src/auditPilot.js`
- `frontend-react/src/mission-workspace.css`
- `frontend-react/src/missionLink.js`
- `frontend-react/src/missionView.js`
- `frontend-react/src/office-live.css`
- `frontend-react/src/officeLive.js`
- `frontend/enterprise.html`
- `frontend/index.html`
- `frontend/workspace.html`
- `run_user_study.py`
- `tasks/plan.md`
- `tasks/todo.md`
- `tests/mission_link.test.mjs`
- `tests/mission_view.test.mjs`
- `tests/office_live.test.mjs`
- `tests/test_ai_extensions.py`
- `tests/test_api.py`
- `tests/test_autonomous.py`
- `tests/test_benchmark_provenance.py`
- `tests/test_employee_commands.py`
- `tests/test_enterprise_missions.py`
- `tests/test_evidence_context.py`
- `tests/test_live.py`
- `tests/test_mission_activity.py`
- `tests/test_mission_planner.py`
- `tests/test_mission_targets.py`
- `tests/test_office_batch.py`
- `tests/test_office_logic.py`
- `tests/test_office_preparation.py`
- `tests/test_research.py`
- `tests/test_simulation.py`
- `tests/test_triad.py`
- `vi_du_kho_bang_chung/manifest.json`
- `week1_benchmark.py`
- `week3_benchmark.py`
