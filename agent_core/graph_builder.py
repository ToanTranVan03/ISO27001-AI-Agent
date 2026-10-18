import os
import json
import ollama
from typing import List, Dict, Any, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field, field_validator
from langgraph.graph import StateGraph, START, END

from backend.database import collect_evidence, get_rubric

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

# ==========================================
# 2. ĐỊNH NGHĨA CÁC NODE
# ==========================================
def node_plan(state: AgentState):
    state["audit_trail"].append("PLAN")
    return state

def node_collect(state: AgentState):
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
    state["audit_trail"].append("EVALUATE")
    return state

def node_verify(state: AgentState):
    # Guardrail 1: Kho bằng chứng rỗng
    if not state["collected_evidences"]:
        state["compliance_status"] = "Insufficient Evidence"
        state["rationale"] = "[GUARDRAIL] Tự động ghi đè: Không tìm thấy bằng chứng hợp lệ."
    else:
        # Guardrail 2: Đối chiếu chéo với Deterministic Rule
        rule_expected = state["deterministic_rule"].get("expected_status")
        if rule_expected and state["compliance_status"] != rule_expected:
            state["compliance_status"] = rule_expected
            state["rationale"] = f"[GUARDRAIL] AI suy luận sai. Tự động ghi đè trạng thái chuẩn: {rule_expected}."
            
    state["audit_trail"].append("VERIFY")
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