import json
from os import getenv
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener
from uuid import uuid4

import streamlit as st

PORT = int(getenv("COMPLIANCE_API_PORT", "8000"))
HOST = getenv("COMPLIANCE_API_HOST", "127.0.0.1")
if HOST not in ("127.0.0.1", "api"):
    raise ValueError("UI allows only the local API or the private Compose service name")
BASE = f"http://{HOST}:{PORT}/api/v1"
HTTP = build_opener(ProxyHandler({}))


def call(
    path: str,
    *,
    payload: dict | None = None,
    method: str = "GET",
    key: str | None = None,
    raw: bool = False,
):
    headers = {"Content-Type": "application/json"}
    if "token" in st.session_state:
        headers["Authorization"] = "Bearer " + st.session_state["token"]
    if key:
        headers["Idempotency-Key"] = key
    data = json.dumps(payload).encode() if payload is not None else None
    request = Request(BASE + path, method=method, headers=headers, data=data)
    try:
        with HTTP.open(request, timeout=30) as response:
            return response.read() if raw else json.load(response)
    except HTTPError as error:
        if error.code == 401 and "token" in st.session_state:
            st.session_state.clear()
            st.rerun()
        try:
            message = json.load(error).get("detail")
        except (ValueError, OSError):
            message = None
        st.error(message if isinstance(message, str) else f"Yêu cầu thất bại ({error.code}).")
    except (URLError, TimeoutError):
        st.error("Không kết nối được API cục bộ.")
    return None


def report(title: str, path: str, key: str) -> None:
    if st.button(title, key=f"request-{key}"):
        st.session_state[f"report-{key}"] = call(path)
    record = st.session_state.get(f"report-{key}")
    if record:
        st.download_button(
            f"Tải {title.lower()}",
            json.dumps(record, ensure_ascii=False, indent=2),
            file_name=f"{key}.json",
            mime="application/json",
            key=f"download-{key}",
        )


def employee_page(base: str) -> None:
    data = call(f"{base}/me/training")
    if not data:
        return
    assignment = data["assignment"]
    if data.get("mfa_request_id"):
        st.info(
            "Bạn có yêu cầu đăng ký MFA. Trong bài mô phỏng, trạng thái đăng ký "
            "được cập nhật từ nguồn định danh."
        )
        st.caption(f"Mã yêu cầu MFA · {data['mfa_request_id']}")
    nda = data.get("nda")
    if nda:
        st.header(nda["document"]["title"])
        st.caption(f"Phiên bản {nda['document']['version']}")
        st.text(nda["document"]["content"])
        if nda["status"] == "ASSIGNED":
            if st.button("Tôi đã đọc và xác nhận cam kết mô phỏng", key=nda["id"]):
                if call(
                    f"{base}/me/nda/acknowledge",
                    method="POST",
                    payload={
                        "request_id": nda["id"],
                        "document_hash": nda["document"]["sha256"],
                        "expected_revision": data["revision"],
                        "acknowledged": True,
                    },
                ):
                    st.rerun()
        else:
            st.write("Mã biên nhận", nda["receipt"]["evidence_id"])
    initial = data["initial"]
    retest = data["retest"]
    st.header("Phỏng vấn và đào tạo")
    if assignment:
        st.write("Trạng thái bài học", assignment["status"])
        st.info("Bài học về cách nhận biết, xử lý và báo cáo tin nhắn giả mạo.")
        if assignment["status"] == "ASSIGNED" and st.button("Xác nhận hoàn thành bài học"):
            if call(f"{base}/me/training/complete", method="POST"):
                st.rerun()
    kind = "retest" if assignment and assignment["status"] == "COMPLETED" else "initial"
    attempt = retest if kind == "retest" else initial
    grade = attempt["grade"] if attempt else None
    if grade:
        st.write("Kết quả", grade["status"], grade["score"])
    if not grade or grade["status"] == "FOLLOWUP":
        question = grade["followup"] if grade else data[f"{kind}_question"]
        st.write(question)
        with st.form(f"answer-{kind}"):
            answer = st.text_area("Câu trả lời", max_chars=2000)
            use_local_model = st.checkbox(
                "Chấm câu trả lời mô phỏng bằng Ollama cục bộ",
                disabled=not data.get("local_model_available", False),
            )
            submitted = st.form_submit_button("Gửi câu trả lời")
        if submitted and call(
            f"{base}/me/interview",
            method="POST",
            payload={"kind": kind, "answer": answer, "use_local_model": use_local_model},
        ):
            st.rerun()


