import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Activity, AlertTriangle, Bot, CheckCircle2, Cpu, Download, HardDrive, Loader2, Send, Shield, Terminal, Users } from "lucide-react";
const EnterpriseScene3D = lazy(() => import("./EnterpriseScene3D"));

const DOMAINS = {
  people: { label: "Con người", icon: Users, color: "#ffb777", area: "people" },
  hardware: { label: "Phần cứng", icon: HardDrive, color: "#78d7e9", area: "hardware" },
  software: { label: "Phần mềm", icon: Cpu, color: "#c4b5ff", area: "software" },
};

const PROCESS = {
  classification_started: ["action", "PHÂN LOẠI SỰ CỐ"],
  candidate_selected: ["tool", "ĐANG ĐỐI CHIẾU BẰNG CHỨNG"],
  classification_completed: ["review", "KẾT LUẬN ĐIỀU KHOẢN SAU KIỂM TRA"],
  telemetry_checked: ["tool", "TRA NHẬT KÝ HOẠT ĐỘNG"],
  incident_received: ["action", "TIẾP NHẬN SỰ CỐ"],
  scan_started: ["action", "QUÉT TELEMETRY DOANH NGHIỆP"],
  finding_detected: ["warning", "PHÁT HIỆN DẤU HIỆU"],
  activity_simulated: ["action", "TẠO NHẬT KÝ HÀNH VI MÔ PHỎNG"],
  inventory_checked: ["tool", "KIỂM TRA TÀI SẢN"],
  analysis_started: ["action", "PHÂN TÍCH"],
  analysis_completed: ["review", "KẾT LUẬN PHÂN TÍCH"],
  tool_call_started: ["tool", "GỌI CÔNG CỤ"],
  tool_call_completed: ["execute", "KẾT QUẢ HÀNH ĐỘNG"],
  verification: ["review", "XÁC MINH"],
  evidence_saved: ["success", "LƯU NHẬT KÝ"],
};

const LOG_STYLE = {
  action: "text-sky-300 border-sky-400",
  tool: "text-violet-300 border-violet-400",
  execute: "text-amber-300 border-amber-400",
  review: "text-teal-300 border-teal-400",
  success: "text-emerald-300 border-emerald-400",
  warning: "text-rose-300 border-rose-400",
};

function formatState(state) {
  if (!state || Object.keys(state).length === 0) return "Chưa có thay đổi";
  return Object.entries(state).map(([key, value]) => `${key}: ${typeof value === "string" ? value : JSON.stringify(value)}`).join(" · ");
}

function activityVisualization(controlId) {
  if (controlId === "A.7.10") return { type: "unapproved_usb_inserted", phase: "employee_action", source: "issue_description" };
  if (controlId === "A.8.19") return { type: "unapproved_software_installed", phase: "employee_action", source: "issue_description" };
  return null;
}

