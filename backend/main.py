from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os

# Thêm thư mục gốc vào đường dẫn hệ thống để gọi được code từ agent_core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent_core.graph_builder import build_iso_agent_graph
from agent_core.enterprise_eval_and_charts import ENTERPRISE_TEST_CASES

# Khởi tạo API Server
app = FastAPI(title="ISO 27001 AI Agent API", version="1.0")

# Biên dịch sẵn Đồ thị AI một lần khi bật server cho nhẹ
agent_graph = build_iso_agent_graph()

# Cấu trúc dữ liệu yêu cầu từ Frontend gửi lên
class EvaluationRequest(BaseModel):
    control_id: str

@app.get("/")
async def root():
    return {"message": "Hệ thống AI Agent ISO 27001 Backend đang hoạt động!"}

@app.post("/api/evaluate")
async def evaluate_control(req: EvaluationRequest):
    # 1. Tìm thông tin control trong dữ liệu giả lập Tuần 1
    case = next((c for c in ENTERPRISE_TEST_CASES if c["control_id"] == req.control_id), None)
    
    if not case:
        raise HTTPException(status_code=404, detail="Không tìm thấy mã Control này trong hệ thống.")

    # 2. Chuẩn bị State ban đầu để đưa vào LangGraph
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

    # 3. Kích hoạt Agent chạy luồng Đồ thị
    try:
        final_state = agent_graph.invoke(initial_state)
        # 4. Trả kết quả JSON sạch sẽ về cho Web/Frontend
        return {
            "control_id": final_state["control_id"],
            "status": final_state["compliance_status"],
            "confidence": final_state["confidence"],
            "rationale": final_state["rationale"],
            "audit_trail": final_state["audit_trail"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))