def actions(base: str, run: dict, role: str) -> None:
    st.header("Hành động")
    candidates = {finding["id"]: finding for finding in run["findings"] if finding["proposed_tool"]}
    if candidates:
        selected = st.selectbox(
            "Chọn phát hiện",
            list(candidates),
            format_func=lambda identifier: candidates[identifier]["criterion_id"],
        )
        if st.button("Lập kế hoạch mô phỏng"):
            result = call(f"{base}/assessments/{run['id']}/findings/{selected}/plan", method="POST")
            if result:
                st.session_state["action_id"] = result["id"]
    pasted = st.text_input(
        "Mã hành động cần mở",
        value=st.session_state.get("action_id", ""),
        key=f"action-input-{st.session_state.get('action_id', '')}",
    ).strip()
    if not pasted:
        return
    action = call(f"{base}/actions/{pasted}")
    if not action:
        return
    st.code(action["id"])
    st.write("Trạng thái", action["state"])
    st.json(action["plan"])
    if action["verification"]:
        st.json(action["verification"])
    route = f"{base}/actions/{action['id']}"
    proof = {"plan_hash": action["plan_hash"]}
    if action["state"] in ("PROPOSED", "WAITING_APPROVAL", "APPROVED"):
        if st.button("Chạy thử điều kiện thực thi"):
            check = call(route + "/dry-run", method="POST", payload=proof)
            if check:
                st.write(check["reason"])
                st.caption(f"Phiên bản nguồn {check['revision']}")
    if role != "admin":
        return
    if action["plan"]["risk"] == "medium" and action["state"] in (
        "SUCCEEDED",
        "VERIFIED",
        "VERIFICATION_FAILED",
    ):
        st.caption("Người đã duyệt có thể khôi phục snapshot nếu nguồn chưa có thay đổi mới.")
        if st.button("Khôi phục cấu hình mô phỏng trước thay đổi"):
            if call(route + "/rollback", method="POST", payload=proof):
                st.rerun()
    if action["state"] == "WAITING_APPROVAL":
        left, right = st.columns(2)
        approved = left.button("Phê duyệt mô phỏng")
        denied = right.button("Từ chối")
        if (approved or denied) and call(
            route + "/decision",
            method="POST",
            payload=proof | {"approve": approved},
        ):
            st.rerun()
    if action["state"] in ("PROPOSED", "APPROVED") and st.button("Thực thi mô phỏng"):
        key = st.session_state.setdefault(f"execute-{action['id']}", str(uuid4()))
        if call(route + "/execute", method="POST", payload=proof, key=key):
            st.rerun()
    if action["state"] in (
        "SUCCEEDED",
        "WAITING_EXTERNAL",
        "VERIFICATION_FAILED",
    ) and st.button("Đọc lại nguồn để xác minh"):
        result = call(route + "/verify", method="POST")
        if result:
            st.write("Kết quả xác minh", result["state"])
            st.json(result["verification"])


