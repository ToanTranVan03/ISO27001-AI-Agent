import os
import json
import ollama
from typing import List, Dict, Any, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field, field_validator
from langgraph.graph import StateGraph, START, END

from backend.database import collect_evidence, get_rubric
from backend.enterprise_spec import CONTROL_TO_NODE, NODE_SPECS

# ==========================================
# 1. ĐỊNH NGHĨA SCHEMA & TRẠNG THÁI
# ==========================================
ComplianceStatus = Literal[
    "Compliant", "Partially Compliant", "Non-Compliant", 
    "Not Applicable", "Insufficient Evidence"
]

class ControlEvaluationOutput(BaseModel):
    status: ComplianceStatus
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    rationale: str
    evidence_ids: List[str]

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, v: Any) -> float:
        try:
            val = float(v)
            if val > 1.0: val = val / 100.0
            return max(0.0, min(1.0, round(val, 4)))
        except Exception:
            return 0.85

class AgentState(TypedDict):
    control_id: str
    control_name: str
    objective: str
    collected_evidences: List[Dict[str, Any]]
    deterministic_rule: Dict[str, Any]  # Thêm Rule để Guardrail đối chiếu
    compliance_status: str
    confidence: float
    rationale: str
    audit_trail: List[str]
    assessment_id: str
    validated_evidence_ids: List[str]
    proposed_evidence_ids: List[str]

# ==========================================
# 2. ĐỊNH NGHĨA CÁC NODE
# ==========================================
def node_plan(state: AgentState):
    node_key=CONTROL_TO_NODE.get(state['control_id']) if state.get('assessment_id') else None
    if node_key:
        state['audit_trail'].append('PLAN → SELECT TOOL: ' + NODE_SPECS[node_key]['tool'])
    else:
        state['audit_trail'].append('PLAN → SELECT TOOL: uploaded-document-evidence')
    return state

def node_collect(state: AgentState):
    if state.get('assessment_id') and state['control_id'] in CONTROL_TO_NODE:
        from backend.enterprise_lab import collect_lab_snapshot
        snapshot = collect_lab_snapshot(state['assessment_id'],state['control_id'])
        state['audit_trail'].append('COLLECT SYNTHETIC LAB EVIDENCE: ' + snapshot['evidence_id'])
    if state.get("assessment_id"):
        evidences, deterministic_rule = collect_evidence(state["control_id"], state["assessment_id"])
    else:
        evidences, deterministic_rule = collect_evidence(state["control_id"])
    state["collected_evidences"] = evidences
    state["deterministic_rule"] = deterministic_rule
    state["audit_trail"].append("COLLECT")
    return state

def node_evaluate(state: AgentState):
    import re
    import json
    import os
    print(f"[NODE: EVALUATE] Gọi Qwen2.5:7B đọc bằng chứng và Rubric ra quyết định...")

    if not state["collected_evidences"]:
        state["compliance_status"] = "Insufficient Evidence"
        state["confidence"] = 1.0
        state["rationale"] = "Không có bằng chứng đầu vào."
        state["proposed_evidence_ids"] = []
        state["audit_trail"].append("EVALUATE (SKIPPED)")
        return state

    safe_evidences = []
    for ev in state["collected_evidences"]:
        ev_copy = dict(ev)
        ev_copy["content"] = re.sub(r"\[SYSTEM INSTRUCTION:.*?\]", "[BLOCKED_BY_GUARDRAIL]", ev_copy["content"], flags=re.I)
        safe_evidences.append(ev_copy)

    rubric_text = "Không có tiêu chí chấm điểm cụ thể cho Control này."
    rubric = get_rubric(state["control_id"])
    if rubric:
        rubric_text = (
            f"- Compliant: {rubric['Compliant']}\n"
            f"- Partially Compliant: {rubric['Partially Compliant']}\n"
            f"- Non-Compliant: {rubric['Non-Compliant']}"
        )

    # Nhồi Rubric vào System Prompt để ÉP AI phải nghe lời
    sys_prompt = f"""Bạn là AI Agent kiểm toán chuyên nghiệp ISO/IEC 27001. 
BẮT BUỘC TRẢ LỜI TRƯỜNG 'rationale' BẰNG TIẾNG VIỆT NGẮN GỌN (TỐI ĐA 2 CÂU).

TIÊU CHÍ CHẤM ĐIỂM (RUBRIC) CHO CONTROL NÀY:
{rubric_text}

Dựa vào tiêu chí trên và bằng chứng, hãy xuất ra JSON đánh giá."""
    
    user_prompt = f"""Control: {state['control_id']} - {state['control_name']}
Bằng chứng: {json.dumps(safe_evidences, ensure_ascii=False)}"""

    # Gọi mô hình Ollama (Phần này giữ nguyên như cũ)
    ollama_client = ollama.Client(
        host=os.getenv("OLLAMA_HOST", "http://localhost:11434")
    )
    resp = ollama_client.chat(
        model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ],
        format=ControlEvaluationOutput.model_json_schema(),
        options={"temperature": 0.0, "num_predict": 250, "num_ctx": 4096}
    )
    
    parsed = ControlEvaluationOutput.model_validate_json(resp["message"]["content"])
    state["compliance_status"] = parsed.status
    state["confidence"] = parsed.confidence
    state["rationale"] = parsed.rationale
    state["proposed_evidence_ids"] = parsed.evidence_ids
    state["audit_trail"].append("EVALUATE")
    return state

