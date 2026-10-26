# ISO 27001 AI Agent

## Current deployment status

This repository is a local development/demo application, not a production enterprise deployment. The API and Ollama model run on the developer machine. Docker Compose can run a PostgreSQL database and simulated enterprise hosts, but it does not provide production identity management, TLS, secrets management, backups, monitoring, or high availability.

## Run locally on Windows

1. Install Python 3.11+, Docker Desktop with Compose, and Ollama. Pull the model with `ollama run qwen2.5:7b`.
2. Create a local environment file and change its sample password:

   ```powershell
   Copy-Item .env.example .env
   ```

   Keep the password in `POSTGRES_PASSWORD` and the password embedded in `DATABASE_URL` identical. Use a URL-safe password.

3. Install Python dependencies and start PostgreSQL:

   ```powershell
   pip install -r requirements.txt
   docker compose -f docker-compose.enterprise-lab.yml up -d postgres
   ```

4. Start the API:

   ```powershell
   uvicorn backend.main:app --reload --env-file .env
   ```

   On first startup the API creates its PostgreSQL tables, loads the selected 56 ISO controls from `docs/56_controls_scope.json`, and seeds the fictional enterprise directory, assets, and incident scenarios. Open `http://127.0.0.1:8000/` for the web interface or `http://127.0.0.1:8000/docs` for Swagger.

The web interface uploads PDF/DOCX files to `/api/evidence`; extracted text, source metadata, and SHA-256 hashes are stored in PostgreSQL. `/api/evaluate` runs LangGraph, whose `COLLECT` node retrieves evidence from PostgreSQL. Each evaluation is also persisted in PostgreSQL. Adding real evidence for a demo control replaces its seeded sample evidence for subsequent evaluations.

The other simulated enterprise hosts are optional and can be started with the same Compose file. Do not use this lab Compose configuration as a production deployment.

## Incident response simulation for the selected 56 controls

The current project scope is the 56 selected ISO controls covering people, hardware/physical security, and software/technology. The incident lab presents exactly three areas: **Con người / Phần cứng / Phần mềm**, with **Con người as the primary project focus**. Every scenario carries a synthetic employee context (affected employee or departmental owner); the Agent checks that employee profile and department alongside related devices/applications before planning an action. The 8 controls in the selected A.6 group are people-focused cases; A.7 and A.8 scenarios provide the related physical and software context. The fictional directory and all identities are synthetic, not real employee records. These are not all Annex A controls and are not a claim of ISO certification.

After login, open **Mô phỏng 3D** and describe an incident in natural language; users do not select an ISO control. For example: `Tôi bị mất laptop lúc 11h; hãy kiểm tra sau thời điểm đó máy còn hoạt động không.` The Agent classifies the description against the 56-control scope, checks the linked synthetic employee and asset, compares endpoint activity after the reported time, presents its selected control and conclusion, then chooses only registered response actions. If the description is ambiguous, it asks for clarification. After the saved report, users can ask follow-up questions grounded in that report and its telemetry. The Three.js logistics campus can be rotated and zoomed; the Agent moves between the three areas and streams intake, inspection, analysis, tool calls, verification, and evidence storage. The API stores before/after states, rationale, and a SHA-256 referenced incident record as synthetic evidence. All activity logs are fabricated lab data; they demonstrate the workflow and do not represent telemetry from a real company endpoint.

To demonstrate employee behavior, use **Nhân viên cắm USB lạ** or **Nhân viên cài app lạ** to write a fixed synthetic endpoint event. **Diễn tập kế tiếp** automatically generates the least-tested of the 56 control scenarios; the control is revealed only after Agent triage. The coverage counter shows progress without a control picker. **Bật giám sát tự động** polls the synthetic feed every five seconds; **Quét ngay** is available for an immediate one-off scan. New findings are mapped to their control and processed through the bounded lab response. Findings already triaged are not duplicated. The automatic monitor runs only while this local API process is running, and its on/off state is in memory. This is generated lab telemetry, not live endpoint monitoring.

Useful endpoints, all requiring an authenticated assessment member:

- `GET /api/assessments/{assessment_id}/enterprise/scenarios` — 56 scenarios and simulated target state.
- `GET /api/assessments/{assessment_id}/enterprise/people` — synthetic employee directory and linked device/application relationships.
- `GET /api/assessments/{assessment_id}/enterprise/metrics` — scenario coverage, verification outcomes, fallback counts, and domain-level experiment metrics.
- `GET /api/assessments/{assessment_id}/enterprise/system-readiness` — authenticated database/inventory, 56-scenario catalog, and Ollama/model readiness; reports when the fixed fallback is active.
- `POST /api/assessments/{assessment_id}/enterprise/controls/{control_id}/simulate` — run one incident and its bounded lab actions.
- `POST /api/assessments/{assessment_id}/enterprise/controls/{control_id}/simulate/stream` — stream the actual inspection and response steps to the 3D interface.
- `POST /api/assessments/{assessment_id}/enterprise/issues/simulate/stream` — classify and simulate a free-text incident without exposing control selection in the UI.
- `POST /api/assessments/{assessment_id}/enterprise/monitor/scan/stream` — proactively scan recent synthetic endpoint events and respond to findings.
- `POST /api/assessments/{assessment_id}/enterprise/monitor/auto/start`, `POST .../stop`, `GET .../status` — control and inspect the local five-second synthetic telemetry monitor.
- `POST /api/assessments/{assessment_id}/enterprise/monitor/simulate-activity` — generate one fixed employee USB/software activity event for the lab.
- `POST /api/assessments/{assessment_id}/enterprise/monitor/drill/next` — generate the least-tested scenario in the 56-control scope without a control picker.
- `POST /api/assessments/{assessment_id}/enterprise/incidents/{incident_id}/chat/stream` — ask follow-up questions about a saved synthetic incident.
- `GET /api/assessments/{assessment_id}/enterprise/incidents` — review saved incident/action history.

The action tools only update PostgreSQL lab fixtures. For A.6 scenarios they update the fictional employee account, onboarding, training, access, or session state as applicable; the incident history records before/after employee and target states. They do not lock a real laptop/account, change firewall rules, run shell commands, erase files, or contact an external service. When Ollama is unavailable, the API records that it used the fixed policy fallback instead of hiding the fallback.

The **Ma trận độ bao phủ** displays each control as read-only progress (not a control picker). It can export a UTF-8 CSV with all 56 scenario statuses, run counts, verification counts, and latest-run times for use in Excel and project reporting.

## Shared multi-user Enterprise Lab (Giai đoạn 1)

**Mới:** xem tài liệu [HUONG_DAN_GIAI_DOAN_1.md](HUONG_DAN_GIAI_DOAN_1.md) để cài và chạy phiên đánh giá chung với tài khoản riêng, job lock PostgreSQL và bảng tiến độ theo thời gian gần thực.

Giao diện mới chạy tại `/`. Giao diện tuần 2 còn giữ tại `/legacy` (API legacy dùng dữ liệu không theo phiên đánh giá; **không dùng để thống kê tiến độ chung**). Chạy từ thư mục repo với:

```powershell
uvicorn backend.main:app --env-file .env --host 127.0.0.1 --port 8000
```

**Không khai báo số liệu mô phỏng thành benchmark thực nghiệm**; các chart và CSV cũ chỉ để tham khảo cho đến khi chạy lại bằng ground truth độc lập.