export default function EnterpriseIncident3D({ assessment, request, token }) {
  const [scenarios, setScenarios] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [history, setHistory] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [readiness, setReadiness] = useState(null);
  const [domain, setDomain] = useState("people");
  const [controlId, setControlId] = useState("");
  const [issueText, setIssueText] = useState("");
  const [classification, setClassification] = useState(null);
  const [chatIncidentId, setChatIncidentId] = useState("");
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [drillLoading, setDrillLoading] = useState(false);
  const [chatError, setChatError] = useState("");
  const [monitoring, setMonitoring] = useState({active:false,state:"stopped"});
  const [room, setRoom] = useState("hub");
  const [sceneActivity, setSceneActivity] = useState(null);
  const [visited, setVisited] = useState([]);
  const [events, setEvents] = useState([]);
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState("idle");
  const [currentStep, setCurrentStep] = useState("");
  const [currentTool, setCurrentTool] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const logEnd = useRef(null);
  const chatEnd = useRef(null);
  const monitorReady = useRef(false);
  const monitorDetectionSeen = useRef("");
  const base = `/api/assessments/${encodeURIComponent(assessment.assessment_id)}/enterprise`;

  const refresh = useCallback(async () => {
    const [catalog, staff, incidents, evaluation, system] = await Promise.all([
      request(`${base}/scenarios`),
      request(`${base}/people`),
      request(`${base}/incidents?limit=20`),
      request(`${base}/metrics`),
      request(`${base}/system-readiness`),
    ]);
    setScenarios(catalog.scenarios || []);
    setEmployees(staff.employees || []);
    setHistory(incidents || []);
    setMetrics(evaluation);
    setReadiness(system);
  }, [base, request]);

  useEffect(() => {
    refresh().catch((e) => setError(e.message || "Không tải được dữ liệu lab.")).finally(() => setLoading(false));
  }, [refresh]);

  useEffect(() => {
    let disposed=false;
    monitorReady.current=false;
    monitorDetectionSeen.current="";
    async function pollMonitor() {
      try {
        const state=await request(`${base}/monitor/auto/status`);
        if(disposed) return;
        setMonitoring(state);
        const detection=state.last_detection;
        if(!monitorReady.current) {
          monitorReady.current=true;
          monitorDetectionSeen.current=detection?.at||"";
        } else if(detection?.at&&detection.at!==monitorDetectionSeen.current) {
          monitorDetectionSeen.current=detection.at;
          setSceneActivity(current=>current?{...current,phase:detection.verified?"contained":"agent_check"}:current);
          const items=await request(`${base}/incidents?limit=20`);
          if(disposed) return;
          setHistory(items||[]);
          const reports=(detection.incident_ids||[]).map(id=>items.find(item=>item.incident_id===id)).filter(Boolean);
          const primary=reports[0];
          if(primary) {
            const control=primary.control_id;
            setControlId(control);
            const controlDomain=scenarios.find(item=>item.control_id===control)?.domain||"people";
            setDomain(controlDomain); setRoom(controlDomain); setClassification(primary.event?.ai_classification||null);
            setChatIncidentId(primary.incident_id);
            setResult({...primary,event:primary.event?.reported_event||primary.event,
              activity_assessment:primary.event?.device_activity_review,
              classification:primary.event?.ai_classification,
              scan_findings:detection.findings,
              actions:reports.flatMap(item=>item.actions||[]),verified:detection.verified});
            setStatus("completed");
          }
          const summary=(detection.findings||[]).map(item=>`${item.control_id} · ${item.summary}`).join("; ");
          setChatMessages(current=>[...current,{role:"assistant",content:`Giám sát tự động vừa quét thấy ${detection.findings?.length||0} dấu hiệu và đã chạy quy trình xử lý. ${summary} Hồ sơ: ${(detection.control_ids||[]).join(", ")}.`}]);
          refresh().catch(()=>{});
        }
      } catch {
        // The authenticated page may briefly reconnect while the API restarts.
      }
    }
    pollMonitor();
    const timer=setInterval(pollMonitor,2500);
    return ()=>{disposed=true;clearInterval(timer);};
  },[base,request,refresh,scenarios]);

  useEffect(() => { logEnd.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [events]);
  useEffect(() => { chatEnd.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [chatMessages, chatLoading, status]);

  const selected = scenarios.find((item) => item.control_id === controlId) || null;
  const selectedEmployee = employees.find((item) => item.employee_id === selected?.human_context?.employee_id) || selected?.employee_profile;
  const counts = useMemo(() => Object.fromEntries(Object.keys(DOMAINS).map((key) => [key, scenarios.filter((item) => item.domain === key).length])), [scenarios]);

  async function startSimulation(inputText = chatInput) {
    const typed = inputText.trim();
    const clarifying = status === "needs_input";
    const issue = clarifying ? `${issueText}\nThông tin bổ sung: ${typed}` : typed;
    if (typed.length < 12 || status === "running") return;
    setError(""); setResult(null); setClassification(null); setControlId(""); setChatIncidentId(""); setChatError(""); setEvents([]); setVisited([]); setSceneActivity(null); setStatus("running"); setRoom("hub");
    setIssueText(issue); setChatInput("");
    setChatMessages((current) => clarifying ? [...current, {role:"user", content:typed}] : [{role:"user", content:issue}]);
    setCurrentStep("Agent nhận mô tả sự cố");
    try {
      const response = await fetch(`${base}/issues/simulate/stream`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, Accept: "text/event-stream", "Content-Type": "application/json" },
        body: JSON.stringify({ issue }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `Lỗi HTTP ${response.status}`);
      }
      if (!response.body) throw new Error("Trình duyệt không hỗ trợ luồng sự kiện.");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let finished = false;
      const handleMessage = (event) => {
        if (event.type === "classification_completed") {
          const found = event.classification || {};
          const visualization = activityVisualization(event.control_id || found.control_id);
          if(visualization) setSceneActivity(current=>current||visualization);
          setClassification(found);
          setControlId(event.control_id || found.control_id || "");
          setDomain(event.domain || found.domain || "people");
          setRoom(event.domain || found.domain || "hub");
        }
        if (event.type === "needs_more_info") {
          setClassification(event.classification || null);
          setChatMessages((current)=>[...current,{role:"assistant",content:event.text||"Bạn vui lòng bổ sung thông tin về sự cố."}]);
          setStatus("needs_input");
          setCurrentStep("AI cần thêm thông tin để phân loại");
          setEvents((current) => [...current, { ...event, kind: "warning", label: "CẦN BỔ SUNG THÔNG TIN", time: new Date().toLocaleTimeString("vi-VN", { hour12: false }) }]);
          finished = true;
          return;
        }
        if (event.type === "result") {
          if(event.result.verified) setSceneActivity(current=>current?{...current,phase:"contained"}:current);
          setResult(event.result);
          setClassification(event.result.classification || null);
          setControlId(event.result.control_id || "");
          setDomain(event.result.classification?.domain || scenarios.find((item) => item.control_id === event.result.control_id)?.domain || "people");
          setChatIncidentId(event.result.incident_id);
          setChatMessages((current)=>[...current,{role:"assistant",content:`${event.result.classification?.matched_control?.control_id || event.result.control_id} · ${event.result.classification?.matched_control?.name || "Điều khoản được đối chiếu"}. ${event.result.activity_assessment?.conclusion || ""} ${event.result.agent_rationale || ""}`.trim()}]);
          setStatus("completed");
          setCurrentStep(event.result.verified ? "Xử lý và xác minh hoàn tất" : "Cần rà soát kết quả");
          setCurrentTool("");
          const completedDomain = event.result.classification?.domain || scenarios.find((item) => item.control_id === event.result.control_id)?.domain;
          if (completedDomain) setVisited((current) => [...new Set([...current, completedDomain])]);
          refresh().catch(() => {});
          finished = true;
          return;
        }
        if (event.type === "error") {
          setError(event.text); setStatus("error"); setCurrentStep("Agent cần xử lý lỗi"); finished = true; return;
        }
        const [kind, label] = PROCESS[event.type] || ["action", "TIẾN TRÌNH AGENT"];
        if (event.room && DOMAINS[event.room]) setRoom(event.room);
        if (event.type === "incident_received") setRoom("hub");
        if (event.type === "tool_call_started") setCurrentTool(event.tool_id || "");
        if (event.type === "tool_call_completed") setCurrentTool(`${event.tool_id || "tool"} ✓`);
        if (event.type === "inventory_checked" || event.type === "tool_call_started") {
          if (event.room && DOMAINS[event.room]) setVisited((current) => [...new Set([...current, event.room])]);
        }
        setCurrentStep(label);
        setEvents((current) => [...current, { ...event, kind, label, time: new Date().toLocaleTimeString("vi-VN", { hour12: false }) }]);
      };
      while (!finished) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
        const frames = buffer.split(/\r?\n\r?\n/);
        buffer = frames.pop() || "";
        for (const frame of frames) {
          const line = frame.split(/\r?\n/).find((part) => part.startsWith("data: "));
          if (line) handleMessage(JSON.parse(line.slice(6)));
          if (finished) break;
        }
        if (done) break;
      }
      if (!finished) throw new Error("Luồng Agent kết thúc trước khi trả kết quả.");
      await reader.cancel().catch(() => {});
    } catch (e) {
      setChatMessages((current)=>[...current,{role:"assistant",content:`Quy trình chưa hoàn tất: ${e.message||"đã xảy ra lỗi"}`}]);
      setError(e.message || "Không chạy được mô phỏng."); setStatus("error"); setCurrentStep("Đã dừng quy trình");
    }
  }

  async function sendFollowup() {
    const message = chatInput.trim();
    if (!chatIncidentId || !message || chatLoading) return;
    setChatInput(""); setChatError(""); setChatLoading(true);
    setChatMessages((current) => [...current, { role: "user", content: message }]);
    try {
      const response = await fetch(`${base}/incidents/${encodeURIComponent(chatIncidentId)}/chat/stream`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, Accept: "text/event-stream", "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `Lỗi HTTP ${response.status}`);
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let finished = false;
      while (!finished) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
        const frames = buffer.split(/\r?\n\r?\n/);
        buffer = frames.pop() || "";
        for (const frame of frames) {
          const line = frame.split(/\r?\n/).find((part) => part.startsWith("data: "));
          if (!line) continue;
          const event = JSON.parse(line.slice(6));
          if (event.type === "chat_response") {
            setChatMessages((current) => [...current, { role: "assistant", content: event.answer }]);
            finished = true;
          } else if (event.type === "error") {
            throw new Error(event.text);
          }
        }
        if (done) break;
      }
      if (!finished) throw new Error("Luồng hội thoại kết thúc trước khi có câu trả lời.");
      await reader.cancel().catch(() => {});
    } catch (e) {
      setChatError(e.message || "Không gửi được câu hỏi.");
    } finally {
      setChatLoading(false);
    }
  }

  async function scanCompanyDevices(chatPrompt = "Quét thiết bị doanh nghiệp và tự kiểm tra USB lạ, phần mềm chưa được phê duyệt, công cụ quản trị trái phép.") {
    if (status === "running" || chatLoading) return;
    const prompt = chatPrompt;
    setError(""); setChatError(""); setResult(null); setClassification(null); setControlId("");
    setChatIncidentId(""); setChatInput(""); setChatMessages([{role:"user",content:prompt}]);
    setEvents([]); setVisited([]); setStatus("running"); setRoom("hub"); setCurrentStep("Agent đang quét telemetry doanh nghiệp");
    setSceneActivity(current=>current?{...current,phase:"agent_check"}:current);
    try {
      const response = await fetch(`${base}/monitor/scan/stream`, {
        method:"POST", headers:{Authorization:`Bearer ${token}`,Accept:"text/event-stream"},
      });
      if (!response.ok) {
        const body = await response.json().catch(()=>({}));
        throw new Error(body.detail||`Lỗi HTTP ${response.status}`);
      }
      const reader=response.body.getReader(); const decoder=new TextDecoder(); let buffer=""; let finished=false;
      while(!finished) {
        const {value,done}=await reader.read();
        buffer+=decoder.decode(value||new Uint8Array(),{stream:!done});
        const frames=buffer.split(/\r?\n\r?\n/); buffer=frames.pop()||"";
        for(const frame of frames) {
          const line=frame.split(/\r?\n/).find(part=>part.startsWith("data: "));
          if(!line) continue;
          const event=JSON.parse(line.slice(6));
          if(event.type==="classification_completed") {
            const found=event.classification||{};
            const visualization=activityVisualization(event.control_id||found.control_id);
            if(visualization) setSceneActivity(current=>current||visualization);
            setClassification(found);
            setControlId(event.control_id||found.control_id||"");
            setDomain(event.domain||found.domain||"people"); setRoom(event.domain||found.domain||"hub");
          }
          if(event.type==="result") {
            const report=event.result; setResult(report);
            if(report.verified) setSceneActivity(current=>current?{...current,phase:"contained"}:current);
            if(report.scan_findings?.length) setSceneActivity(current=>current?{...current,phase:report.verified?"contained":"agent_check"}:current);
            setClassification(report.classification||null);
            setControlId(report.control_id||"");
            setChatIncidentId(report.incident_id||"");
            if(report.classification?.domain) setDomain(report.classification.domain);
            setChatMessages(current=>[...current,{role:"assistant",content:report.scan_summary||"Quét thiết bị đã hoàn tất."}]);
            setStatus("completed"); setCurrentStep("Quét và xử lý telemetry hoàn tất"); setCurrentTool("");
            if(report.classification?.domain) setVisited([report.classification.domain]);
            refresh().catch(()=>{}); finished=true; break;
          }
          if(event.type==="error") {
            setChatMessages(current=>[...current,{role:"assistant",content:event.text}]);
            setError(event.text); setStatus("error"); finished=true; break;
          }
          const [kind,label]=PROCESS[event.type]||["action","TIẾN TRÌNH AGENT"];
          setCurrentStep(label);
          setEvents(current=>[...current,{...event,kind,label,time:new Date().toLocaleTimeString("vi-VN",{hour12:false})}]);
        }
        if(done) break;
      }
      if(!finished) throw new Error("Luồng quét kết thúc trước khi có kết quả.");
      await reader.cancel().catch(()=>{});
    } catch(e) {
      setError(e.message||"Không quét được thiết bị."); setStatus("error");
      setChatMessages(current=>[...current,{role:"assistant",content:`Không hoàn tất được quét: ${e.message||"đã xảy ra lỗi"}`}]);
    }
  }

  async function toggleAutomaticMonitoring() {
    if(status==="running"||chatLoading) return;
    try {
      const action=monitoring.active?"stop":"start";
      const state=await request(`${base}/monitor/auto/${action}`,{method:"POST"});
      setMonitoring(state);
      if(!monitoring.active) setChatMessages(current=>[...current,{role:"assistant",content:"Đã bật giám sát tự động. Agent sẽ rà nhật ký telemetry mỗi 5 giây và tự phân loại, xử lý dấu hiệu mới trong doanh nghiệp mô phỏng."}]);
      else setChatMessages(current=>[...current,{role:"assistant",content:"Đã gửi yêu cầu dừng giám sát tự động."}]);
    } catch(e) {
      setError(e.message||"Không đổi được trạng thái giám sát.");
    }
  }

  async function simulateEmployeeActivity(activityType, label) {
    if (status === "running" || chatLoading) return;
    setError(""); setChatError(""); setResult(null); setClassification(null); setControlId("");
    setChatIncidentId(""); setChatInput(""); setIssueText(""); setEvents([]); setVisited([]); setRoom("hub");
    setStatus("running"); setCurrentStep("Đang ghi nhận hành vi nhân viên giả lập");
    setChatMessages([{role:"user",content:label}]);
    try {
      const response=await fetch(`${base}/monitor/simulate-activity`,{
        method:"POST",headers:{Authorization:`Bearer ${token}`,"Content-Type":"application/json"},
        body:JSON.stringify({activity_type:activityType}),
      });
      const body=await response.json().catch(()=>({}));
      if(!response.ok) throw new Error(body.detail||`Lỗi HTTP ${response.status}`);
      const targetRoom=activityType==="unapproved_usb_inserted"?"hardware":"software";
      setRoom(targetRoom);
      setSceneActivity({type:activityType,phase:"employee_action",employee_id:body.employee_id,asset_id:body.host_asset_id||body.asset_id,accessory_id:body.host_asset_id?body.asset_id:null,observed_at:body.observed_at});
      const employee=employees.find(item=>item.employee_id===body.employee_id);
      const nextStep=monitoring.active?"Giám sát tự động đang bật; Agent sẽ phát hiện và xử lý trong vài giây.":"Bây giờ hãy bấm “Quét thiết bị” để Agent tự phát hiện và xử lý.";
      const message=`Đã ghi nhật ký giả lập: ${employee?.display_name||body.employee_id} (${body.employee_id}) · ${body.summary} Thời điểm: ${new Date(body.observed_at).toLocaleString("vi-VN")}. ${nextStep}`;
      setChatMessages(current=>[...current,{role:"assistant",content:message}]);
      setEvents([{type:"activity_simulated",text:body.summary,label:"TẠO NHẬT KÝ HÀNH VI MÔ PHỎNG",kind:"action",time:new Date().toLocaleTimeString("vi-VN",{hour12:false}),activity:body}]);
      setStatus("idle"); setCurrentStep("Đã ghi nhận hoạt động mô phỏng");
    } catch(e) {
      setStatus("error"); setError(e.message||"Không tạo được hành vi mô phỏng.");
      setChatMessages(current=>[...current,{role:"assistant",content:`Không tạo được tình huống: ${e.message||"đã xảy ra lỗi"}`}]);
    }
  }

  async function runNextCoverageDrill() {
    if(status==="running"||chatLoading||drillLoading) return;
    const prompt="Chạy diễn tập doanh nghiệp kế tiếp. AI tự chọn tình huống còn thiếu trong bộ 56 điều khoản, không yêu cầu tôi chọn điều khoản.";
    setDrillLoading(true); setError(""); setChatError(""); setChatInput(""); setChatIncidentId("");
    setResult(null); setClassification(null); setControlId(""); setEvents([]); setVisited([]); setSceneActivity(null); setRoom("hub");
    setChatMessages([{role:"user",content:prompt}]);
    try {
      const activity=await request(`${base}/monitor/drill/next`,{method:"POST"});
      if(monitoring.active) {
        setChatMessages(current=>[...current,{role:"assistant",content:`Đã tạo sự kiện diễn tập giả lập trên ${activity.asset_name}, có nhân sự ${activity.employee_id} thuộc ${activity.department}. Giám sát tự động đang bật và sẽ nhận diện, phân loại, xử lý sự kiện này.`}]);
      } else {
        await scanCompanyDevices(prompt);
      }
    } catch(e) {
      setError(e.message||"Không tạo được lượt diễn tập.");
      setChatMessages(current=>[...current,{role:"assistant",content:`Không chạy được diễn tập: ${e.message||"đã xảy ra lỗi"}`}]);
    } finally {
      setDrillLoading(false);
    }
  }

  function downloadCoverageReport() {
    const rows=metrics?.control_coverage||[];
    if(!rows.length) return;
    const generatedAt=new Date().toISOString();
    const csvCell=(value)=>{
      let text=String(value??"");
      if(/^[=+@\-]/.test(text)) text=`'${text}`;
      return `"${text.replaceAll('"','""')}"`;
    };
    const headers=["Thời điểm xuất (UTC)","Phạm vi","Nhóm","Mã kiểm soát","Tên tình huống","Trạng thái","Số lượt chạy","Lượt xác minh đạt","Lượt cần rà soát","Lần chạy gần nhất","Nguồn dữ liệu"];
    const data=rows.map(item=>[
      generatedAt,"56 tình huống ISO 27001",DOMAINS[item.domain]?.label||item.domain,item.control_id,item.control_name,
      item.status==="verified"?"Đã xác minh":item.status==="needs_review"?"Cần rà soát":"Chưa chạy",
      item.incident_count,item.verified_incidents,item.needs_review,item.last_run_at||"Chưa có","Dữ liệu lab giả lập",
    ]);
    const csv="\uFEFF"+[headers,...data].map(row=>row.map(csvCell).join(",")).join("\r\n");
    const url=URL.createObjectURL(new Blob([csv],{type:"text/csv;charset=utf-8"}));
    const link=document.createElement("a");
    link.href=url;
    link.download=`bao-cao-do-bao-phu-56-${generatedAt.slice(0,10)}.csv`;
    document.body.appendChild(link); link.click(); link.remove(); URL.revokeObjectURL(url);
  }

  async function openHistoryIncident(item) {
    setControlId(item.control_id);
    setDomain(scenarios.find((scenario) => scenario.control_id === item.control_id)?.domain || "people");
    setResult({...item,event:item.event?.reported_event||item.event,activity_assessment:item.event?.device_activity_review,classification:item.event?.ai_classification});
    setClassification(item.event?.ai_classification||null);
    setIssueText(item.event?.reported_event||"");
    setChatIncidentId(item.incident_id);
    setChatInput("");
    setChatMessages([]);
    setChatError("");
    try {
      const messages = await request(`${base}/incidents/${encodeURIComponent(item.incident_id)}/chat`);
      setChatMessages(messages.map(({role,content})=>({role,content})));
    } catch {
      setChatMessages([{role:"user",content:item.event?.reported_event||item.title},{role:"assistant",content:item.agent_rationale}]);
    }
  }

  function startNewChat() {
    if (status === "running" || chatLoading) return;
    setChatMessages([]); setChatInput(""); setIssueText(""); setChatIncidentId("");
    setChatError(""); setError(""); setResult(null); setClassification(null); setControlId("");
    setEvents([]); setVisited([]); setSceneActivity(null); setStatus("idle"); setRoom("hub"); setCurrentStep(""); setCurrentTool("");
  }

  const activeArea = selected ? DOMAINS[selected.domain]?.label : "";

  if (loading) return <div className="flex min-h-screen items-center justify-center bg-[#101827] text-slate-200"><Loader2 className="mr-3 animate-spin"/>Đang nạp doanh nghiệp 3D…</div>;

  return <main className="min-h-screen bg-[#101827] px-3 pb-8 pt-20 text-slate-100 sm:px-5">
    <style>{`@keyframes labBob{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}@keyframes labPulse{0%,100%{opacity:.25}50%{opacity:.75}}@keyframes labSpin{to{transform:rotate(360deg)}}.lab-agent-float{animation:labBob 1.9s ease-in-out infinite}.lab-pulse{animation:labPulse 1.5s ease-in-out infinite}.lab-spin{transform-box:fill-box;transform-origin:center;animation:labSpin 4s linear infinite}.lab-target{animation:labPulse .9s ease-in-out infinite}@media(prefers-reduced-motion:reduce){.lab-agent-float,.lab-pulse,.lab-spin,.lab-target{animation:none}}`}</style>
    <div className="mx-auto max-w-[1900px]">
      <header className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3"><div className="rounded-2xl bg-[#ff9457] p-3"><Bot size={24}/></div><div><h1 className="text-lg font-black sm:text-xl">ISO ENTERPRISE LAB · MÔ PHỎNG 3D</h1><p className="text-xs text-slate-400">Lấy con người làm trọng tâm; phần cứng và phần mềm là tài sản liên quan</p></div></div>
        <div className={`flex items-center gap-2 rounded-full border border-white/10 px-4 py-2 text-xs font-bold ${status === "running" ? "bg-orange-300/10 text-orange-200" : status === "completed" ? "bg-emerald-300/10 text-emerald-200" : status === "needs_input" ? "bg-amber-300/10 text-amber-200" : "bg-white/5 text-slate-300"}`}><span className={`h-2 w-2 rounded-full ${status === "running" ? "animate-pulse bg-orange-300" : status === "completed" ? "bg-emerald-300" : status === "needs_input" ? "bg-amber-300" : "bg-slate-500"}`}/>{status === "running" ? "AI ĐANG PHÂN TÍCH" : status === "completed" ? "MÔ PHỎNG HOÀN TẤT" : status === "needs_input" ? "CẦN MÔ TẢ RÕ HƠN" : status === "error" ? "CẦN KIỂM TRA" : "SẴN SÀNG NHẬN MÔ TẢ"}</div>
      </header>

      <section className="mb-4 grid gap-3 rounded-3xl border border-[#ffb777]/25 bg-gradient-to-r from-[#392b29] via-[#282536] to-[#172337] p-4 sm:grid-cols-[auto_1fr_auto] sm:items-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#ffb777]/15 text-[#ffca91]"><Users size={24}/></div>
        <div><div className="text-xs font-black uppercase tracking-wider text-[#ffca91]">Trọng tâm chuyên ngành · Con người</div><p className="mt-1 text-xs leading-5 text-slate-300">Agent đối chiếu nhân sự, vai trò, phòng ban và sự kiện trước khi quyết định quy trình. Thiết bị và ứng dụng chỉ là ngữ cảnh liên quan trong cùng doanh nghiệp.</p></div>
        <div className="rounded-xl border border-white/10 bg-black/15 px-3 py-2 text-center"><div className="text-lg font-black text-[#ffca91]">{counts.people||0} / {scenarios.length||56}</div><div className="text-[9px] text-slate-400">kiểm soát trực tiếp về nhân sự</div></div>
      </section>

      <section className="mb-4 grid gap-2 sm:grid-cols-3" aria-label="Trạng thái sẵn sàng của lab">
        {[
          {label:"API và PostgreSQL",ok:readiness?.database?.status==="ready",detail:readiness?.database?.status==="ready"?`${readiness.database.people} nhân sự · ${readiness.database.assets} tài sản lab`:"Chưa kiểm tra được kết nối"},
          {label:"Bộ mô phỏng ISO",ok:readiness?.scenario_catalog?.status==="ready",detail:`${readiness?.scenario_catalog?.controls||0}/56 tình huống sẵn sàng`},
          {label:"Mô hình AI",ok:readiness?.ollama?.status==="ready",detail:readiness?.ollama?.status==="ready"?`${readiness.ollama.configured_model} · AI trực tuyến`:readiness?.ollama?`Đang dùng fallback · cần Ollama ${readiness.ollama.configured_model}`:"Đang kiểm tra Ollama…"},
        ].map(item=><div key={item.label} className={`rounded-xl border px-3 py-2 ${item.ok?"border-emerald-300/15 bg-emerald-300/5":"border-amber-300/15 bg-amber-300/5"}`}><div className={`flex items-center gap-2 text-[9px] font-black uppercase tracking-wider ${item.ok?"text-emerald-200":"text-amber-200"}`}><span className={`h-1.5 w-1.5 rounded-full ${item.ok?"bg-emerald-300":"bg-amber-300"}`}/>{item.label} · {item.ok?"SẴN SÀNG":readiness?"CHÚ Ý":"ĐANG KIỂM TRA"}</div><div className="mt-1 truncate text-[9px] text-slate-400">{item.detail}</div></div>)}
      </section>

      <section className="mb-4 overflow-hidden rounded-3xl border border-white/10 bg-[#172337] shadow-xl">
        <div className="flex items-center justify-between border-b border-white/10 px-4 py-3 sm:px-5"><div className="flex items-center gap-3"><div className="rounded-xl bg-[#ff9457]/15 p-2 text-[#ffb777]"><Bot size={20}/></div><div><h2 className="text-sm font-black text-white">Chat với AI Agent</h2><p className="text-[10px] text-slate-400">Mô tả tình huống hoặc để Agent tự giám sát thiết bị</p></div></div><div className="flex flex-wrap items-center justify-end gap-2">{chatMessages.length>0&&<button onClick={startNewChat} disabled={status==="running"||chatLoading} className="rounded-lg border border-white/10 px-2.5 py-1.5 text-[9px] font-bold text-slate-300 hover:bg-white/5 disabled:opacity-40">Chat mới</button>}<button onClick={toggleAutomaticMonitoring} disabled={status==="running"||chatLoading} className={`rounded-lg border px-3 py-1.5 text-[9px] font-black disabled:opacity-40 ${monitoring.active?"border-emerald-300/30 bg-emerald-300/10 text-emerald-200":"border-white/10 text-slate-300 hover:bg-white/5"}`}>{monitoring.active?"Tắt giám sát tự động":"Bật giám sát tự động"}</button><button onClick={scanCompanyDevices} disabled={status==="running"||chatLoading} className="rounded-lg border border-[#78d7e9]/30 bg-[#78d7e9]/10 px-3 py-1.5 text-[9px] font-black text-[#a6eaf2] hover:bg-[#78d7e9]/20 disabled:opacity-40">Quét ngay</button><span className={`flex items-center gap-2 rounded-full px-3 py-1.5 text-[9px] font-bold ${status==="running"||chatLoading?"bg-amber-300/10 text-amber-200":"bg-emerald-300/10 text-emerald-200"}`}><span className={`h-1.5 w-1.5 rounded-full ${status==="running"||chatLoading?"animate-pulse bg-amber-300":"bg-emerald-300"}`}/>{status==="running"?"ĐANG PHÂN TÍCH":chatLoading?"ĐANG TRẢ LỜI":monitoring.active?"ĐANG GIÁM SÁT":"SẴN SÀNG"}</span></div></div>
        <div className="scroll-soft flex h-64 flex-col gap-3 overflow-y-auto bg-[#101827]/70 p-4 sm:h-72 sm:px-6" aria-live="polite">
          {chatMessages.length===0&&<div className="my-auto flex gap-3"><div className="mt-1 rounded-xl bg-[#ff9457]/15 p-2 text-[#ffb777]"><Bot size={17}/></div><div className="max-w-[85%] rounded-2xl rounded-tl-sm border border-white/5 bg-[#172337] px-4 py-3 text-xs leading-5 text-slate-200"><div className="mb-1 text-[9px] font-black uppercase tracking-wider text-[#ffca91]">AI Agent · Việt Tín Logistics</div>Hãy kể vấn đề bằng lời của bạn. Tôi sẽ kiểm tra hồ sơ nhân sự, tài sản và nhật ký liên quan trước; sau khi phân tích xong mới kết luận điều khoản nào có thể bị vi phạm và đề xuất cách xử lý. Bạn cũng có thể bấm <b>Quét thiết bị</b> để tôi tìm dấu hiệu USB lạ, phần mềm chưa duyệt hoặc công cụ quản trị trái phép.</div></div>}
          {chatMessages.map((item,index)=><div key={`${item.role}-${index}`} className={`flex ${item.role==="user"?"justify-end":"justify-start"}`}><div className={`max-w-[88%] rounded-2xl px-4 py-3 text-xs leading-5 ${item.role==="user"?"rounded-br-sm bg-[#ff9457] text-[#251b17]":"rounded-tl-sm border border-white/5 bg-[#172337] text-slate-200"}`}><div className={`mb-1 text-[9px] font-black uppercase tracking-wider ${item.role==="user"?"text-[#55301f]":"text-[#ffca91]"}`}>{item.role==="user"?"Bạn":"AI Agent"}</div><div className="whitespace-pre-wrap">{item.content}</div></div></div>)}
          {(status==="running"||drillLoading)&&<div className="flex items-center gap-2 text-[10px] text-sky-200"><Loader2 size={14} className="animate-spin"/>{drillLoading?"Đang tạo và phân tích diễn tập 56 điều khoản…":currentStep||"AI đang phân tích sự cố…"}</div>}{chatLoading&&<div className="flex items-center gap-2 text-[10px] text-sky-200"><Loader2 size={14} className="animate-spin"/>AI đang xem lại hồ sơ…</div>}<div ref={chatEnd}/>
        </div>
        <div className="border-t border-white/10 p-3 sm:p-4"><div className="flex items-end gap-2 rounded-2xl border border-white/10 bg-[#101827] p-2 focus-within:border-[#ffb777]/50"><textarea value={chatInput} onChange={(e)=>setChatInput(e.target.value)} onKeyDown={(e)=>{if(e.key==="Enter"&&(e.ctrlKey||e.metaKey)){e.preventDefault();chatIncidentId?sendFollowup():startSimulation();}}} disabled={status==="running"||chatLoading||drillLoading} maxLength={chatIncidentId?1000:2000} rows={2} placeholder={chatIncidentId?"Hỏi tiếp về sự cố này…":"Nhập tin nhắn cho AI Agent… (Ctrl + Enter để gửi)"} className="max-h-32 min-h-12 min-w-0 flex-1 resize-y bg-transparent px-2 py-2 text-sm leading-5 text-white outline-none placeholder:text-slate-500 disabled:opacity-60"/><button onClick={()=>chatIncidentId?sendFollowup():startSimulation()} disabled={!chatInput.trim()||status==="running"||chatLoading||drillLoading} className="flex h-10 shrink-0 items-center gap-2 rounded-xl bg-[#ff9457] px-4 text-xs font-black text-[#251b17] hover:bg-[#ffad77] disabled:cursor-not-allowed disabled:opacity-40"><Send size={15}/><span>Gửi</span></button></div><div className="mt-2 flex flex-wrap items-center gap-2 px-1"><span className="mr-1 text-[9px] font-bold uppercase tracking-wider text-slate-500">Tạo tín hiệu để Agent tự phát hiện:</span><button onClick={()=>simulateEmployeeActivity("unapproved_usb_inserted","Mô phỏng: nhân viên cắm USB lạ vào máy tính doanh nghiệp") } disabled={status==="running"||chatLoading||drillLoading} className="rounded-full border border-white/10 px-3 py-1.5 text-[9px] font-bold text-slate-300 hover:border-amber-200/30 hover:text-amber-100 disabled:opacity-40">Nhân viên cắm USB lạ</button><button onClick={()=>simulateEmployeeActivity("unapproved_software_installed","Mô phỏng: nhân viên tải và cài phần mềm lạ trên hệ thống doanh nghiệp") } disabled={status==="running"||chatLoading||drillLoading} className="rounded-full border border-white/10 px-3 py-1.5 text-[9px] font-bold text-slate-300 hover:border-violet-200/30 hover:text-violet-100 disabled:opacity-40">Nhân viên cài app lạ</button></div><div className="mt-2 flex flex-wrap justify-between gap-2 px-1 text-[9px] text-slate-500"><span>Điều khoản chỉ được kết luận sau khi Agent kiểm tra và phân tích.</span><span>{chatInput.length}/{chatIncidentId?1000:2000} ký tự</span></div>{chatError&&<p className="mt-2 text-xs text-rose-300">{chatError}</p>}</div>
      </section>

      {error&&<div role="alert" className="mb-4 flex items-center gap-2 rounded-xl border border-rose-300/20 bg-rose-400/10 p-3 text-sm text-rose-100"><AlertTriangle size={17}/>{error}</div>}

      <section className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
        {[{label:"Phạm vi nghiên cứu",value:`${scenarios.length}/56 kiểm soát`,Icon:Shield},{label:"Nhân sự giả lập",value:`${employees.length} hồ sơ`,Icon:Users},{label:"Đã mô phỏng",value:`${metrics?.total_incidents||0} lượt`,Icon:Activity},{label:"Tỷ lệ xác minh",value:`${Math.round((metrics?.verification_rate||0)*100)}%`,Icon:CheckCircle2}].map((item)=><div key={item.label} className="flex items-center gap-3 rounded-2xl border border-white/10 bg-[#172337] p-3 sm:p-4"><item.Icon size={20} className="text-[#ffb777]"/><div><div className="text-[10px] text-slate-400">{item.label}</div><div className="mt-1 text-sm font-black">{item.value}</div></div></div>)}
      </section>

      <section className="mb-4 rounded-3xl border border-white/10 bg-[#172337] p-4"><div className="mb-3 flex flex-wrap items-end justify-between gap-2"><div><h2 className="text-xs font-black uppercase tracking-wider text-slate-200">Số liệu thực nghiệm theo khu vực</h2><p className="mt-1 text-[10px] text-slate-500">Coverage là số kiểm soát đã chạy ít nhất một lần; xác minh là kết quả mô phỏng khớp trạng thái mong đợi.</p></div><span className="text-[9px] text-slate-500">{metrics?.controls_tested||0}/{metrics?.scope_controls||56} kiểm soát đã được thử</span></div><div className="grid gap-2 md:grid-cols-3">{Object.entries(DOMAINS).map(([key, area])=>{const data=metrics?.by_domain?.[key]||{};const Icon=area.icon;return <div key={key} className="rounded-xl border border-white/5 bg-black/15 p-3"><div className="flex items-center gap-2 text-xs font-bold" style={{color:area.color}}><Icon size={14}/>{area.label}</div><div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[10px] text-slate-400"><span>{data.controls_tested||0}/{counts[key]||0} kiểm soát</span><span>{data.incidents||0} lượt chạy</span><span>{data.verified||0} đã xác minh</span></div></div>})}</div><div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 border-t border-white/5 pt-3 text-[10px] text-slate-400"><span>Quyết định từ Ollama: <b className="text-sky-200">{metrics?.agent_model_incidents||0}</b></span><span>Policy fallback: <b className="text-amber-200">{metrics?.policy_fallback_incidents||0}</b></span><span>Lượt gọi tool: <b className="text-violet-200">{metrics?.action_count||0}</b></span></div><p className="mt-3 text-[9px] text-slate-600">Chỉ số đánh giá đầu ra của lab giả lập, không phải kết luận chứng nhận ISO.</p></section>

      <details className="mb-4 rounded-3xl border border-white/10 bg-[#172337] p-4">
        <summary className="flex cursor-pointer list-none flex-wrap items-center justify-between gap-2 text-xs font-black text-slate-200">
          <span>MA TRẬN ĐỘ BAO PHỦ 56 TÌNH HUỐNG</span>
          <span className="text-[10px] font-medium text-slate-500">Chỉ xem tiến độ · AI tự chọn tình huống diễn tập</span>
        </summary>
        <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
          <p className="text-[9px] text-slate-500">Kiểm thử độ bao phủ độc lập với luồng sự cố do bạn mô tả. Xuất báo cáo CSV để mở bằng Excel.</p>
          <button onClick={runNextCoverageDrill} disabled={status==="running"||chatLoading||drillLoading} className="inline-flex items-center gap-2 rounded-lg border border-[#ffb777]/20 bg-[#ffb777]/5 px-3 py-2 text-[9px] font-bold text-[#ffcfaa] hover:bg-[#ffb777]/10 disabled:cursor-not-allowed disabled:opacity-40">{drillLoading?<Loader2 size={13} className="animate-spin"/>:<Activity size={13}/>}Kiểm thử tình huống kế tiếp · {metrics?.controls_tested||0}/56</button>
          <button onClick={downloadCoverageReport} disabled={!metrics?.control_coverage?.length} className="inline-flex items-center gap-2 rounded-lg border border-sky-200/15 bg-sky-200/5 px-3 py-2 text-[9px] font-bold text-sky-100 hover:bg-sky-200/10 disabled:cursor-not-allowed disabled:opacity-40"><Download size={13}/>Tải báo cáo CSV</button>
        </div>
        <div className="mt-3 flex flex-wrap gap-3 border-y border-white/5 py-2 text-[9px] text-slate-400">
          <span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-slate-500"/>Chưa chạy</span>
          <span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-emerald-400"/>Đã chạy, xác minh đạt</span>
          <span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-amber-400"/>Cần rà soát</span>
        </div>
        <div className="mt-3 grid gap-4 lg:grid-cols-3">
          {Object.entries(DOMAINS).map(([key, area])=>{
            const items=(metrics?.control_coverage||[]).filter(item=>item.domain===key);
            const Icon=area.icon;
            return <section key={key}>
              <h3 className="mb-2 flex items-center gap-2 text-[10px] font-black uppercase tracking-wider" style={{color:area.color}}><Icon size={13}/>{area.label}<span className="text-slate-600">{items.filter(item=>item.status!=="not_tested").length}/{items.length}</span></h3>
              <div className="max-h-64 space-y-1 overflow-y-auto pr-1">
                {items.map(item=>{
                  const dot=item.status==="verified"?"bg-emerald-400":item.status==="needs_review"?"bg-amber-400":"bg-slate-600";
                  const label=item.status==="verified"?"Đạt":item.status==="needs_review"?"Rà soát":"Chưa chạy";
                  return <div key={item.control_id} className="flex items-center gap-2 rounded-lg border border-white/5 bg-black/10 px-2 py-1.5" title={`${item.control_id} · ${item.control_name}`}>
                    <i className={`h-2 w-2 shrink-0 rounded-full ${dot}`}/>
                    <span className="w-12 shrink-0 font-mono text-[9px] text-slate-300">{item.control_id}</span>
                    <span className="min-w-0 flex-1 truncate text-[9px] text-slate-500">{item.control_name}</span>
                    <span className="shrink-0 text-[8px] text-slate-600">{item.incident_count?`${item.verified_incidents}/${item.incident_count}`:label}</span>
                  </div>;
                })}
              </div>
            </section>;
          })}
        </div>
      </details>

      <section className="grid items-start gap-4 xl:grid-cols-[minmax(0,1fr)_335px]">
        <div className="space-y-4">
          <Suspense fallback={<div className="flex h-[500px] items-center justify-center rounded-[30px] border border-white/10 bg-[#172337] text-sm text-slate-300 md:h-[580px]"><Loader2 className="mr-3 animate-spin"/>Nạp mô hình doanh nghiệp 3D…</div>}><EnterpriseScene3D room={room} visited={visited} selected={selected} working={status==="running"} resolved={status==="completed"&&Boolean(result?.verified)} currentTool={currentTool} currentStep={currentStep} activity={sceneActivity}/></Suspense>
          {selected&&<div className="rounded-2xl border border-[#ffb777]/20 bg-[#172337] p-4"><div className="flex flex-wrap items-center gap-2"><span className="rounded-md bg-white/10 px-2 py-1 font-mono text-xs font-bold text-sky-200">AI chọn {selected.control_id}</span><span className="text-xs font-bold text-slate-400">{activeArea} · {selected.department}</span>{classification?.confidence!=null&&<span className="rounded-full bg-sky-300/10 px-2.5 py-1 text-[10px] text-sky-200">Độ tin cậy {Math.round(classification.confidence*100)}%</span>}</div><h2 className="mt-2 font-black">{selected.control_name}</h2><p className="mt-1 text-xs leading-5 text-slate-400">Điều khoản yêu cầu: {selected.objective}</p><div className="mt-3 rounded-xl border border-white/5 bg-black/15 p-3"><div className="text-[9px] font-black uppercase tracking-wider text-slate-500">Mô tả bạn đưa</div><p className="mt-1 text-sm leading-6 text-slate-200">{classification?.original_issue||result?.event||issueText||selected.event}</p></div><p className="mt-3 text-xs leading-5 text-[#ffca91]">Kết luận phân loại: {classification?.rationale||"AI đã đối chiếu sự cố với mục tiêu điều khoản."}</p><div className="mt-3 flex flex-wrap items-center gap-2 rounded-xl border border-[#ffb777]/15 bg-[#ffb777]/5 px-3 py-2"><Users size={15} className="text-[#ffca91]"/><span className="text-xs font-bold text-[#ffca91]">{selectedEmployee?.employee_id||selected.human_context?.employee_id||"Nhân sự phụ trách"}</span><span className="text-xs text-slate-300">· {selectedEmployee?.job_title||selected.human_context?.role||"Nhân viên liên quan"}</span><span className="text-[10px] text-slate-500">· {selected.human_context?.relationship === "affected_employee" ? "người trong tình huống" : "đầu mối phòng ban"}</span><span className="text-xs text-slate-500">· Tài sản liên quan: {selected.target.name} ({selected.target.asset_id})</span></div><div className="mt-3 rounded-xl bg-black/20 p-3 text-xs"><div className="text-slate-500">Trạng thái tài sản lab</div><div className="mt-1 text-slate-200">{formatState(selected.current_state)}</div></div></div>}
          {selectedEmployee&&<div className="rounded-2xl border border-[#ffb777]/25 bg-gradient-to-br from-[#302b2e] to-[#172337] p-4"><div className="flex flex-wrap items-start justify-between gap-3"><div className="flex items-center gap-3"><div className="rounded-xl bg-[#ffb777]/15 p-2.5 text-[#ffca91]"><Users size={20}/></div><div><div className="text-[10px] font-black uppercase tracking-wider text-[#ffca91]">Hồ sơ nhân sự · dữ liệu giả lập</div><h3 className="mt-1 text-sm font-black">{selectedEmployee.display_name} · {selectedEmployee.employee_id}</h3><p className="mt-1 text-xs text-slate-400">{selectedEmployee.job_title} · {selectedEmployee.department}</p></div></div><div className="flex gap-2 text-[9px]"><span className="rounded-full bg-white/5 px-2.5 py-1 text-slate-300">Nhân sự: {selectedEmployee.employment_status}</span><span className="rounded-full bg-white/5 px-2.5 py-1 text-slate-300">Tài khoản: {selectedEmployee.account_status}</span></div></div><div className="mt-4 border-t border-white/10 pt-3"><div className="mb-2 text-[10px] font-bold text-slate-400">THIẾT BỊ / ỨNG DỤNG CÓ LIÊN KẾT ({selectedEmployee.linked_assets?.length||0})</div>{selectedEmployee.linked_assets?.length?<div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">{selectedEmployee.linked_assets.map((asset)=><div key={`${asset.asset_id}-${asset.relationship}`} className="rounded-xl border border-white/5 bg-black/15 p-2.5"><div className="flex items-center justify-between gap-2"><span className="truncate text-xs font-bold text-slate-200">{asset.name}</span><span className="shrink-0 rounded bg-white/5 px-1.5 py-0.5 text-[8px] uppercase text-slate-500">{asset.type}</span></div><div className="mt-1 font-mono text-[9px] text-slate-500">{asset.asset_id} · {asset.relationship === "affected_employee" ? "đối tượng sự cố" : "nhân sự phụ trách"}</div></div>)}</div>:<p className="text-xs text-slate-500">Chưa có thiết bị/ứng dụng được gán trong kịch bản này.</p>}</div></div>}
          {result&&<div className="rounded-2xl border border-emerald-300/20 bg-[#14251f] p-4"><div className="flex flex-wrap items-center justify-between gap-2"><h3 className="flex items-center gap-2 font-black"><CheckCircle2 size={18} className="text-emerald-300"/>{result.scan_only?"Kết quả quét thiết bị":"Báo cáo sau xử lý"}</h3><span className="rounded-full bg-emerald-300/10 px-3 py-1 text-xs font-bold text-emerald-200">{result.scan_only&&result.status==="NO_FINDINGS"?"KHÔNG CÓ SỰ CỐ MỚI":result.verified||result.status==="RESOLVED"?"ĐÃ XÁC MINH":"CẦN RÀ SOÁT"}</span></div><p className="mt-2 text-sm leading-6 text-slate-300">{result.agent_rationale||result.scan_summary}</p>{result.scan_findings?.length>0&&<div className="mt-3 space-y-2">{result.scan_findings.map((finding,index)=><div key={`${finding.asset_id}-${finding.event_type}-${index}`} className="rounded-xl border border-amber-200/15 bg-amber-200/5 p-3"><div className="flex flex-wrap items-center gap-2 text-xs font-bold text-amber-100"><span>{finding.control_id} · {finding.control_name}</span><span className="rounded bg-white/5 px-2 py-0.5 text-[9px]">{finding.asset_id}</span></div><p className="mt-1 text-xs text-slate-300">{finding.summary}</p><p className="mt-1 text-[10px] text-slate-500">{finding.employee_id?`Nhân sự liên quan ${finding.employee_id} · `:""}{new Date(finding.observed_at).toLocaleString("vi-VN")} · dữ liệu giả lập</p></div>)}</div>}{result.activity_assessment&&<div className="mt-3 rounded-xl border border-[#78d7e9]/20 bg-[#78d7e9]/5 p-3"><div className="text-[10px] font-black uppercase tracking-wider text-[#9be5f0]">Kết quả kiểm tra thiết bị {result.activity_assessment.reported_at?`sau ${new Date(result.activity_assessment.reported_at).toLocaleTimeString("vi-VN",{hour:"2-digit",minute:"2-digit"})}`:"· chưa có mốc giờ"}</div><p className="mt-1 text-xs leading-5 text-slate-200">{result.activity_assessment.conclusion}</p>{result.activity_assessment.limitation&&<p className="mt-1 text-[9px] text-slate-500">Giới hạn: {result.activity_assessment.limitation}</p>}<div className="mt-2 space-y-1">{result.activity_assessment.events_after_reported_time?.map((event)=><div key={`${event.observed_at}-${event.event_type}`} className="flex flex-wrap gap-x-2 text-[9px] text-slate-400"><span className="font-mono text-[#9be5f0]">{new Date(event.observed_at).toLocaleTimeString("vi-VN",{hour:"2-digit",minute:"2-digit"})}</span><span className="font-mono">{event.event_type}</span><span>{event.summary}</span></div>)}</div></div>}<div className="mt-3 grid gap-2 sm:grid-cols-2">{result.actions?.map((action,i)=><div key={`${action.action_id||action.tool_id}-${i}`} className="rounded-xl border border-white/5 bg-black/15 p-3"><div className="text-sm font-bold">{action.label}</div><div className="mt-1 text-xs text-emerald-200">{action.status} · {action.target_asset_id}</div><div className="mt-2 text-[10px] text-slate-500">Trước: {formatState(action.before_state)}</div><div className="mt-1 text-[10px] text-slate-400">Sau: {formatState(action.after_state)}</div>{action.person_before_state&&<details className="mt-3 border-t border-white/5 pt-2"><summary className="cursor-pointer text-[10px] font-bold text-[#ffca91]">Xem trạng thái nhân sự trước / sau</summary><div className="mt-2 text-[10px] text-slate-500">Nhân sự trước: {formatState(action.person_before_state)}</div><div className="mt-1 text-[10px] text-slate-300">Nhân sự sau: {formatState(action.person_after_state)}</div></details>}</div>)}</div>{result.evidence_id&&<div className="mt-3 break-all rounded-xl bg-black/20 p-3 font-mono text-[10px] text-slate-500">Biên nhận: {result.evidence_id}{result.sha256_hash&&<><br/>SHA-256: {result.sha256_hash}</>}</div>}</div>}
        </div>

        <aside className="space-y-4">
          <div className="flex h-[440px] flex-col rounded-3xl border border-white/10 bg-[#172337] p-4 xl:h-[580px]"><div className="flex items-center justify-between border-b border-white/10 pb-3"><div className="flex items-center gap-2"><Terminal size={18} className="text-violet-300"/><div><h2 className="text-sm font-black">QUY TRÌNH KIỂM TRA</h2><p className="text-[10px] text-slate-500">Live trace từ backend Agent</p></div></div><Activity size={16} className={status==="running"?"animate-pulse text-emerald-300":"text-slate-500"}/></div>
            <div className="scroll-soft mt-3 min-h-0 flex-1 space-y-3 overflow-y-auto pr-1" aria-live="polite">{events.length===0?<div className="flex h-full flex-col items-center justify-center gap-3 text-center text-slate-500"><Bot size={32}/><p className="text-xs leading-5">Mô tả sự cố ở khung trên.<br/>AI sẽ phân loại, tra thông tin liên quan và đề xuất xử lý.</p></div>:events.map((event,i)=>{const style=LOG_STYLE[event.kind]||LOG_STYLE.action;return <div key={`${event.type}-${i}`} className={`border-l-2 pl-3 ${style.split(" ").at(-1)}`}><div className={`flex items-center gap-2 text-[9px] font-black ${style.split(" ")[0]}`}><span>{event.label}</span><span className="ml-auto text-slate-600">{event.time}</span></div><p className="mt-1 text-xs leading-5 text-slate-300">{event.text}</p>{event.type==="telemetry_checked"&&event.activity_assessment?.events_after_reported_time?.map((item)=><p key={`${item.observed_at}-${item.event_type}`} className="mt-1 font-mono text-[9px] text-[#9be5f0]">{new Date(item.observed_at).toLocaleTimeString("vi-VN",{hour:"2-digit",minute:"2-digit"})} · {item.event_type}</p>)}{event.type==="tool_call_completed"&&<><p className="mt-1 break-all font-mono text-[9px] text-slate-500">Tài sản: {formatState(event.after_state)}</p>{event.person_after_state&&<p className="mt-1 break-all font-mono text-[9px] text-[#ffca91]">Nhân sự: {formatState(event.person_after_state)}</p>}</>}</div>})}<div ref={logEnd}/>{status==="running"&&<div className="flex items-center gap-2 text-[10px] text-orange-200"><Loader2 size={13} className="animate-spin"/>Đang chờ bước tiếp theo từ backend…</div>}</div>
            <div className="mt-3 rounded-xl border border-white/5 bg-black/15 p-3 text-[10px] leading-4 text-slate-500">Luồng này hiển thị các bước vận hành (tiếp nhận, kiểm tra, phân tích, gọi tool, xác minh); không hiển thị chain-of-thought nội bộ.</div>
          </div>
          <div className="rounded-3xl border border-white/10 bg-[#172337] p-4"><h2 className="mb-3 text-sm font-black">LỊCH SỬ MÔ PHỎNG</h2>{history.length===0?<p className="text-xs text-slate-500">Chưa có sự cố.</p>:<div className="max-h-48 space-y-2 overflow-y-auto">{history.slice(0,8).map((item)=><button key={item.incident_id} onClick={()=>openHistoryIncident(item)} className="w-full rounded-xl bg-black/15 p-3 text-left hover:bg-white/5"><div className="flex justify-between gap-2"><span className="font-mono text-[10px] text-sky-200">{item.control_id}</span><span className="text-[9px] text-slate-500">{new Date(item.created_at).toLocaleTimeString("vi-VN")}</span></div><div className="mt-1 text-xs font-bold">{item.title}</div></button>)}</div>}</div>
        </aside>
      </section>
      <footer className="mt-5 text-center text-[10px] text-slate-600">Tất cả người, thiết bị, phần mềm và hành động đều là dữ liệu mô phỏng trong PostgreSQL lab.</footer>
    </div>
  </main>;
}