def node_verify(state: AgentState):
    # Evidence-first: keep ONLY IDs genuinely returned by the model and present in
    # the evidence collected for this evaluation. Ground truth is never read here.
    available = {ev['evidence_id'] for ev in state['collected_evidences']}
    proposed = state.get('proposed_evidence_ids', [])
    valid = [value for value in proposed if value in available]
    state['validated_evidence_ids'] = list(dict.fromkeys(valid))
    if not available or (state['compliance_status'] != 'Insufficient Evidence' and not valid):
        state['compliance_status'] = 'Insufficient Evidence'
        state['confidence'] = 0.0
        state['rationale'] = 'Chưa đủ bằng chứng hợp lệ được viện dẫn để xác nhận kết luận.'
    elif len(valid) < len(proposed):
        state['audit_trail'].append('VERIFY (REJECTED UNKNOWN EVIDENCE IDS)')
    state['audit_trail'].append('VERIFY')
    return state

def node_report(state: AgentState):
    state["audit_trail"].append("REPORT")
    return state

# ==========================================
# 3. BUILD GRAPH
# ==========================================
def build_iso_agent_graph():
    builder = StateGraph(AgentState)
    for node_name, node_func in [("PLAN", node_plan), ("COLLECT", node_collect), 
                                 ("EVALUATE", node_evaluate), ("VERIFY", node_verify), 
                                 ("REPORT", node_report)]:
        builder.add_node(node_name, node_func)
    
    builder.add_edge(START, "PLAN")
    builder.add_edge("PLAN", "COLLECT")
    builder.add_edge("COLLECT", "EVALUATE")
    builder.add_edge("EVALUATE", "VERIFY")
    builder.add_edge("VERIFY", "REPORT")
    builder.add_edge("REPORT", END)
    
    return builder.compile()

# ==========================================
# 4. CHẠY HÀNG LOẠT TRÊN 6 TÌNH HUỐNG DOANH NGHIỆP
# ==========================================
if __name__ == "__main__":
    from backend.database import get_control, initialize_database
    from agent_core.enterprise_eval_and_charts import ENTERPRISE_TEST_CASES

    initialize_database()
    graph = build_iso_agent_graph()
    print("=== BẮT ĐẦU CHẠY LANGGRAPH TRÊN DỮ LIỆU DOANH NGHIỆP (6 CONTROLS) ===\n")
    
    for case in ENTERPRISE_TEST_CASES:
        control = get_control(case["control_id"])
        if control is None:
            raise RuntimeError(f"Control {case['control_id']} is missing from PostgreSQL.")
        initial_state = {
            "control_id": control["control_id"],
            "control_name": control["name"],
            "objective": control["objective"],
            "collected_evidences": [],
            "deterministic_rule": {},
            "compliance_status": "UNKNOWN",
            "confidence": 0.0,
            "rationale": "",
            "audit_trail": []
        }
        
        print(f"-> Đang xử lý Node Stream cho [{case['control_id']}]...")
        final_state = graph.invoke(initial_state)
        
        print(f"   Kết quả    : {final_state['compliance_status']}")
        print(f"   Lý giải AI : {final_state['rationale']}\n")