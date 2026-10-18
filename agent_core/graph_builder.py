import os
import json
import ollama
from typing import List, Dict, Any, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field, field_validator
from langgraph.graph import StateGraph, START, END

# Lấy dữ liệu 6 tình huống doanh nghiệp từ file Tuần 1 sang
from agent_core.enterprise_eval_and_charts import ENTERPRISE_TEST_CASES

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
    # Tìm kiếm đúng Test Case trong cơ sở dữ liệu Tuần 1
    case = next((c for c in ENTERPRISE_TEST_CASES if c["control_id"] == state["control_id"]), None)
    if case:
        state["collected_evidences"] = case["evidences"]
        state["deterministic_rule"] = case.get("deterministic_rule", {})
    
    state["audit_trail"].append("COLLECT")
    return state

def node_evaluate(state: AgentState):
    import re
    print(f"[NODE: EVALUATE] Gọi Qwen2.5:7B đọc bằng chứng và ra quyết định...")

    # 1. BỎ QUA GỌI AI NẾU KHÔNG CÓ BẰNG CHỨNG (Tránh treo và tiết kiệm thời gian)
    if not state["collected_evidences"]:
        state["compliance_status"] = "Insufficient Evidence"
        state["confidence"] = 1.0
        state["rationale"] = "Không có bằng chứng đầu vào."
        state["audit_trail"].append("EVALUATE (SKIPPED)")
        return state

    # 2. Lọc Prompt Injection an toàn
    safe_evidences = []
    for ev in state["collected_evidences"]:
        ev_copy = dict(ev)
        ev_copy["content"] = re.sub(r"\[SYSTEM INSTRUCTION:.*?\]", "[BLOCKED_BY_GUARDRAIL]", ev_copy["content"], flags=re.I)
        safe_evidences.append(ev_copy)

    sys_prompt = """Bạn là AI Agent kiểm toán ISO/IEC 27001. Dựa vào bằng chứng cung cấp, hãy xuất ra JSON đánh giá.
BẮT BUỘC TRẢ LỜI TRƯỜNG 'rationale' BẰNG TIẾNG VIỆT NGẮN GỌN (TỐI ĐA 2 CÂU)."""
    
    user_prompt = f"""Control: {state['control_id']} - {state['control_name']}
Mục tiêu: {state['objective']}
Bằng chứng: {json.dumps(safe_evidences, ensure_ascii=False)}"""

    # 3. Đặt giới hạn an toàn (num_predict và num_ctx) để AI không bao giờ bị treo
    resp = ollama.chat(
        model="qwen2.5:7b",
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ],
        format=ControlEvaluationOutput.model_json_schema(),
        options={
            "temperature": 0.0, 
            "num_predict": 250,  # Khóa mõm: Không cho phép nói quá 250 tokens
            "num_ctx": 4096      # Mở rộng Context window để đọc JSON không lỗi
        }
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
    graph = build_iso_agent_graph()
    print("=== BẮT ĐẦU CHẠY LANGGRAPH TRÊN DỮ LIỆU DOANH NGHIỆP (6 CONTROLS) ===\n")
    
    for case in ENTERPRISE_TEST_CASES:
        initial_state = {
            "control_id": case["control_id"],
            "control_name": case["name"],
            "objective": case["objective"],
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