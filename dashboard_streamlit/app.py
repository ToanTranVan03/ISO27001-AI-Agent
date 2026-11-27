"""Streamlit Dashboard for the People-Centric ISO/IEC 27001:2022 Multi-Agent System.

Supports TWO backend modes selectable in the Sidebar:
1. FastAPI REST API (/api/pc/*): Connects over HTTP with Bearer token to FastAPI + PostgreSQL (pc_* tables).
2. Standalone In-Memory: Runs PCService in-process for instant zero-dependency local demos & AppTest CI.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import requests
import streamlit as st

from backend.pc_service import ConflictError, PCService
from backend.pc_storage import CLOSED_LOOP_STAGES, COMPLIANCE_STATES, InMemoryPCStore
from dashboard_streamlit.api_client import FastAPIPCClient

STATUS_ICON = {
    "Compliant": "🟢",
    "Non-compliant": "🔴",
    "Partial": "🟠",
    "Insufficient Evidence": "⚪",
    "Not Applicable": "⚫",
    "Pending Remediation": "🟡",
}
RISK_ICON = {"LOW": "🟢 LOW", "MEDIUM": "🟠 MEDIUM", "HIGH": "🔴 HIGH"}

st.set_page_config(page_title="ISO 27001 People-Centric Agent", page_icon="🛡️", layout="wide")


@st.cache_resource
def get_local_service() -> PCService:
    svc = PCService(InMemoryPCStore())
    svc.generate(count=25, seed=2026, include_canonical=True)
    return svc


def _guard(fn, *args, **kwargs):
    """Run a service/API call and surface errors in the UI instead of crashing the page."""
    try:
        return fn(*args, **kwargs)
    except ConflictError as exc:
        st.warning(f"Xung đột trạng thái: {exc}")
    except (KeyError, ValueError, PermissionError, RuntimeError, requests.RequestException) as exc:
        st.error(f"{type(exc).__name__}: {exc}")
    return None


# ------------------------------------------------------------------ sidebar connection & controls
default_api_url = os.getenv("PC_API_URL", "").strip()
with st.sidebar:
    st.title("🛡️ ISO 27001 Agent")
    backend_choice = st.selectbox(
        "Nguồn kết nối dữ liệu",
        ["Standalone In-Memory", "FastAPI REST API (/api/pc/*)"],
        index=1 if default_api_url else 0,
    )

    if backend_choice == "FastAPI REST API (/api/pc/*)":
        api_url = st.text_input("FastAPI URL", value=default_api_url or "http://127.0.0.1:8000")
        with st.expander("🔑 Đăng nhập lấy Bearer Token", expanded=not bool(st.session_state.get("pc_api_token"))):
            u_in = st.text_input("Username", value="admin")
            p_in = st.text_input("Password", type="password")
            if st.button("Đăng nhập FastAPI"):
                try:
                    r = requests.post(f"{api_url.rstrip('/')}/api/auth/login", json={"username": u_in, "password": p_in}, timeout=10)
                    r.raise_for_status()
                    st.session_state["pc_api_token"] = r.json()["token"]
                    st.success("Đăng nhập thành công!")
                except Exception as exc:
                    st.error(f"Lỗi đăng nhập: {exc}")
        token = st.text_input("Bearer Token", value=st.session_state.get("pc_api_token", os.getenv("PC_API_TOKEN", "")), type="password")
        service: Any = FastAPIPCClient(api_url, token)
        if st.button("🏭 Sinh 25 Doanh nghiệp mẫu (API)"):
            if _guard(service.generate, 25, 2026, True):
                st.toast("Đã khởi tạo 25 doanh nghiệp trên FastAPI/PostgreSQL!")
    else:
        service = get_local_service()

companies = _guard(service.list_companies) or []
if not companies:
    st.info("Chưa có doanh nghiệp nào trên Backend. Hãy đăng nhập FastAPI và bấm **🏭 Sinh 25 Doanh nghiệp mẫu (API)** ở thanh bên.")
    st.stop()

with st.sidebar:
    labels = {c["company_id"]: f"{c['company_id']} · {c['name']} ({c['size_tier']})" for c in companies}
    company_id = st.selectbox(
        "Doanh nghiệp (company_id)",
        sorted(labels, key=lambda cid: (cid != "COMP-CANONICAL-01", cid)),
        format_func=labels.get,
    )
    company = next(c for c in companies if c["company_id"] == company_id)
    execution_mode = st.radio(
        "Chế độ thực thi",
        ["simulation", "hybrid_lab"],
        index=0 if company["execution_mode"] == "simulation" else 1,
        help="hybrid_lab mở phiên WinRM/SSH thật tới LAB_AD_HOST / LAB_PC02_HOST khi đặt ISO_LAB_ENABLE_REAL=1.",
    )
    auto_remediate = st.checkbox("Tự động lập kế hoạch & khắc phục", value=True)
    dry_run = st.checkbox("Dry-run (không thực thi)", value=False)
    use_llm = st.checkbox("Dùng SLM qwen2.5:7b (Ollama)", value=False)
    admin_name = st.text_input("Quản trị viên phê duyệt", value="admin_dashboard")
    run_scan = st.button("🔍 Quét tuân thủ toàn diện", type="primary", use_container_width=True)
    st.caption(f"Quy mô: {company['employee_count']} nhân sự · SoA loại trừ: {len(company['soa_exclusions'])} control")

scan_key = f"scan::{company_id}"
if run_scan:
    with st.spinner("Đang chạy đồ thị 8 bước cho toàn bộ control…"):
        result = _guard(
            service.assess_company,
            company_id,
            auto_remediate=auto_remediate,
            use_llm=use_llm,
            dry_run=dry_run,
            execution_mode=execution_mode,
        )
    if result:
        st.session_state[scan_key] = result

tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Tổng quan 3 Trụ cột", "✅ Phê duyệt hành động (HITL)", "🗣️ Phỏng vấn thích ứng", "🧪 Benchmark đối chứng"]
)

# ------------------------------------------------------------------ tab 1
with tab1:
    scan = st.session_state.get(scan_key)
    if scan:
        st.caption(
            f"Lượt quét `{scan['assessment_batch_id']}` · chế độ hiệu lực: **{scan['effective_execution_mode']}** · "
            f"{scan['completed_at_utc']}"
        )
        cols = st.columns(len(COMPLIANCE_STATES))
        for col, state in zip(cols, COMPLIANCE_STATES):
            col.metric(f"{STATUS_ICON[state]} {state}", scan["status_counts"][state])
        rows = [
            {
                "Control": c["control_id"],
                "Trụ cột": c["pillar"],
                "Ban đầu": c["initial_status"],
                "Hiện tại": f"{STATUS_ICON[c['status']]} {c['status']}",
                "Chờ duyệt": len(c["pending_approval_action_ids"]),
                "Cảnh báo injection": len(c["prompt_injection_alerts"]),
            }
            for c in scan["controls"]
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        picked = st.selectbox("Xem vết chi tiết của control", [c["control_id"] for c in scan["controls"]])
        detail = next(c for c in scan["controls"] if c["control_id"] == picked)
        flow = " → ".join(detail["stage_history"])
        st.markdown(f"**Vết Closed-loop ({len(detail['stage_history'])}/{len(CLOSED_LOOP_STAGES)} bước):** {flow}")
        st.write(detail["rationale"])
        if detail.get("llm_execution_log"):
            st.caption(f"Vết gọi SLM: `{detail['llm_execution_log']}`")
        if detail["verification_summary"]:
            st.info(detail["verification_summary"])
        if detail["executed_actions"]:
            st.dataframe(pd.DataFrame(detail["executed_actions"]), hide_index=True, use_container_width=True)
        if detail["findings"]:
            with st.expander("Phát hiện (findings)"):
                st.json(detail["findings"])
    else:
        latest = _guard(service.latest_assessments, company_id) or []
        if latest:
            st.caption("Kết quả gần nhất đã lưu (bấm quét để chạy lại).")
            st.dataframe(
                pd.DataFrame(
                    [
                        {"Control": a["control_id"], "Trụ cột": a["pillar"], "Trạng thái": a["status"], "Bước": a["current_stage"]}
                        for a in latest
                    ]
                ),
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("Chưa có kết quả. Bấm **Quét tuân thủ toàn diện** ở thanh bên.")

# ------------------------------------------------------------------ tab 2
with tab2:
    pending = _guard(service.list_actions, company_id, "PENDING_APPROVAL") or []
    st.subheader(f"Lệnh chờ duyệt ({len(pending)})")
    st.caption("Mức HIGH luôn dừng ở đây: Agent không tự thực thi khóa AD, ép mã hóa ổ đĩa hay gỡ phần mềm.")
    if not pending:
        st.success("Không có lệnh nào đang chờ duyệt.")
    for act in pending:
        title = f"{RISK_ICON.get(act['risk_level'], act['risk_level'])} · {act['tool_name']} · {act['control_id']}"
        with st.expander(title, expanded=True):
            st.write("**Tham số (đã qua Pydantic):**")
            st.json(act["tool_params"])
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Xem trước (dry-run):**")
                st.json(act.get("dry_run_preview") or {})
            with c2:
                st.write("**snapshot_before (dùng để rollback):**")
                st.json(act.get("snapshot_before") or {})
            reason = st.text_input("Lý do từ chối (bắt buộc khi Reject)", key=f"reason::{act['action_id']}")
            b1, b2 = st.columns(2)
            if b1.button("✅ Approve", key=f"ok::{act['action_id']}", type="primary"):
                res = _guard(
                    service.decide,
                    company_id,
                    act["action_id"],
                    "APPROVE",
                    admin_name,
                    "",
                    act.get("assessment_run_id"),
                    execution_mode,
                )
                if res:
                    st.session_state.pop(scan_key, None)
                    st.toast(f"Đã duyệt · trạng thái control: {res['assessment']['status']}")
                    st.rerun()
            if b2.button("⛔ Reject", key=f"no::{act['action_id']}"):
                res = _guard(
                    service.decide,
                    company_id,
                    act["action_id"],
                    "REJECT",
                    admin_name,
                    reason,
                    act.get("assessment_run_id"),
                    execution_mode,
                )
                if res:
                    st.session_state.pop(scan_key, None)
                    st.toast("Đã từ chối hành động.")
                    st.rerun()

    history = [a for a in (_guard(service.list_actions, company_id) or []) if a["approval_status"] != "PENDING_APPROVAL"]
    if history:
        st.subheader("Lịch sử hành động")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Tool": a["tool_name"],
                        "Control": a["control_id"],
                        "Rủi ro": a["risk_level"],
                        "Trạng thái": a["approval_status"],
                        "Người duyệt": a.get("approved_by"),
                    }
                    for a in history
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )

# ------------------------------------------------------------------ tab 3
with tab3:
    st.warning(
        "⚖️ Đạo đức AI: điểm do SLM chấm chỉ phục vụ đào tạo. `disciplinary_blocked = True` luôn bật — "
        "không dùng kết quả này làm căn cứ kỷ luật khi chưa có con người xác minh."
    )
    employees = _guard(service.list_employees, company_id) or []
    active = [e for e in employees if e["employment_status"] != "terminated"]
    if active:
        emp_labels = {e["employee_id"]: f"{e['employee_id']} · {e['full_name']} ({e['department']})" for e in active}
        emp_id = st.selectbox("Nhân viên", list(emp_labels), format_func=emp_labels.get)
        session_key = f"interview::{company_id}::{emp_id}"
        if st.button("▶️ Bắt đầu phỏng vấn A.6.8"):
            session = _guard(service.start_interview, company_id, emp_id, "A.6.8")
            if session:
                st.session_state[session_key] = session
                st.session_state.pop(f"graded::{session_key}", None)

        session = st.session_state.get(session_key)
        graded = st.session_state.get(f"graded::{session_key}")
        if session and not graded:
            with st.form(f"form::{session_key}"):
                answers = []
                for i, q in enumerate(session["questions"], 1):
                    st.markdown(f"**Câu {i}.** {q['prompt']}")
                    answers.append(st.text_area("Trả lời", key=f"ans::{session_key}::{i}", height=100))
                submitted = st.form_submit_button("Nộp bài")
            if submitted:
                res = _guard(service.submit_interview, company_id, session["session_id"], answers, use_llm)
                if res:
                    st.session_state[f"graded::{session_key}"] = res
                    st.rerun()
        if graded:
            verdict = "✅ Đạt" if graded["passed"] else "❌ Chưa đạt"
            st.metric("Điểm SLM (0–10)", graded["slm_score"], verdict)
            st.write(graded["slm_feedback"])
            st.caption(f"Nguồn chấm: {graded['grading_source']}")
            if graded["prompt_injection_alerts"]:
                st.error(f"Phát hiện Prompt Injection: {graded['prompt_injection_alerts']}")
            st.info(
                f"human_verified = {graded['human_verified']} · disciplinary_blocked = {graded['disciplinary_blocked']}"
            )
            v1, v2 = st.columns(2)
            if v1.button("🧑‍⚖️ Kiểm toán viên xác nhận Đạt"):
                if _guard(service.verify_interview, company_id, graded["session_id"], admin_name, True):
                    st.success("Đã xác minh: cập nhật incident_process_known = True.")
            if v2.button("🧑‍⚖️ Kiểm toán viên xác nhận Chưa đạt"):
                if _guard(service.verify_interview, company_id, graded["session_id"], admin_name, False):
                    st.success("Đã xác minh: giữ incident_process_known = False.")
    else:
        st.info("Doanh nghiệp này không có nhân sự đang làm việc.")

# ------------------------------------------------------------------ tab 4
with tab4:
    st.caption("4 mô hình chạy trên cùng ≥25 doanh nghiệp; Ground Truth chỉ được đọc sau khi mọi mô hình chạy xong.")
    if st.button("🧪 Chạy benchmark 25 doanh nghiệp"):
        with st.spinner("Đang chạy M1–M4 (khoảng 10–30 giây)…"):
            _guard(service.run_benchmark, 25, 2026, use_llm)
    report = _guard(service.latest_benchmark)
    if not report:
        st.info("Chưa có kết quả. Bấm nút phía trên để chạy.")
    else:
        df = pd.DataFrame(report["summary"])
        st.caption(f"{report['enterprise_count']} doanh nghiệp · {df['evaluated_cases'].iloc[0]} ca · {report['generated_at_utc']}")
        show = [
            "model_name", "precision", "recall", "f1_score", "fpr",
            "false_remediation_rate", "remediation_success_rate", "avg_latency_ms", "total_tokens", "estimated_token_cost_usd",
        ]
        st.dataframe(df[show], hide_index=True, use_container_width=True)
        chart = df.set_index("model_name")[["precision", "recall", "f1_score", "false_remediation_rate"]]
        st.bar_chart(chart)
        st.caption(f"Xuất: `{report['exports']['csv_path']}` · `{report['exports']['json_path']}`")