def assessment_page(base: str, role: str) -> None:
    st.header("Đánh giá")
    with st.form("assessment"):
        code = st.text_input("Mã nhân viên", value="NV015")
        scenarios = st.checkbox("Chạy danh mục kịch bản mô phỏng")
        submitted = st.form_submit_button("Bắt đầu đánh giá")
        queued = st.form_submit_button("Lưu yêu cầu để chạy sau")
    if submitted or queued:
        result = call(
            f"{base}/assessment-jobs" if queued else f"{base}/assessments",
            method="POST",
            key=str(uuid4()),
            payload={"mode": "scenarios" if scenarios else "offboarding", "employee_code": code},
        )
        if result:
            st.session_state["job" if queued else "run"] = result
    saved_job = st.text_input("Mã yêu cầu đánh giá đã lưu")
    if saved_job and st.button("Mở yêu cầu đã lưu"):
        loaded = call(f"{base}/assessment-jobs/{saved_job.strip()}")
        if loaded:
            st.session_state["job"] = loaded
    job = st.session_state.get("job")
    if job:
        st.code(job["id"])
        if job["state"] == "PENDING" and st.button("Chạy yêu cầu đã lưu"):
            resumed = call(f"{base}/assessment-jobs/{job['id']}/resume", method="POST")
            if resumed:
                st.session_state["job"] = job = resumed
        if job["assessment_id"] and st.button("Xem kết quả yêu cầu"):
            completed = call(f"{base}/assessments/{job['assessment_id']}")
            if completed:
                st.session_state["run"] = completed
    run_id = st.text_input("Mã đánh giá đã lưu")
    if run_id and st.button("Mở đánh giá"):
        result = call(f"{base}/assessments/{run_id.strip()}")
        if result:
            st.session_state["run"] = result
    run = st.session_state.get("run")
    if not run:
        return
    st.code(run["id"])
    st.write("Phiên bản chính sách", run["policy_version"])
    st.dataframe(
        [
            {
                "Tiêu chí": item["criterion_id"],
                "Mã tham chiếu": ", ".join(item["control_ids"]),
                "Kết quả": item["status"],
                "Bằng chứng": len(item["evidence_ids"]),
                "Giải thích": item["explanation"],
            }
            for item in run["findings"]
        ],
        hide_index=True,
    )
    with st.expander("Căn cứ, điểm và độ bao phủ"):
        st.json({"điểm": run["scores"], "bằng chứng": run["findings"]})
    with st.expander("Tài liệu tham chiếu theo tiêu chí"):
        citations = run.get("citations_by_control")
        if citations is None:
            st.caption("Lần đánh giá cũ chưa lưu danh sách nguồn.")
        elif not any(citations.values()):
            st.caption("Các tiêu chí trong lần đánh giá này dùng rubric nghiên cứu.")
        else:
            refs = [item for group in citations.values() for item in group]
            selected_ref = st.selectbox(
                "Chọn nguồn tham chiếu",
                refs,
                format_func=lambda item: f"{item['control_id']} · {item['source_ref']}",
                key=f"citations-{run['id']}",
            )
            if st.button("Đọc đoạn đã dẫn"):
                query = urlencode({"expected_sha256": selected_ref["content_sha256"]})
                cited = call(
                    f"{base}/knowledge/{selected_ref['control_id']}/chunks/"
                    f"{selected_ref['chunk_id']}?{query}"
                )
                if cited:
                    st.text(cited["content"])
            missing = [control for control, items in citations.items() if not items]
            if missing:
                st.caption("Chỉ có rubric nghiên cứu · " + ", ".join(missing))
    with st.expander("Đối chiếu hai lần đánh giá"):
        before = st.text_input("Mã đánh giá trước")
        if before and st.button("Đối chiếu cùng phạm vi"):
            query = urlencode({"before": before.strip()})
            comparison = call(f"{base}/assessments/{run['id']}/compare?{query}")
            if comparison:
                st.json(comparison)
    actions(base, run, role)
    st.header("Báo cáo")
    if st.button("Tạo bản CSV khoảng cách"):
        st.session_state[f"csv-{run['id']}"] = call(
            f"{base}/assessments/{run['id']}/reports/gap.csv",
            raw=True,
        )
    csv_data = st.session_state.get(f"csv-{run['id']}")
    if csv_data:
        st.download_button(
            "Tải CSV khoảng cách", csv_data, file_name=f"gap-{run['id']}.csv", mime="text/csv"
        )
    report("Báo cáo khoảng cách", f"{base}/assessments/{run['id']}/reports/gap", f"gap-{run['id']}")
    report(
        "Báo cáo khắc phục",
        f"{base}/assessments/{run['id']}/reports/remediation",
        f"remediation-{run['id']}",
    )
    report("Nhật ký", f"{base}/reports/audit", "audit")
    report("Bản trích SoA", f"{base}/reports/soa", "soa")


