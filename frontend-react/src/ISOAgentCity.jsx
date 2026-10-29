import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  Activity, AlertTriangle, Bot, BrainCircuit, CheckCircle2, ChevronRight,
  ClipboardCheck, Cpu, Database, FileText, FolderSearch,
  LayoutGrid, Loader2, MessageCircle, Rocket, RotateCcw, Search,
  Send, ShieldCheck, Sparkles, Terminal, Users,
  X, ZoomIn, ZoomOut,
} from "lucide-react";

/**
 * ISO AGENT CITY — giao diện thử nghiệm lấy cảm hứng từ 2 MP4 do người dùng cung cấp.
 * - Auto-Audit gọi FastAPI và thực hiện LangGraph/Ollama trong lab thật.
 * - Không có tính năng tải file bằng chứng; thiếu bằng chứng được ghi nhận.
 * - Phân biệt rõ bằng chứng mô phỏng lab và hồ sơ doanh nghiệp thật.
 * - Có thể hiển thị trong App.jsx SAU lớp xác thực có sẵn.
 * - Các tòa nhà chỉ để xem thông tin; không phải nút bắt đầu kiểm toán.
 */
const EXPERTS = [
  { id: "planner", name: "Chief Audit", title: "Trưởng nhóm kiểm toán", location: "Trung tâm điều hành", mission: "Lập kế hoạch và phân công 56 controls", icon: "🧠", color: "#FDB56C", x: 435, y: 250, area: "management" },
  { id: "collector", name: "Collector", title: "Chuyên gia bằng chứng", location: "Phòng Nhân sự", mission: "Tìm quy trình và thu thập hồ sơ A.6.1", icon: "🔎", color: "#85D8C3", x: 195, y: 367, area: "hr" },
  { id: "evaluator", name: "Evaluator", title: "Chuyên gia ISO 27001", location: "Trung tâm CNTT", mission: "Đối chiếu yêu cầu với bằng chứng", icon: "📋", color: "#A9B9FA", x: 842, y: 371, area: "it" },
  { id: "verifier", name: "Verifier", title: "Chuyên gia xác minh", location: "Phòng Kế toán", mission: "Kiểm tra độ tin cậy và nguồn gốc", icon: "✅", color: "#F8B9D4", x: 520, y: 142, area: "accounting" },
  { id: "risk", name: "Risk Analyst", title: "Chuyên gia rủi ro", location: "Nhà Kho", mission: "Phân tích rủi ro và hành động xử lý", icon: "🛡️", color: "#C1B2FE", x: 635, y: 542, area: "warehouse" },
  { id: "reporter", name: "Reporter", title: "Chuyên gia báo cáo", location: "Trung tâm Dữ liệu", mission: "Tổng hợp báo cáo có trích dẫn", icon: "📊", color: "#FFCE93", x: 224, y: 562, area: "data" },
];

const ROOMS = [
  { id: "hr", title: "Phòng Nhân sự", sub: "A.6 • Con người", x: 64, y: 245, icon: "👥", color: "#85D8C3", tag: "HỒ SƠ NHÂN SỰ" },
  { id: "accounting", title: "Phòng Kế toán", sub: "Kiểm soát truy cập", x: 392, y: 40, icon: "💰", color: "#F8B9D4", tag: "CHỨNG TỪ" },
  { id: "management", title: "Phòng Quản lý", sub: "Điều hành kiểm toán", x: 370, y: 211, icon: "🏛️", color: "#FDB56C", tag: "AUDIT HQ" },
  { id: "it", title: "Trung tâm CNTT", sub: "A.8 • Công nghệ", x: 716, y: 260, icon: "💻", color: "#A9B9FA", tag: "SOC / IT" },
  { id: "warehouse", title: "Nhà Kho", sub: "A.7 • Vật lý", x: 506, y: 431, icon: "📦", color: "#C1B2FE", tag: "TÀI SẢN" },
  { id: "data", title: "Trung tâm Dữ liệu", sub: "Kho evidence & log", x: 98, y: 446, icon: "🗂️", color: "#FFCE93", tag: "EVIDENCE" },
];

const STAGES = [
  { key: "plan", title: "Lập kế hoạch kiểm toán", expert: "planner", room: "management", control: "PHÂN CÔNG" },
  { key: "collect", title: "Thu thập hồ sơ nhân sự A.6.1", expert: "collector", room: "hr", control: "A.6.1" },
  { key: "verify", title: "Kiểm tra nguồn gốc tài liệu", expert: "verifier", room: "accounting", control: "EVIDENCE" },
  { key: "evaluate", title: "Đối chiếu yêu cầu công nghệ", expert: "evaluator", room: "it", control: "A.8" },
  { key: "risk", title: "Phân loại rủi ro vật lý", expert: "risk", room: "warehouse", control: "A.7" },
  { key: "report", title: "Tổng hợp báo cáo mô phỏng", expert: "reporter", room: "data", control: "REPORT" },
];

const AGENT_STOP = Object.fromEntries(EXPERTS.map((e) => [e.id, { x: e.x, y: e.y }]));
const INDICATOR = {
  action: { label: "HÀNH ĐỘNG", color: "#72CBF4" },
  tool: { label: "TOOL EVENT", color: "#C6A7FF" },
  finding: { label: "ĐỐI CHIẾU", color: "#79E2BD" },
  wait: { label: "THIẾU BẰNG CHỨNG", color: "#FFBE78" },
  done: { label: "ĐÃ XỬ LÝ", color: "#9BE6A8" },
};
const timeLabel = () => new Date().toLocaleTimeString("vi-VN", { hour12: false });

