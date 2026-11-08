"""
ISO/IEC 27001:2022 Statement of Applicability (SoA) & Risk Treatment Plan (RTP)
=================================================================================
Bản Tuyên bố về Khả năng Áp dụng (SoA) và Kế hoạch Xử lý Rủi ro (RTP)
được tạo tự động theo thời gian thực từ dữ liệu kiểm toán trong PostgreSQL.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import UUID

from backend import database, teamwork


DOMAIN_NAMES = {
    "A.5": "Kiểm soát Tổ chức (Organizational Controls)",
    "A.6": "Kiểm soát Con người (People Controls)",
    "A.7": "Kiểm soát Vật lý (Physical Controls)",
    "A.8": "Kiểm soát Công nghệ (Technological Controls)",
}


def build_soa_matrix(assessment_id: str | UUID) -> Dict[str, Any]:
    """Tổng hợp bảng ma trận SoA từ cơ sở dữ liệu kiểm toán hiện hành."""
    assessment_id_str = str(assessment_id)
    all_controls = database.list_controls()
    progress_board = teamwork.progress_board(assessment_id_str)
    progress_by_id = {item["control_id"]: item for item in progress_board}

    soa_rows: List[Dict[str, Any]] = []
    stats = {
        "total": len(all_controls),
        "applicable": len(all_controls),
        "compliant": 0,
        "partially_compliant": 0,
        "non_compliant": 0,
        "insufficient_evidence": 0,
        "not_started": 0,
    }

    rtp_items: List[Dict[str, Any]] = []

    for ctrl in all_controls:
        cid = ctrl["control_id"]
        prefix = cid.split(".")[0] + "." + cid.split(".")[1]
        domain = DOMAIN_NAMES.get(prefix, ctrl.get("group", "Chung"))
        prog = progress_by_id.get(cid, {})

        comp_status = prog.get("compliance_status") or "Chưa đánh giá"
        workflow_status = prog.get("workflow_status") or "NOT_STARTED"

        if comp_status == "Compliant":
            stats["compliant"] += 1
        elif comp_status == "Partially Compliant":
            stats["partially_compliant"] += 1
        elif comp_status == "Non-Compliant":
            stats["non_compliant"] += 1
        elif comp_status == "Insufficient Evidence":
            stats["insufficient_evidence"] += 1
        else:
            stats["not_started"] += 1

        rationale = "Đang chờ nạp bằng chứng và kích hoạt phiên đánh giá."
        if prog.get("latest_evaluation_id"):
            history = teamwork.list_history(assessment_id_str, cid)
            if history:
                rationale = history[0].get("rationale") or rationale

        is_gap = comp_status in ("Non-Compliant", "Partially Compliant", "Insufficient Evidence")
        row = {
            "control_id": cid,
            "name": ctrl["name"],
            "domain": domain,
            "objective": ctrl["objective"],
            "is_applicable": True,
            "justification": "Bắt buộc áp dụng theo phạm vi ISMS của doanh nghiệp.",
            "compliance_status": comp_status,
            "workflow_status": workflow_status,
            "assigned_to": prog.get("assigned_to") or "Chưa phân công",
            "rationale": rationale,
            "updated_at": prog.get("updated_at"),
        }
        soa_rows.append(row)

        if is_gap:
            rtp_items.append({
                "control_id": cid,
                "name": ctrl["name"],
                "status": comp_status,
                "domain": domain,
                "finding": rationale,
                "owner": prog.get("assigned_to") or ("HR" if "A.6" in cid else "IT / SecOps"),
                "priority": "Cao" if comp_status == "Non-Compliant" else "Trung bình",
                "target_resolution": "Hoàn tất khắc phục và nạp bằng chứng bổ sung trước kỳ đánh giá chính thức.",
            })

    # Tỷ lệ tuân thủ trên tổng số controls
    compliance_score = round(
        (stats["compliant"] + stats["partially_compliant"] * 0.5) / max(stats["total"], 1) * 100, 1
    )

    return {
        "assessment_id": assessment_id_str,
        "standard": "ISO/IEC 27001:2022 & ISO/IEC 27002:2022 Annex A",
        "title": "BẢN TUYÊN BỐ VỀ KHẢ NĂNG ÁP DỤNG (STATEMENT OF APPLICABILITY - SoA)",
        "organization": "HiveFive Enterprise System",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": {
            **stats,
            "compliance_percentage": compliance_score,
        },
        "controls": soa_rows,
        "risk_treatment_plan": rtp_items,
    }


def render_soa_html(soa_data: Dict[str, Any]) -> str:
    """Sinh trang HTML định dạng báo cáo kiểm toán chuyên nghiệp để in hoặc xuất PDF."""
    stats = soa_data["stats"]
    ctrl_rows = ""
    for c in soa_data["controls"]:
        status_color = "#10b981" if c["compliance_status"] == "Compliant" else (
            "#f59e0b" if c["compliance_status"] == "Partially Compliant" else (
                "#ef4444" if c["compliance_status"] == "Non-Compliant" else "#6b7280"
            )
        )
        ctrl_rows += f"""
        <tr>
            <td style="font-weight: bold; font-family: monospace;">{c['control_id']}</td>
            <td><strong>{c['name']}</strong><br><small style="color:#64748b;">{c['domain']}</small></td>
            <td style="text-align: center;"><span style="background: #e2e8f0; padding: 3px 8px; border-radius: 4px; font-size: 11px;">Áp dụng</span></td>
            <td><span style="color: {status_color}; font-weight: bold;">● {c['compliance_status']}</span></td>
            <td style="font-size: 12px; color: #334155;">{c['rationale']}</td>
            <td style="font-size: 11px; color: #64748b;">{c['assigned_to']}</td>
        </tr>
        """

    rtp_rows = ""
    for r in soa_data["risk_treatment_plan"][:15]:
        rtp_rows += f"""
        <tr>
            <td style="font-weight: bold;">{r['control_id']}</td>
            <td>{r['name']}</td>
            <td><span style="color: #ef4444; font-weight: bold;">{r['status']}</span></td>
            <td style="font-size: 12px;">{r['finding']}</td>
            <td><strong>{r['owner']}</strong></td>
            <td><span style="background: #fee2e2; color: #991b1b; padding: 2px 6px; border-radius: 4px; font-size: 11px;">{r['priority']}</span></td>
        </tr>
        """

    html = f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<title>Statement of Applicability (SoA) — ISO/IEC 27001:2022</title>
<style>
    @page {{ size: A4 landscape; margin: 15mm; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; margin: 0; padding: 25px; color: #1e293b; background: #fff; line-height: 1.5; }}
    .header {{ border-bottom: 2px solid #0f172a; padding-bottom: 15px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: flex-end; }}
    h1 {{ margin: 0; font-size: 22px; color: #0f172a; }}
    .sub {{ color: #64748b; font-size: 13px; margin-top: 4px; }}
    .meta-box {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; margin-bottom: 25px; }}
    .meta-item strong {{ display: block; font-size: 20px; color: #2563eb; }}
    .meta-item span {{ font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: bold; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 30px; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 8px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #f1f5f9; color: #334155; font-size: 12px; text-transform: uppercase; }}
    .section-title {{ font-size: 16px; font-weight: bold; margin: 25px 0 12px 0; color: #0f172a; border-left: 4px solid #2563eb; padding-left: 10px; }}
    .print-btn {{ position: fixed; bottom: 20px; right: 20px; background: #2563eb; color: #fff; border: none; padding: 12px 20px; border-radius: 8px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
    @media print {{ .print-btn {{ display: none; }} body {{ padding: 0; }} }}
</style>
</head>
<body>
    <button class="print-btn" onclick="window.print()">🖨️ In / Lưu file PDF (Ctrl+P)</button>
    <div class="header">
        <div>
            <h1>{soa_data['title']}</h1>
            <div class="sub">Tiêu chuẩn: <strong>{soa_data['standard']}</strong> | Tổ chức: <strong>{soa_data['organization']}</strong></div>
        </div>
        <div style="text-align: right; font-size: 12px; color: #64748b;">
            Mã đánh giá: {soa_data['assessment_id'][:8]}...<br>
            Thời điểm trích xuất: {soa_data['generated_at'][:19].replace('T', ' ')} UTC
        </div>
    </div>

    <div class="meta-box">
        <div class="meta-item">
            <span>Tổng Controls Phạm vi</span>
            <strong>{stats['total']}</strong>
        </div>
        <div class="meta-item">
            <span>Đạt Tuân thủ (Compliant)</span>
            <strong style="color: #10b981;">{stats['compliant']}</strong>
        </div>
        <div class="meta-item">
            <span>Còn lỗ hổng (Gaps / Review)</span>
            <strong style="color: #ef4444;">{stats['non_compliant'] + stats['partially_compliant'] + stats['insufficient_evidence']}</strong>
        </div>
        <div class="meta-item">
            <span>Chỉ số Tuân thủ ISMS</span>
            <strong style="color: #2563eb;">{stats['compliance_percentage']}%</strong>
        </div>
    </div>

    <div class="section-title">1. MA TRẬN KHẢ NĂNG ÁP DỤNG CÁC KIỂM SOÁT (ANNEX A CONTROLS MATRIX)</div>
    <table>
        <thead>
            <tr>
                <th style="width: 80px;">Mã</th>
                <th style="width: 220px;">Tên Kiểm Soát & Phân Nhóm</th>
                <th style="width: 90px; text-align: center;">Áp dụng</th>
                <th style="width: 130px;">Trạng Thái</th>
                <th>Căn Cứ Đánh Giá / Rationale (AI Agent)</th>
                <th style="width: 100px;">Phụ trách</th>
            </tr>
        </thead>
        <tbody>
            {ctrl_rows}
        </tbody>
    </table>

    <div class="section-title">2. KẾ HOẠCH XỬ LÝ RỦI RO & KHẮC PHỤC (RISK TREATMENT PLAN - RTP)</div>
    <p style="font-size: 12px; color: #64748b;">Danh sách các kiểm soát chưa đạt được trích xuất tự động để làm kế hoạch khắc phục nộp cho đoàn đánh giá chứng nhận:</p>
    <table>
        <thead>
            <tr>
                <th style="width: 80px;">Mã</th>
                <th style="width: 200px;">Kiểm Soát</th>
                <th style="width: 120px;">Hiện Trạng</th>
                <th>Phát Hiện Cụ Thể Cần Xử Lý</th>
                <th style="width: 120px;">Phòng Ban</th>
                <th style="width: 90px;">Mức Ưu Tiên</th>
            </tr>
        </thead>
        <tbody>
            {rtp_rows}
        </tbody>
    </table>
</body>
</html>"""
    return html