def benchmark_page() -> None:
    st.header("Kết quả benchmark mô phỏng")
    upload = st.file_uploader("Chọn dashboard.json do lệnh benchmark xuất", type="json")
    if upload is None:
        return
    if upload.size > 32_000:
        st.error("Tệp tóm tắt benchmark quá lớn.")
        return
    try:
        data = json.loads(upload.getvalue())
        modes = {"MOCK_TEST_ONLY": "Chạy kiểm thử mock", "OLLAMA_LOCAL_RESEARCH": "Ollama cục bộ"}
        mode = modes[data["mode"]]
        tenants, cases = data["tenants"], data["cases"]
        if type(tenants) is not int or type(cases) is not int or not 0 < tenants <= cases:
            raise ValueError
        metrics = data["metrics"]
        if not isinstance(metrics, list) or not 1 <= len(metrics) <= 4:
            raise ValueError
        rows: list[dict[str, str | float | None]] = []
        for item in metrics:
            method = item["method"]
            if method not in ("M1", "M2", "M3", "M4") or any(
                r["Phương pháp"] == method for r in rows
            ):
                raise ValueError
            row: dict[str, str | float | None] = {"Phương pháp": method}
            for field in ("precision", "recall", "f1", "fpr", "coverage"):
                value = item[field]
                if value is not None and (type(value) not in (int, float) or not 0 <= value <= 1):
                    raise ValueError
                row[field] = value
            rows.append(row)
    except (ValueError, KeyError, TypeError):
        st.error("Tệp tóm tắt benchmark không hợp lệ.")
        return
    st.caption(f"{mode} · {tenants} doanh nghiệp · {cases} ca")
    st.dataframe(rows, hide_index=True)
    st.caption("Phạm vi đo là phát hiện. M2 và M3 dùng chung đầu ra phát hiện.")


st.set_page_config(page_title="Đánh giá an toàn thông tin", layout="wide")
st.title("Đánh giá an toàn thông tin")
st.caption("SIMULATION · Rubric nghiên cứu · ISO/IEC 27001:2022")
if "token" not in st.session_state:
    with st.form("login", clear_on_submit=True):
        username = st.text_input("Tên đăng nhập")
        password = st.text_input("Mật khẩu", type="password")
        signed_in = st.form_submit_button("Đăng nhập")
    if signed_in:
        token = call(
            "/auth/token", method="POST", payload={"username": username, "password": password}
        )
        if token:
            st.session_state["token"] = token["access_token"]
            st.rerun()
    st.stop()

if st.sidebar.button("Đăng xuất"):
    st.session_state.clear()
    st.rerun()
companies = call("/companies")
if not companies:
    st.info("Tài khoản chưa có doanh nghiệp đang hoạt động.")
    st.stop()
company_map = {company["id"]: company for company in companies}
tenant = st.sidebar.selectbox(
    "Doanh nghiệp", list(company_map), format_func=lambda item: company_map[item]["name"]
)
if st.session_state.get("active_company") != tenant:
    for state_key in list(st.session_state):
        if state_key not in ("token", "active_company"):
            del st.session_state[state_key]
    st.session_state["active_company"] = tenant
role = company_map[tenant]["role"]
st.sidebar.caption(f"Vai trò hiện tại · {role}")
base = f"/companies/{tenant}"
if role == "employee":
    employee_page(base)
else:
    if st.sidebar.radio("Trang", ("Đánh giá", "Benchmark")) == "Benchmark":
        benchmark_page()
    else:
        assessment_page(base, role)