function Robot({ x, y, color = "#FFA666", floating = false, size = 1 }) {
  return (
    <g transform={`translate(${x} ${y}) scale(${size})`}>
      <g className={floating ? "iso-agent-float" : ""}>
      <ellipse cx="0" cy="41" rx="25" ry="7" fill="#835952" opacity=".15" />
      <path d="M-11 24 L-7 35 M11 24 L7 35" stroke="#6C8795" strokeWidth="6" strokeLinecap="round" />
      <rect x="-25" y="-8" width="50" height="41" rx="18" fill={color} stroke="#FFF9EE" strokeWidth="4" />
      <path d="M-25 8 L-32 13 M25 8 L32 13" stroke={color} strokeWidth="9" strokeLinecap="round" />
      <rect x="-31" y="-45" width="62" height="48" rx="21" fill="#FFFEF5" stroke={color} strokeWidth="4" />
      <rect x="-23" y="-35" width="46" height="29" rx="12" fill="#3B5666" />
      <ellipse cx="-10" cy="-20" rx="4" ry="5" fill="white" />
      <ellipse cx="10" cy="-20" rx="4" ry="5" fill="white" />
      <path d="M-7 -12 Q0 -7 7 -12" fill="none" stroke="#FFD9A2" strokeWidth="2" strokeLinecap="round" />
      <path d="M0 -45 V-55" stroke="#7B969E" strokeWidth="3" />
      <circle cx="0" cy="-57" r="5" fill="#FFD27E" />
      </g>
    </g>
  );
}

function TinyTree({ x, y, rose = false, scale = 1 }) {
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <ellipse cx="4" cy="8" rx="17" ry="6" fill="#7B9E88" opacity=".19" />
      <path d="M0 6 L0 -24" stroke="#A68B76" strokeWidth="5" />
      <circle cx="-6" cy="-33" r="15" fill={rose ? "#E8B7D1" : "#A4D8B6"} />
      <circle cx="10" cy="-35" r="13" fill={rose ? "#E9C3DB" : "#75C3A1"} />
      <circle cx="0" cy="-48" r="13" fill={rose ? "#F1D5E5" : "#C0E9CA"} />
    </g>
  );
}

function Building({ room, active, visited, theme, onView }) {
  const c = room.color;
  const pale = theme === "garden";
  return (
    <g transform={`translate(${room.x} ${room.y})`} onClick={() => onView(room.id)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onView(room.id); } }} role="button" tabIndex={0} style={{ cursor: "pointer" }} aria-label={`Xem khu vực ${room.title}`}>
      {active && <ellipse cx="115" cy="155" rx="123" ry="46" fill="#FFF5B1" className="iso-room-glow" />}
      <ellipse cx="114" cy="164" rx="108" ry="28" fill={pale ? "#8CA89B" : "#B77F64"} opacity=".19" />
      <polygon points="8,105 110,51 220,106 118,163" fill="#FFF5EA" stroke="#FFFFFF" strokeWidth="3" />
      <polygon points="8,105 118,163 118,179 8,121" fill="#DEB397" />
      <polygon points="118,163 220,106 220,123 118,179" fill="#CBA38B" />
      <polygon points="26,103 111,58 201,105 118,148" fill={pale ? "#FDF8EC" : "#FCE6CD"} />
      <polygon points="26,103 26,46 111,0 111,58" fill="#E6FAF8" fillOpacity=".38" stroke="#FFFFFF" strokeWidth="3" />
      <polygon points="111,0 201,49 201,105 111,58" fill="#E6FAF8" fillOpacity=".31" stroke="#FFFFFF" strokeWidth="3" />
      <path d="M26 73 L111 28 L201 76" fill="none" stroke="#FFFFFF" strokeWidth="2" strokeOpacity=".8" />
      <TinyTree x={48} y={108} rose={pale} scale={.65} />
      <polygon points="80,111 126,88 166,111 122,134" fill="#EFBF8F" />
      <polygon points="80,111 122,134 122,145 80,121" fill="#D39F7F" />
      <polygon points="122,134 166,111 166,121 122,145" fill="#BC8F71" />
      {room.id === "warehouse" ? (
        <g>
          <polygon points="132,96 157,82 180,95 155,109" fill="#F7DCA1" />
          <polygon points="132,96 155,109 155,126 132,114" fill="#CFA66F" />
          <polygon points="155,109 180,95 180,114 155,126" fill="#B98D62" />
        </g>
      ) : (
        <g>
          <rect x="133" y="78" width="28" height="28" rx="3" fill="#7892A4" />
          <rect x="138" y="83" width="18" height="17" rx="2" fill="#A7E8DF" />
        </g>
      )}
      <Robot x={106} y={91} size={.5} color={c} />
      <rect x="25" y="-55" width="175" height="45" rx="17" fill={active ? "#FFFFFF" : "#FFFEF6"} stroke={active ? "#FF965D" : "#E9D9C6"} strokeWidth={active ? "3" : "1.2"} />
      <text x="40" y="-37" fill="#604D50" fontSize="12.5" fontWeight="900">{room.icon} {room.title}</text>
      <text x="40" y="-22" fill="#8D8791" fontSize="10.5">{active ? "Robot đang làm việc..." : visited ? "✓ Đã kiểm tra trong lab" : room.sub}</text>
      <rect x="72" y="158" width="94" height="22" rx="11" fill="#FFF9F1" />
      <text x="119" y="173" fill="#A36E6B" textAnchor="middle" fontSize="10" fontWeight="800">{room.tag}</text>
    </g>
  );
}

function CityMap({ scene, activeExpert, visited, onView, zoom }) {
  const selected = EXPERTS.find((a) => a.id === activeExpert) || EXPERTS[0];
  const planet = scene === "mars";
  return (
    <div className="iso-map-viewport">
      <svg viewBox="0 0 1060 730" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Làng AI Audit dạng isometric với sáu phòng ban và các chuyên gia AI" style={{ width: `${zoom}%`, minWidth: "870px", display: "block", margin: "auto" }}>
        <defs>
          <linearGradient id="iso-ground" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0" stopColor={planet ? "#92869C" : "#D4EEF0"} />
            <stop offset=".45" stopColor={planet ? "#EDB183" : "#E7F4DF"} />
            <stop offset="1" stopColor={planet ? "#FFC991" : "#C9E8CD"} />
          </linearGradient>
          <pattern id="iso-grid" width="40" height="40" patternUnits="userSpaceOnUse" patternTransform="skewX(-28) rotate(12)">
            <path d="M40 0 H0 V40" stroke={planet ? "#AE795D" : "#88C4A7"} strokeOpacity=".16" fill="none" />
          </pattern>
        </defs>
        <rect width="1060" height="730" fill="url(#iso-ground)" />
        {planet ? (
          <>
            <ellipse cx="525" cy="785" rx="778" ry="665" fill="#F4B883" stroke="#FFE3B9" strokeWidth="12" />
            <circle cx="959" cy="92" r="46" fill="#76C5D7" />
            <ellipse cx="942" cy="78" rx="25" ry="10" fill="#AEDFE7" transform="rotate(-23 942 78)" />
            <ellipse cx="851" cy="210" rx="53" ry="22" fill="#D69264" opacity=".26" />
            <ellipse cx="180" cy="640" rx="60" ry="24" fill="#C9805B" opacity=".25" />
          </>
        ) : (
          <>
            <ellipse cx="530" cy="660" rx="780" ry="590" fill="#D8F0D0" stroke="#F5F9E9" strokeWidth="12" />
            <path d="M0 175 Q160 120 325 150 T700 140 T1060 145" stroke="#FFFFFF" strokeOpacity=".32" strokeWidth="20" fill="none" />
            {[[50,220],[180,180],[322,120],[900,235],[940,490],[750,620],[335,650],[80,600],[630,118]].map(([x,y],i) => <TinyTree key={i} x={x} y={y} rose={i%2===0} scale={i%3===0?1.4:1} />)}
          </>
        )}
        <ellipse cx="535" cy="540" rx="600" ry="340" fill="url(#iso-grid)" />
        <path d="M181 409 L517 163 L809 420 L626 569 L231 609 L181 409" fill="none" stroke="#FFF4E0" strokeWidth="10" strokeDasharray="17 15" strokeLinecap="round" opacity=".88" />
        <path d="M502 339 L608 550" fill="none" stroke="#FFF7EC" strokeWidth="9" strokeDasharray="18 19" strokeLinecap="round" />
        {ROOMS.map((r) => <Building key={r.id} room={r} active={selected.area===r.id} visited={visited.includes(r.id)} theme={scene} onView={onView} />)}
        <g style={{ transform: `translate(${selected.x}px, ${selected.y}px)`, transition: "transform 1100ms cubic-bezier(.2,.8,.27,1)" }}>
          <ellipse cx="0" cy="36" rx="45" ry="15" fill="#FFF4B6" opacity=".65" className="iso-room-glow" />
          <Robot x={0} y={0} color={selected.color} floating size={1.05} />
          <rect x="-68" y="-102" width="136" height="30" rx="15" fill="#FFFFFF" stroke="#EDDBCD" />
          <text x="0" y="-83" fill="#665469" fontSize="12" textAnchor="middle" fontWeight="900">{selected.icon} {selected.name}</text>
        </g>
        <g>
          <ellipse cx="80" cy="119" rx="32" ry="7" fill="#926F72" opacity=".15" />
          <g className="iso-drone"><path d="M40 104 H114" stroke="#FFFFFF" strokeWidth="6" strokeLinecap="round"/><ellipse cx="77" cy="100" rx="29" ry="13" fill="#FFFFFF"/><rect x="64" y="94" width="26" height="11" rx="6" fill="#76C9D9"/></g>
        </g>
      </svg>
    </div>
  );
}

function Avatar({ expert, size = 39 }) {
  return (
    <div className="iso-avatar" style={{ width: size, height: size, background: `${expert.color}25`, borderColor: `${expert.color}80`, color: expert.color }}>
      <Bot size={size*.52} />
      <span className="iso-avatar-pin" style={{ background: expert.color }} />
    </div>
  );
}

const newChat = (content, from = "agent") => ({ id: `${Date.now()}-${Math.random()}`, from, content, time: timeLabel() });
export default function ISOAgentCity({ user, assessment, request, onLogout }) {
  const [scene, setScene] = useState("mars");
  const [zoom, setZoom] = useState(100);
  const [status, setStatus] = useState("idle");
  const [stage, setStage] = useState(-1);
  const [activeExpert, setActiveExpert] = useState("planner");
  const [visited, setVisited] = useState([]);
  const [panel, setPanel] = useState("chat");
  const [logs, setLogs] = useState([]);
  const [chat, setChat] = useState([newChat("Chào Sếp! Tôi có thể thực hiện vòng kiểm toán 56 controls trên dữ liệu đã kết nối trong Enterprise Lab. Không cần tải file. Nếu không đủ bằng chứng, tôi ghi nhận khoảng trống và tự chuyển sang control tiếp theo.")]);
  const [draft, setDraft] = useState("");
  const [run, setRun] = useState(null);
  const [runError, setRunError] = useState("");
  const [failedControls, setFailedControls] = useState([]);
  const [sourceInfo, setSourceInfo] = useState(null);
  const [showFailures, setShowFailures] = useState(false);
  const [selectedRoom, setSelectedRoom] = useState(null);
  const logEl = useRef(null);
  const chatEl = useRef(null);
  const lastEventId = useRef(0);
  const missingNoticeCount = useRef(0);
  const observedRunId = useRef(null);
  const polling = useRef(false);

  const say = useCallback((message, from = "agent") =>
    setChat((items) => [...items, newChat(message, from)]), []);

  // Refresh sau khi mở lại trang, đồng thời nhận phiên mới do thành viên khác tạo.
  useEffect(() => {
    let disposed = false;
    if (!request || !assessment?.assessment_id) return undefined;
    const refreshLatest = async () => {
      try {
        const existing = await request(`/api/assessments/${assessment.assessment_id}/auto-audits/latest`);
        if (!disposed && existing) {
          if (observedRunId.current !== existing.run_id) {
            observedRunId.current = existing.run_id;
            lastEventId.current = 0;
            missingNoticeCount.current = 0;
            setLogs([]);
            setChat([newChat("Đang đồng bộ phiên kiểm toán chung trong PostgreSQL.")]);
          }
          setRun(existing);
          setStatus(existing.status === "RUNNING" ? "running" : "completed");
        }
      } catch (error) {
        if (!disposed) setRunError(`Không tải được tiến độ: ${error.message}`);
      }
    };
    refreshLatest();
    const timer = setInterval(refreshLatest, 6000);
    return () => { disposed = true; clearInterval(timer); };
  }, [request, assessment?.assessment_id]);

  useEffect(() => { if (logEl.current) logEl.current.scrollTop=logEl.current.scrollHeight; }, [logs]);
  useEffect(() => { if (chatEl.current) chatEl.current.scrollTop=chatEl.current.scrollHeight; }, [chat]);

  // Chỉ hiển thị các event đã được ghi thật trong PostgreSQL.
  useEffect(() => {
    if (!run?.run_id || !request) return undefined;
    let disposed = false;
    const poll = async () => {
      if (polling.current) return;
      polling.current = true;
      try {
        const [snapshot, events] = await Promise.all([
          request(`/api/auto-audits/${run.run_id}`),
          request(`/api/auto-audits/${run.run_id}/events?after=${lastEventId.current}`),
        ]);
        if (disposed) return;
        setRun(snapshot);
        setStatus(snapshot.status === "RUNNING" ? "running" : "completed");
        setRunError("");
        if (snapshot.status === "FAILED" || snapshot.status === "INTERRUPTED") {
          setRunError(snapshot.error_message || "Phiên kiểm toán đã bị ngắt.");
        }
        const fresh = events.filter((item) => item.event_id > lastEventId.current);
        if (fresh.length) {
          lastEventId.current = fresh[fresh.length-1].event_id;
          setLogs((items) => [...items, ...fresh.map((event) => {
            const kind = event.event_type === "CONTROL_STARTED" ? "action" :
              ["JOB_CLAIMED", "PIPELINE_STEP", "SOURCE_INDEXED", "SOURCE_ALREADY_INDEXED"].includes(event.event_type) ? "tool" :
              ["SOURCE_ERROR", "SOURCE_CONFIG_ERROR", "SOURCE_CHANGED_REVIEW", "JOB_FAILURE", "CONTROL_ERROR"].includes(event.event_type) ? "wait" :
              event.event_type === "CONTROL_FINISHED" ?
                (event.details.workflow_status === "WAITING_EVIDENCE" ? "wait" : "finding") : "done";
            const result = event.event_type === "CONTROL_FINISHED" ?
              ` | ${event.details.workflow_status} | ISO: ${event.details.compliance_status || "Chưa kết luận"} | Evidence: ${event.details.evidence_count || 0} (lab: ${event.details.synthetic_evidence_count || 0})` :
              event.event_type === "PIPELINE_STEP" ? ` | ${event.details.step}` :
              event.event_type === "SOURCE_INDEXED" ? ` | ${event.details.file} | Đã lưu evidence thật` :
              event.event_type === "SOURCE_ERROR" ? ` | ${event.details.file} | Không đọc được tài liệu` :
              event.event_type === "JOB_FAILURE" ? ` | ${event.details.error || "Lỗi job"}` : "";
            return { id: event.event_id, kind,
              time: new Date(event.created_at).toLocaleTimeString("vi-VN"),
              msg: `${event.event_type} ${event.control_id || ""}${result}`.trim() };
          })].slice(-200));
          for (const event of fresh) {
            if (event.event_type === "CONTROL_STARTED") {
              const ctrl = event.control_id || "";
              const group = ctrl.startsWith("A.6.") ? "hr" : ctrl.startsWith("A.7.") ? "warehouse" : "it";
              const expert = group === "hr" ? "collector" : group === "warehouse" ? "risk" : "evaluator";
              setActiveExpert(expert);
              setStage(group === "hr" ? 1 : group === "warehouse" ? 4 : 3);
              setVisited((v) => v.includes(group) ? v : [...v, group]);
            }
            if (event.event_type === "CONTROL_FINISHED" &&
                ["WAITING_EVIDENCE", "NEEDS_REVIEW"].includes(event.details.workflow_status)) {
              missingNoticeCount.current += 1;
              if (missingNoticeCount.current <= 3 || missingNoticeCount.current % 10 === 0) {
                say(`Đã kiểm tra ${event.control_id}: ${event.details.compliance_status || "chưa kết luận"}. Tôi ghi lại khoảng trống và tự chuyển sang mục tiếp theo. Không yêu cầu tải tài liệu.`);
              }
            }
            if (event.event_type === "RUN_FINISHED") {
              setActiveExpert("reporter");
              setStage(5);
              say(`Đã xử lý ${event.details.processed}/${event.details.total} controls. Thiếu bằng chứng hoặc cần xem xét: ${event.details.gaps}; tác vụ lỗi: ${event.details.failed}. Đây là đánh giá lab, không phải chứng nhận doanh nghiệp tuân thủ ISO.`);
            }
            if (event.event_type === "RUN_INTERRUPTED") {
              say("Phiên kiểm toán bị ngắt do API khởi động lại. Có thể bắt đầu một phiên mới.");
            }
          }
        }
      } catch (error) {
        if (!disposed) setRunError(error.message || "Không đọc được trạng thái kiểm toán.");
      } finally { polling.current = false; }
    };
    poll();
    const timer = setInterval(poll, 1800);
    return () => { disposed = true; clearInterval(timer); };
  }, [run?.run_id, request, say]);

  useEffect(() => {
    if (!request || !assessment?.assessment_id) return undefined;
    let disposed = false;
    request(`/api/assessments/${assessment.assessment_id}/auto-audits/sources`)
      .then(data => { if (!disposed) setSourceInfo(data); })
      .catch(() => { if (!disposed) setSourceInfo(null); });
    return () => { disposed = true; };
  }, [request, assessment?.assessment_id]);

  useEffect(() => {
    if (!request || !run?.run_id || !run?.failed) {
      setFailedControls([]);
      return undefined;
    }
    let disposed = false;
    const refresh = () => request(`/api/auto-audits/${run.run_id}/failures`)
      .then(data => { if (!disposed) setFailedControls(data.failed_controls || []); })
      .catch(() => {});
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => { disposed = true; clearInterval(interval); };
  }, [request, run?.run_id, run?.failed]);

  const start = async () => {
    if (status === "running" || !request || !assessment?.assessment_id) return;
    setRunError("");
    setFailedControls([]);
    setShowFailures(false);
    setStatus("running");
    setLogs([]);
    setChat([]);
    setStage(0);
    setActiveExpert("planner");
    setVisited([]);
    setPanel("chat");
    lastEventId.current = 0;
    missingNoticeCount.current = 0;
    try {
      const created = await request(`/api/assessments/${assessment.assessment_id}/auto-audits`, {
        method: "POST",
      });
      observedRunId.current = created.run_id;
      setRun(created);
      say("Tôi đã tạo phiên kiểm toán backend. LangGraph/Ollama sẽ lần lượt xử lý controls. Không đủ bằng chứng thì tự ghi nhận khoảng trống, không hỏi tải file.");
    } catch (error) {
      setStatus("idle");
      setRunError(error.message || "Không thể tạo phiên kiểm toán.");
      say(`Không khởi động được Auto-Audit: ${error.message}`);
    }
  };

  const send = (event) => {
    event.preventDefault();
    const message = draft.trim();
    if (!message) return;
    say(message, "user");
    setDraft("");
    say("Tôi ghi nhận lời nhắn trong giao diện. Lệnh tự động đang lấy dữ liệu từ nguồn đã kết nối; khung chat chưa hỗ trợ hội thoại Ollama trực tiếp.");
  };
  const current = EXPERTS.find((a) => a.id === activeExpert) || EXPERTS[0];
  const roomInfo = selectedRoom && ROOMS.find((r) => r.id === selectedRoom);
  const liveCount = status === "running" ? 1 : 0;
  const label = status === "running" ? "ĐANG KIỂM TOÁN" : status === "completed" ? "ĐÃ KẾT THÚC" : "SẴN SÀNG";
  return (
    <div className="iso-agent-city min-h-screen text-white">
      <style>{`
        .iso-agent-city{font-family:ui-rounded,Inter,"Trebuchet MS",system-ui,sans-serif;background:radial-gradient(ellipse at 60% 40%,#34435D 0%,#18263A 60%,#111C2B 100%);color:#F8F8FE}
        .iso-panel{background:linear-gradient(140deg,rgba(37,54,76,.91),rgba(27,43,62,.95));border:1px solid rgba(255,255,255,.1);box-shadow:0 22px 54px rgba(5,13,27,.14);border-radius:25px;backdrop-filter:blur(18px)}
        .iso-ghost{background:rgba(255,255,255,.065);border:1px solid rgba(255,255,255,.095)}
        .iso-avatar{display:flex;align-items:center;justify-content:center;border:1px solid;border-radius:15px;flex-shrink:0;position:relative}
        .iso-avatar-pin{width:7px;height:7px;border:2px solid #1B3046;box-sizing:content-box;border-radius:100%;position:absolute;bottom:-3px;right:-2px}
        .iso-scroll{scrollbar-width:thin;scrollbar-color:#5C6E85 transparent}
        .iso-map-viewport{width:100%;height:100%;overflow:auto;display:flex;align-items:center;justify-content:center}
        @keyframes isoFloat{0%,100%{transform:translateY(0)}50%{transform:translateY(-9px)}}
        @keyframes isoGlow{0%,100%{opacity:.3}50%{opacity:.75}}
        @keyframes isoDrone{0%,100%{transform:translateX(0) translateY(0)}50%{transform:translateX(640px) translateY(88px)}}
        .iso-agent-float{animation:isoFloat 2.2s ease-in-out infinite}
        .iso-room-glow{animation:isoGlow 1.8s ease-in-out infinite}
        .iso-drone{animation:isoDrone 16s ease-in-out infinite}
        @media(prefers-reduced-motion:reduce){.iso-agent-float,.iso-room-glow,.iso-drone{animation:none!important}}
      `}</style>
      <div className="mx-auto max-w-[1900px] px-4 pb-6">
        <header className="flex flex-wrap items-center justify-between gap-3 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-[18px] bg-gradient-to-br from-orange-300 to-orange-500 shadow-[0_8px_24px_rgba(255,141,72,.24)]"><Sparkles size={27}/></div>
            <div><h1 className="text-lg font-black tracking-wide sm:text-xl">ISO ENTERPRISE · AI AGENT CITY</h1><p className="text-[10px] font-bold tracking-[.13em] text-slate-400">6 CHUYÊN GIA AI · 56 CONTROLS · ISO/IEC 27001:2022</p></div>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span className="iso-ghost rounded-full px-3 py-2 text-slate-300">🧪 LAB + OLLAMA</span>
            {user && <span className="iso-ghost hidden rounded-full px-3 py-2 text-slate-300 sm:inline">👤 {user.username || user.full_name || user.name || "Thành viên"}</span>}
            {/* Đăng xuất được quản lý tại App.jsx để tránh nút lặp. */}
          </div>
        </header>
        <div className="mb-3 grid grid-cols-2 gap-3 lg:grid-cols-4">
          {[
            { k:"ĐỘI CHUYÊN GIA", v:"6 Agents", icon:<Users size={19}/> },
            { k:"KIỂM SOÁT ISO", v:"56 Controls", icon:<ShieldCheck size={19}/> },
            { k:"AGENTS ĐANG LÀM", v:String(liveCount), icon:<Activity size={19}/> },
            { k:"CONTROLS ĐÃ XỬ LÝ", v:`${run?.processed || 0}/${run?.total || 56}`, icon:<CheckCircle2 size={19}/> },
          ].map((m) => <div key={m.k} className="iso-panel flex items-center gap-3 p-3.5"><span className="rounded-xl bg-orange-400/10 p-2.5 text-orange-300">{m.icon}</span><div><div className="text-[10px] font-bold text-slate-400">{m.k}</div><div className="text-xl font-black">{m.v}</div></div></div>)}
        </div>
        <div className="grid grid-cols-1 gap-3 xl:grid-cols-[285px_minmax(0,1fr)_340px]">
          <aside className="iso-panel flex min-h-[580px] flex-col p-3.5 xl:h-[745px]">
            <div className="mb-3 flex items-center gap-2 border-b border-white/10 pb-3"><BrainCircuit className="text-orange-300" size={22}/><div><div className="text-sm font-black">ĐỘI AI CHUYÊN GIA</div><div className="text-[10px] text-slate-400">Mỗi Agent một chuyên môn</div></div></div>
            <div className="space-y-1.5">
              {EXPERTS.map((agent) => {
                const doing = status !== "idle" && activeExpert === agent.id;
                return <button key={agent.id} type="button" onClick={() => {setActiveExpert(agent.id);setPanel("expert");}} className={`flex w-full items-center gap-2.5 rounded-2xl border p-2.5 text-left transition ${doing?"border-orange-300/60 bg-orange-400/10":"border-white/[.06] bg-white/[.03] hover:bg-white/[.07]"}`}>
                  <Avatar expert={agent} size={36}/><div className="min-w-0 flex-1"><p className="truncate text-xs font-black">{agent.name}</p><p className="truncate text-[10px] text-slate-400">{agent.title}</p></div><span className={`h-2 w-2 rounded-full ${doing ? "animate-pulse bg-orange-300":"bg-slate-600"}`}/>
                </button>;
              })}
            </div>
            <div className="mt-3 border-t border-white/10 pt-3"><div className="mb-2 flex items-center gap-2 text-xs font-black"><Terminal size={17} className="text-cyan-300"/> NÃO BỘ AI — NHẬT KÝ</div></div>
            <div ref={logEl} aria-live="polite" className="iso-scroll min-h-[130px] flex-1 space-y-2 overflow-y-auto rounded-xl bg-[#0D1B2B] p-2.5 font-mono">
              {logs.length===0 ? <div className="pt-8 text-center text-[11px] leading-relaxed text-slate-500">Đang chờ lệnh Auto-Audit.<br/>Sự kiện backend xuất hiện ở đây.</div> : logs.map((item) => <div key={item.id} className="border-l-2 border-white/10 pl-2.5"><div className="flex flex-wrap items-center justify-between gap-1"><span className="text-[9px] font-black" style={{color:INDICATOR[item.kind]?.color}}>[{INDICATOR[item.kind]?.label}]</span><span className="text-[9px] text-slate-600">{item.time}</span></div><p className="mt-1 break-words text-[10px] leading-relaxed text-slate-300">{item.msg}</p></div>)}
            </div>
            <p className="mt-2 text-center text-[10px] text-slate-500">Sự kiện job từ PostgreSQL · Lab có thể dùng evidence tổng hợp</p>
          </aside>
          <section className="flex min-w-0 flex-col gap-3">
            <div className="iso-panel flex flex-wrap items-center justify-between gap-2 px-4 py-2.5">
              <div className="flex items-center gap-2 text-xs font-black"><LayoutGrid size={17} className="text-orange-300"/> THẾ GIỚI AI AGENT</div>
              <div className="flex flex-wrap items-center gap-2 text-[11px]">
                <button type="button" onClick={() => setScene("mars")} className={`rounded-full px-3 py-1.5 font-bold ${scene==="mars"?"bg-orange-400 text-[#273047]":"iso-ghost text-slate-300"}`}>🪐 Sao Hỏa</button>
                <button type="button" onClick={() => setScene("garden")} className={`rounded-full px-3 py-1.5 font-bold ${scene==="garden"?"bg-emerald-300 text-[#273047]":"iso-ghost text-slate-300"}`}>🌷 Pastel City</button>
                <button type="button" onClick={()=>setZoom((z)=>Math.max(100,z-15))} title="Thu nhỏ" className="iso-ghost rounded-full p-2"><ZoomOut size={14}/></button>
                <button type="button" onClick={()=>setZoom((z)=>Math.min(165,z+15))} title="Phóng to" className="iso-ghost rounded-full p-2"><ZoomIn size={14}/></button>
              </div>
            </div>
            <div className="relative min-w-0 flex-1 overflow-hidden rounded-[29px] border-[3px] border-orange-200/40 bg-[#E9B995] shadow-2xl" style={{height:"575px", minHeight:"510px"}}>
              <CityMap scene={scene} activeExpert={activeExpert} visited={visited} onView={setSelectedRoom} zoom={zoom}/>
              <div className="pointer-events-none absolute left-4 top-4 rounded-2xl border border-white/70 bg-white/90 px-4 py-2.5 text-xs font-black text-[#815A6D] shadow-lg">{scene==="mars"?"🪐 MARS AUDIT BASE":"🌸 PASTEL AUDIT CITY"}<p className="mt-0.5 text-[9px] text-[#9A8091]">CHUYÊN GIA ĐANG HIỂN THỊ: {current.name.toUpperCase()}</p></div>
              <div className="pointer-events-none absolute bottom-4 left-4 rounded-2xl bg-white/90 px-3 py-2 text-[#825F6D] shadow"><div className="text-[10px] font-black">{current.icon} {current.name}</div><div className="text-[9px]">{current.location}</div></div>
              {roomInfo && <div className="absolute right-4 top-4 z-20 max-w-[235px] rounded-2xl border border-white/60 bg-white/95 p-3 text-[#544A5D] shadow-xl"><div className="flex justify-between gap-2"><b className="text-xs">{roomInfo.icon} {roomInfo.title}</b><button onClick={()=>setSelectedRoom(null)} aria-label="Đóng"><X size={14}/></button></div><p className="mt-1 text-[11px]">{roomInfo.sub}</p><p className="mt-2 text-[10px] text-[#A7796B]">Chọn tòa nhà chỉ để xem thông tin, không khởi chạy đánh giá.</p></div>}
            </div>
            <button type="button" onClick={start} disabled={status==="running"} className="flex w-full items-center justify-center gap-3 rounded-full border-[3px] border-orange-200 bg-gradient-to-r from-[#FE7937] via-[#FF9A55] to-[#FFAD65] px-3 py-4 text-center text-[12px] font-black shadow-[0_6px_0_#A85B40,0_16px_30px_rgba(235,115,65,.18)] transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-75 sm:text-[15px]">
              {status==="running" ? <Loader2 size={22} className="animate-spin"/> : status==="completed" ? <RotateCcw size={22}/> : <Rocket size={23}/>}
              {status==="running" ? `ĐANG KIỂM TOÁN ${run?.processed || 0}/${run?.total || 56} CONTROLS` : status==="completed" ? "CHẠY PHIÊN KIỂM TOÁN LAB MỚI" : "🚀 KHỞI ĐỘNG AUTO-AUDIT 56 CONTROLS"}
            </button>
            {runError && <div role="alert" className="rounded-xl border border-red-400/30 bg-red-400/10 px-4 py-3 text-xs text-red-200">{runError}</div>}
            <div className="iso-panel px-4 py-3">
              <div className="mb-2 flex items-center justify-between gap-2 text-xs"><span className="font-black">TIẾN ĐỘ KIỂM TOÁN THỰC THI</span><span className="text-slate-400">{run?.processed || 0}/{run?.total || 56} controls</span></div>
              <div className="h-3 w-full overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-orange-400 transition-all" style={{width: `${run?.total ? Math.min(100,100*run.processed/run.total) : 0}%`}}/></div>
              <div className="mt-2 flex flex-wrap gap-3 text-[11px] text-slate-300"><span>Đang xử lý: <b>{run?.current_control || "Không"}</b></span><span>Thiếu/chờ xem xét: <b>{run?.gaps || 0}</b></span><span>Lỗi: <b>{run?.failed || 0}</b></span></div>
              <div className="mt-2 rounded-xl border border-cyan-300/15 bg-cyan-300/5 px-3 py-2 text-[11px] text-slate-300">
                <b className="text-cyan-200">Nguồn bằng chứng tự động: </b>
                {sourceInfo?.error ? `Cấu hình lỗi: ${sourceInfo.error}` :
                 sourceInfo?.enabled ? `${sourceInfo.configured_items} tài liệu khai báo trong thư mục được cấp quyền` :
                 "Chưa kết nối thư mục — hiện chỉ sử dụng dữ liệu lab"}
              </div>
              {run?.failed > 0 && <div className="mt-2 rounded-xl border border-red-400/25 bg-red-400/5 p-3 text-xs">
                <button type="button" onClick={() => setShowFailures(value => !value)} className="font-bold text-red-200 underline underline-offset-2">
                  {showFailures ? "Ẩn chi tiết lỗi" : `Xem ${run.failed} tác vụ lỗi`}
                </button>
                {showFailures && <div className="mt-2 max-h-52 space-y-2 overflow-y-auto">
                  {failedControls.length === 0 && <div className="text-slate-400">Đang lấy chi tiết từ PostgreSQL...</div>}
                  {failedControls.map((item, i) => <div key={`${item.control_id}-${i}`} className="rounded-lg bg-black/15 p-2 text-slate-200">
                    <b>{item.control_id}</b> · {item.reason || item.error_type || "Không có lý do chi tiết; kiểm tra Terminal FastAPI"}
                    {item.job_id && <div className="break-all text-[10px] text-slate-400">Job: {item.job_id}</div>}
                  </div>)}
                </div>}
              </div>}
              <div className="mt-2 text-[10px] text-slate-400">Các chuyên gia là biểu diễn trực quan của pipeline LangGraph; bằng chứng tổng hợp từ phòng thí nghiệm không đại diện cho doanh nghiệp thật.</div>
            </div>
          </section>
          <aside className="iso-panel flex min-h-[560px] flex-col p-3.5 xl:h-[745px]">
            <div className="mb-3 flex items-center gap-2"><Avatar expert={current} size={43}/><div className="min-w-0 flex-1"><div className="text-sm font-black">{current.name}</div><div className="text-[11px] text-slate-400">{current.title}</div></div><span className={`rounded-full px-2.5 py-1 text-[10px] font-bold ${status==="running"?"bg-orange-300/15 text-orange-200":"bg-emerald-300/10 text-emerald-300"}`}>{label}</span></div>
            <div className="mb-3 flex gap-1.5 border-b border-white/10 pb-3">
              {[{id:"chat",name:"Trò chuyện",Icon:MessageCircle},{id:"expert",name:"Chuyên gia",Icon:Bot},{id:"tasks",name:"Tiến độ",Icon:ClipboardCheck}].map(t=><button key={t.id} type="button" onClick={()=>setPanel(t.id)} className={`flex flex-1 items-center justify-center gap-1 rounded-xl px-1.5 py-2 text-[10px] font-bold ${panel===t.id?"bg-orange-400 text-[#29354A]":"iso-ghost text-slate-300"}`}><t.Icon size={13}/>{t.name}</button>)}
            </div>
            {panel==="chat" ? <>
              <div ref={chatEl} aria-live="polite" className="iso-scroll min-h-[220px] flex-1 space-y-3 overflow-y-auto pr-1">
                {chat.map(m => <div key={m.id} className={`flex gap-2 ${m.from==="user"?"justify-end":""}`}>{m.from==="agent"&&<Avatar expert={current} size={30}/>}<div className={`max-w-[88%] rounded-[16px] px-3 py-2.5 ${m.from==="user"?"rounded-tr-sm bg-orange-400 text-[#2C3146]":"rounded-tl-sm border border-white/10 bg-[#34465A]"}`}><p className="whitespace-pre-wrap text-[11px] leading-[1.65]">{m.content}</p><p className={`mt-1 text-[9px] ${m.from==="user"?"text-[#6B5155]":"text-slate-400"}`}>{m.time}</p></div></div>)}
                <div className="rounded-xl border border-cyan-300/20 bg-cyan-300/5 p-3 text-[11px] leading-relaxed text-slate-300">
                  <b className="text-cyan-200">Không dùng upload:</b> Agent tự tìm trong cơ sở dữ liệu và môi trường lab đã kết nối. Thiếu tài liệu được đánh dấu Insufficient Evidence để người phụ trách xem xét sau. Không tự kết luận đạt.
                </div>
              </div>
              <form className="mt-3 flex items-center gap-2 rounded-2xl border border-white/10 bg-[#102034] p-2" onSubmit={send}><input aria-label="Nhắn tin cho chuyên gia" value={draft} onChange={e=>setDraft(e.target.value)} placeholder="Nhắn tin cho Chief Audit..." className="min-w-0 flex-1 bg-transparent px-2 py-2 text-[11px] outline-none placeholder:text-slate-500"/><button type="submit" disabled={!draft.trim()} className="rounded-full bg-orange-400 p-2 text-[#273042] disabled:opacity-40"><Send size={15}/></button></form>
            </> : panel==="expert" ? <div className="iso-scroll flex-1 space-y-4 overflow-y-auto"><div className="rounded-2xl border border-white/10 bg-white/[.04] p-4"><div className="mb-3 flex items-center gap-3"><Avatar expert={current} size={54}/><div><div className="font-black">{current.name}</div><div className="text-xs text-slate-400">{current.title}</div></div></div><div className="space-y-3 text-xs"><p><span className="text-slate-400">Địa điểm:</span> {current.location}</p><p><span className="text-slate-400">Trách nhiệm:</span> {current.mission}</p><p><span className="text-slate-400">Đội:</span> ISO 27001 AI Audit Team</p></div></div><div className="rounded-2xl bg-orange-300/10 p-4 text-xs leading-relaxed text-orange-100">💡 Trong bản hoàn chỉnh, nhiệm vụ chuyên gia sẽ gắn với job và tool thực tế của LangGraph, không phải tên Agent được đổi theo timer.</div><button type="button" onClick={()=>setPanel("chat")} className="rounded-full bg-orange-400 px-4 py-2.5 text-xs font-bold text-[#273042]">Trở về Chat</button></div> : <div className="iso-scroll flex-1 space-y-2 overflow-y-auto">{STAGES.map((s,i)=><div key={s.key} className={`flex gap-3 rounded-xl border p-3 ${i===stage?"border-orange-300/30 bg-orange-300/10":"border-white/[.05] bg-white/[.03]"}`}><span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white/10 text-[11px] font-black">{i+1}</span><div><div className="text-xs font-black">{s.title}</div><div className="mt-1 text-[10px] text-slate-400">{EXPERTS.find(e=>e.id===s.expert)?.name} · {status==="completed"||i<stage?"Đã đi qua (demo)":i===stage?"Đang xử lý":"Đang chờ"}</div></div></div>)}</div>}
            <div className="mt-3 border-t border-white/10 pt-3 text-center text-[10px] text-slate-500">Workflow FastAPI/LangGraph/Ollama · Bằng chứng lab có thể là dữ liệu giả lập</div>
          </aside>
        </div>
        <footer className="mt-3 flex flex-wrap items-center justify-between gap-2 text-[10px] text-slate-500"><span>ISO ENTERPRISE LAB · AI AUDIT CITY · 6 CHUYÊN GIA</span><span>Phiên lab lưu PostgreSQL; không phải chứng nhận tuân thủ ISO</span></footer>
      </div>
    </div>
  );
}
