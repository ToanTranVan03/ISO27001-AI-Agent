import { runA61Pilot } from "./auditPilot";
import React, { useEffect, useRef, useState } from "react";
import {
  Activity, AlertCircle, ArrowUp, Bot, BrainCircuit,
  Building2, CheckCircle2, Clock3, Cpu, Database,
  FileSearch, FileText, FileUp, Loader2, MessageCircle,
  Paperclip, Rocket, ShieldCheck, Sparkles, Terminal,
  UploadCloud, Users, Warehouse, Wallet, X
} from "lucide-react";

// ======================================================
// AUTONOMOUS ISO ENTERPRISE — FRONTEND DEMO
// Không thực thi FastAPI/LangGraph thật.
// Không tạo kết luận tuân thủ ISO thật.
// ======================================================

const ROOMS = [
  {
    id: "hr",
    name: "Phòng Nhân sự",
    short: "NHÂN SỰ",
    control: "A.6.1",
    color: "#F8AF7A",
    icon: "👥",
    x: 65,
    y: 277,
  },
  {
    id: "accounting",
    name: "Phòng Kế toán",
    short: "KẾ TOÁN",
    control: "A.8",
    color: "#A5D5BB",
    icon: "💰",
    x: 320,
    y: 110,
  },
  {
    id: "management",
    name: "Phòng Quản lý",
    short: "QUẢN LÝ",
    control: "A.6",
    color: "#B9B6EF",
    icon: "📋",
    x: 705,
    y: 230,
  },
  {
    id: "warehouse",
    name: "Nhà Kho",
    short: "NHÀ KHO",
    control: "A.7",
    color: "#F4CC80",
    icon: "📦",
    x: 480,
    y: 428,
  },
];

const AGENT_POSITIONS = {
  home: { x: 480, y: 370 },
  hr: { x: 205, y: 444 },
  accounting: { x: 450, y: 277 },
  management: { x: 837, y: 405 },
  warehouse: { x: 613, y: 595 },
};

const STATUS_NAMES = {
  idle: "Sẵn sàng",
  running: "Đang tự động kiểm toán",
  waiting: "Cần bổ sung bằng chứng",
  completed: "Đã hoàn tất mô phỏng",
};

const LOG_STYLES = {
  action: {
    name: "HÀNH ĐỘNG",
    color: "text-sky-300",
    dot: "bg-sky-400",
  },
  execute: {
    name: "THỰC THI",
    color: "text-amber-300",
    dot: "bg-amber-400",
  },
  tool: {
    name: "GỌI TOOL",
    color: "text-violet-300",
    dot: "bg-violet-400",
  },
  review: {
    name: "ĐỐI CHIẾU",
    color: "text-teal-300",
    dot: "bg-teal-400",
  },
  warning: {
    name: "THIẾU DỮ LIỆU",
    color: "text-orange-300",
    dot: "bg-orange-400",
  },
  success: {
    name: "HOÀN THÀNH",
    color: "text-emerald-300",
    dot: "bg-emerald-400",
  },
};

function Panel({ children, className = "" }) {
  return (
    <section
      className={
        "rounded-[28px] border border-white/10 " +
        "bg-[#172639]/85 shadow-[0_20px_60px_rgba(9,17,30,.25)] " +
        "backdrop-blur-xl " + className
      }
    >
      {children}
    </section>
  );
}

// ======================================================
// PHÒNG BAN MINIATURE / DIORAMA
// ======================================================

function DioramaRoom({ room, active, finished }) {
  const col = room.color;
  const isWarehouse = room.id === "warehouse";

  return (
    <g transform={`translate(${room.x} ${room.y})`}>
      {active && (
        <ellipse
          cx="120"
          cy="165"
          rx="125"
          ry="48"
          fill="#FFE99C"
          opacity=".5"
          className="room-pulse"
        />
      )}

      {/* Bóng đổ */}
      <ellipse
        cx="120"
        cy="168"
        rx="110"
        ry="31"
        fill="#A97048"
        opacity=".17"
      />

      {/* Đế isometric */}
      <polygon
        points="7,112 116,53 231,113 119,173"
        fill="#FFF3DF"
        stroke="#D7A47B"
        strokeWidth="3"
      />
      <polygon
        points="7,112 119,173 119,184 7,124"
        fill="#D3A47F"
      />
      <polygon
        points="119,173 231,113 231,125 119,184"
        fill="#BE8E72"
      />

      {/* Mặt sàn */}
      <polygon
        points="26,108 116,60 211,110 119,159"
        fill="#FFF0D7"
        stroke="#F7D9B9"
        strokeWidth="2"
      />
      <polygon
        points="53,110 115,77 183,111 119,146"
        fill={col}
        opacity=".28"
      />

      {/* Tường kính 2 phía */}
      <polygon
        points="26,108 26,51 116,3 116,60"
        fill="#E0F6F8"
        fillOpacity=".29"
        stroke="#FFFFFF"
        strokeWidth="3"
      />
      <polygon
        points="116,3 211,55 211,110 116,60"
        fill="#E0F6F8"
        fillOpacity=".23"
        stroke="#FFFFFF"
        strokeWidth="3"
      />
      <path
        d="M26 79 L116 32 L211 83"
        stroke="#FFF"
        strokeOpacity=".55"
        fill="none"
      />

      {/* Cây xanh */}
      <g>
        <polygon points="42,114 53,108 64,114 53,121" fill="#D79471"/>
        <path d="M44 114 L53 121 V135 L44 129 Z" fill="#E5A584"/>
        <path d="M53 121 L64 114 V129 L53 135 Z" fill="#BD7C62"/>
        <path d="M53 110 V82" stroke="#538C67" strokeWidth="3"/>
        <ellipse cx="44" cy="90" rx="9" ry="16" fill="#92C79A" transform="rotate(-27 44 90)"/>
        <ellipse cx="61" cy="84" rx="9" ry="15" fill="#70B58C" transform="rotate(27 61 84)"/>
      </g>

      {/* Nội thất mỗi phòng */}
      {isWarehouse ? (
        <g>
          <polygon points="100,106 132,89 164,105 132,123" fill="#DFA871"/>
          <polygon points="100,106 132,123 132,143 100,126" fill="#B88058"/>
          <polygon points="132,123 164,105 164,125 132,143" fill="#C99262"/>
          <path d="M114 99 L146 115" stroke="#FFF0D6" strokeWidth="3"/>
          <polygon points="149,89 174,76 196,88 171,103" fill="#F3C984"/>
          <polygon points="149,89 171,103 171,120 149,107" fill="#BF9568"/>
          <polygon points="171,103 196,88 196,106 171,120" fill="#D5AD75"/>
        </g>
      ) : (
        <g>
          {/* Bàn làm việc */}
          <polygon
            points="83,119 125,96 173,121 129,146"
            fill="#EFC18E"
            stroke="#D09B70"
            strokeWidth="2"
          />
          <polygon
            points="83,119 129,146 129,154 83,127"
            fill="#CF9A75"
          />
          <polygon
            points="129,146 173,121 173,128 129,154"
            fill="#BB855F"
          />

          {/* Máy tính */}
          <polygon points="121,110 141,99 158,109 139,120" fill="#647B94"/>
          <polygon points="141,99 141,76 158,86 158,109" fill="#6D8194"/>
          <polygon points="145,84 154,89 154,102 145,97" fill="#A8E6E4"/>
        </g>
      )}

      {/* Nhân viên robot chibi */}
      <g transform="translate(102 78)">
        <path d="M-7 32 V44 M8 32 V44" stroke="#7F93B2" strokeWidth="7" strokeLinecap="round"/>
        <rect x="-17" y="9" width="34" height="30" rx="12" fill={col} stroke="#FFF9ED" strokeWidth="3"/>
        <rect x="-27" y="14" width="10" height="18" rx="5" fill={col}/>
        <rect x="17" y="14" width="10" height="18" rx="5" fill={col}/>
        <rect x="-22" y="-23" width="44" height="38" rx="17" fill="#FFF8EF" stroke={col} strokeWidth="3"/>
        <rect x="-15" y="-14" width="30" height="21" rx="9" fill="#425A69"/>
        <circle cx="-7" cy="-5" r="3" fill="white"/>
        <circle cx="7" cy="-5" r="3" fill="white"/>
        <path d="M-4 3 Q0 7 4 3" fill="none" stroke="#FFE1AC" strokeWidth="2"/>
        <path d="M0 -23 V-32" stroke="#8094A0" strokeWidth="2"/>
        <circle cx="0" cy="-34" r="4" fill="#F7B16F"/>
      </g>

      {/* Biển tên */}
      <rect
        x="34"
        y="-52"
        width="169"
        height="43"
        rx="18"
        fill="#FFFDF7"
        stroke={active ? "#FF8B3D" : "#F4DFC8"}
        strokeWidth={active ? 3 : 1.5}
      />
      <text x="49" y="-34" fontSize="12" fontWeight="900" fill="#493F3D">
        {room.icon} {room.name}
      </text>
      <text x="50" y="-19" fontSize="10" fill="#8B857F">
        {active ? "🤖 Agent đang kiểm tra..." : finished ? "✓ Đã ghé thăm" : "Hoạt động bình thường"}
      </text>

      {/* Mã ISO */}
      <rect x="91" y="165" width="62" height="23" rx="12" fill="#FFF9EE"/>
      <text
        x="122"
        y="180"
        textAnchor="middle"
        fontSize="11"
        fontWeight="bold"
        fill="#A66845"
      >
        {room.control}
      </text>
    </g>
  );
}

// ======================================================
// MASCOT AGENT ĐANG BAY
// ======================================================

function FloatingAgent({ position, working }) {
  return (
    <g
      style={{
        transform: `translate(${position.x}px, ${position.y}px)`,
        transition: "transform 1.4s cubic-bezier(.22,.9,.28,1)",
      }}
    >
      <g className="agent-bob">
        <ellipse cx="0" cy="30" rx="25" ry="8" fill="#A36A49" opacity=".2"/>

        {/* Phản lực bay */}
        <path d="M-8 18 L-4 36 L0 22 L4 36 L9 18" fill="#FFD78B" opacity=".85"/>

        {/* Tay và thân */}
        <rect x="-23" y="-9" width="46" height="43" rx="19" fill="#FF9A60" stroke="#FFF9EA" strokeWidth="4"/>
        <rect x="-32" y="0" width="11" height="23" rx="6" fill="#FFAC6F"/>
        <rect x="21" y="0" width="11" height="23" rx="6" fill="#FFAC6F"/>
        <rect x="-10" y="11" width="20" height="13" rx="6" fill="#FFF0D1"/>

        {/* Đầu robot */}
        <rect x="-30" y="-43" width="60" height="48" rx="21" fill="#FFF8EF" stroke="#FF9A60" strokeWidth="4"/>
        <rect x="-22" y="-32" width="44" height="28" rx="12" fill="#435969"/>

        <ellipse cx="-10" cy="-20" rx="4" ry="5" fill="#FFF"/>
        <ellipse cx="10" cy="-20" rx="4" ry="5" fill="#FFF"/>
        <path d="M-7 -10 Q0 -4 7 -10" stroke="#FFE7B5" strokeWidth="3" fill="none" strokeLinecap="round"/>

        {/* Antenna */}
        <path d="M0 -43 V-55" stroke="#8495A0" strokeWidth="3"/>
        <circle cx="0" cy="-58" r="6" fill="#FFCB7E"/>

        {working && (
          <>
            <circle cx="0" cy="-58" r="12" fill="none" stroke="#FFF" strokeDasharray="4 4" className="spin-slow"/>
            <circle cx="0" cy="0" r="48" fill="none" stroke="#FFF1BE" strokeWidth="2" strokeOpacity=".5" className="agent-halo"/>
          </>
        )}
      </g>
    </g>
  );
}

// ======================================================
// BẢN ĐỒ CĂN CỨ SAO HỎA
// ======================================================

function EnterpriseMap({ activeRoom, visited }) {
  const position = AGENT_POSITIONS[activeRoom] || AGENT_POSITIONS.home;

  return (
    <svg
      viewBox="0 0 1000 650"
      preserveAspectRatio="xMidYMid meet"
      className="block h-full w-full min-w-[720px]"
      role="img"
      aria-label="Bản đồ doanh nghiệp Sao Hỏa với bốn phòng ban và robot AI di chuyển"
    >
      <defs>
        <linearGradient id="mars-ground" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#8A8290"/>
          <stop offset="36%" stopColor="#E6A675"/>
          <stop offset="100%" stopColor="#F6BB7E"/>
        </linearGradient>

        <radialGradient id="mars-sand">
          <stop offset="0%" stopColor="#FFD8A4"/>
          <stop offset="72%" stopColor="#F5B679"/>
          <stop offset="100%" stopColor="#DC935F"/>
        </radialGradient>

        <pattern
          id="sandgrid"
          patternUnits="userSpaceOnUse"
          width="38"
          height="38"
          patternTransform="skewX(-30) rotate(13)"
        >
          <path d="M38 0 H0 V38" fill="none" stroke="#A8704C" strokeOpacity=".12"/>
        </pattern>
      </defs>

      {/* Nền và mặt đất */}
      <rect width="1000" height="650" fill="url(#mars-ground)"/>

      <ellipse
        cx="525"
        cy="740"
        rx="790"
        ry="650"
        fill="url(#mars-sand)"
        stroke="#FFD7A8"
        strokeWidth="12"
      />

      <ellipse cx="520" cy="480" rx="600" ry="280" fill="url(#sandgrid)"/>

      {/* Các hố Sao Hỏa */}
      <ellipse cx="136" cy="547" rx="55" ry="24" fill="#D78F60" opacity=".35" transform="rotate(-24 136 547)"/>
      <ellipse cx="875" cy="523" rx="61" ry="27" fill="#CF8457" opacity=".25" transform="rotate(-25 875 523)"/>
      <ellipse cx="660" cy="112" rx="35" ry="13" fill="#D28F64" opacity=".26"/>

      {/* Đường nối các phòng */}
      <path
        d="M180 410 Q265 295 434 228 Q595 160 825 365 Q825 490 613 553 Q391 600 180 410"
        fill="none"
        stroke="#FFF2D3"
        strokeWidth="9"
        strokeDasharray="15 17"
        strokeLinecap="round"
        opacity=".83"
      />

      {/* Vật thể trang trí */}
      {[
        [78, 170, 13], [910, 210, 14],
        [280, 548, 17], [700, 580, 11],
      ].map(([x, y, r], index) => (
        <g key={index}>
          <ellipse cx={x} cy={y + 7} rx={r + 5} ry={r / 2} fill="#9F7352" opacity=".25"/>
          <polygon
            points={`${x},${y-r} ${x+r},${y} ${x+3},${y+r/2} ${x-r},${y}`}
            fill="#CC865A"
          />
        </g>
      ))}

      {/* Mặt trăng xanh */}
      <circle cx="899" cy="78" r="44" fill="#70BED2"/>
      <ellipse cx="889" cy="61" rx="25" ry="9" fill="#A3DFEA" transform="rotate(-22 889 61)"/>
      <ellipse cx="916" cy="91" rx="16" ry="7" fill="#95D7B7"/>

      {/* Drone bay qua căn cứ */}
      <g>
        <animateMotion
          path="M90 140 Q470 20 890 180 Q530 90 90 140"
          dur="18s"
          repeatCount="indefinite"
        />
        <ellipse rx="27" ry="9" fill="#FFF9E8"/>
        <rect x="-12" y="-7" width="24" height="11" rx="6" fill="#84CDE1"/>
        <circle cx="0" cy="-2" r="3" fill="#FFF"/>
        <path d="M-24 -4 H-39 M24 -4 H39" stroke="#FFF9E8" strokeWidth="5" strokeLinecap="round"/>
      </g>

      {/* Diorama không phải nút bấm */}
      {ROOMS.map(room => (
        <DioramaRoom
          key={room.id}
          room={room}
          active={activeRoom === room.id}
          finished={visited.includes(room.id)}
        />
      ))}

      {/* Mascot tự bay khi nhiệm vụ thay đổi */}
      <FloatingAgent
        position={position}
        working={activeRoom !== "home"}
      />
    </svg>
  );
}

// ======================================================
// CHAT MESSAGES
// ======================================================

function ChatMessage({ message }) {
  const isAgent = message.sender === "agent";

  return (
    <div className={`flex gap-2.5 ${isAgent ? "" : "justify-end"}`}>
      {isAgent && (
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl bg-[#FF9854]">
          <Bot size={21} color="white"/>
        </div>
      )}

      <div
        className={
          "max-w-[88%] rounded-[19px] px-4 py-3 " +
          (isAgent
            ? "rounded-tl-sm border border-white/10 bg-[#34475D] text-[#EEF2F6]"
            : "rounded-tr-sm bg-[#FF8F42] text-white")
        }
      >
        <p className="whitespace-pre-wrap text-[13px] leading-[1.65]">
          {message.content}
        </p>

        <p className={`mt-2 text-[10px] ${isAgent ? "text-slate-400" : "text-orange-100"}`}>
          {message.time}
        </p>
      </div>
    </div>
  );
}

// ======================================================
// MAIN APP
// ======================================================

export default function SpaceBaseDashboard({
    request,
    assessment,
    }) {
  const [status, setStatus] = useState("idle");
  const [activeRoom, setActiveRoom] = useState("home");
  const [visited, setVisited] = useState([]);
  const [evidence, setEvidence] = useState(null);

  const [logs, setLogs] = useState([]);
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: "agent",
      content:
        "Xin chào Sếp! 🧡\nTôi là ISO-BOT, trợ lý kiểm toán tự động.\n\nNhấn nút Auto-Audit để tôi bắt đầu khảo sát doanh nghiệp nhé!",
      time: "Sẵn sàng",
    },
  ]);

  const [chatInput, setChatInput] = useState("");
  const [fileError, setFileError] = useState("");
  const [dragging, setDragging] = useState(false);

  const timers = useRef([]);
  const logBox = useRef(null);
  const chatBox = useRef(null);
  const inputFile = useRef(null);
  const nextId = useRef(2);

  const now = () =>
    new Date().toLocaleTimeString("vi-VN", {
      hour12: false,
    });

  const addLog = (type, text) => {
    setLogs(prev => [
      ...prev,
      {
        id: nextId.current++,
        type,
        text,
        time: now(),
      },
    ]);
  };

  const addMessage = (sender, content) => {
    setMessages(prev => [
      ...prev,
      {
        id: nextId.current++,
        sender,
        content,
        time: now(),
      },
    ]);
  };

  const clearTimers = () => {
    timers.current.forEach(id => clearTimeout(id));
    timers.current = [];
  };

  const schedule = (callback, delay) => {
    const id = setTimeout(callback, delay);
    timers.current.push(id);
  };

  useEffect(() => {
    return () => {
      timers.current.forEach(id => clearTimeout(id));
    };
  }, []);

  useEffect(() => {
    if (logBox.current) {
      logBox.current.scrollTop = logBox.current.scrollHeight;
    }
  }, [logs]);

  useEffect(() => {
    if (chatBox.current) {
      chatBox.current.scrollTop = chatBox.current.scrollHeight;
    }
  }, [messages, status]);

  // ====================================================
  // MỘT NÚT KHỞI ĐỘNG TOÀN BỘ WORKFLOW DEMO
  // ====================================================


async function startAudit() {
  if (status === "running" || status === "waiting") return;

  clearTimers();

  setStatus("running");
  setActiveRoom("hr");
  setVisited([]);
  setLogs([]);
  setEvidence(null);
  setFileError("");

  addMessage(
    "agent",
    "🚀 Tôi bắt đầu kiểm tra A.6.1 bằng FastAPI và Agent thật. Sếp có thể theo dõi trạng thái xử lý ở Não bộ AI."
  );

  try {
    const result = await runA61Pilot({
      request,
      assessmentId: assessment.assessment_id,
      onEvent: ({ type, text }) => addLog(type, text),
    });

    if (result.outcome === "waiting") {
      setStatus("waiting");

      addMessage(
        "agent",
        "Sếp ơi, backend báo rằng A.6.1 cần thêm bằng chứng. Tôi đang tạm dừng control này để chờ tài liệu phù hợp."
      );
      return;
    }

    setVisited(["hr"]);
    setStatus("completed");

    addMessage(
      "agent",
      `Job A.6.1 đã kết thúc xử lý.\nMã job: ${result.jobId}\n\nKết quả đánh giá ISO cần được đọc và xác minh từ backend.`
    );
  } catch (error) {
    setStatus("idle");

    addLog(
      "warning",
      error.message || "Không thể chạy Agent."
    );

    addMessage(
      "agent",
      `Tôi gặp lỗi khi thực hiện nhiệm vụ:\n${error.message}`
    );
  }
}


  // ====================================================
  // AGENT TIẾP TỤC SAU KHI ĐƯỢC CẤP BẰNG CHỨNG
  // ====================================================

  function receiveEvidence(file) {
    if (!file || status !== "waiting") return;

    const extensionOkay = /\.(pdf|docx|doc)$/i.test(file.name);
    const sizeOkay = file.size <= 15 * 1024 * 1024;

    if (!extensionOkay) {
      setFileError("Chỉ hỗ trợ tài liệu PDF, DOC hoặc DOCX.");
      return;
    }

    if (!sizeOkay) {
      setFileError("File vượt quá 15 MB.");
      return;
    }

    clearTimers();
    setFileError("");
    setEvidence({ name: file.name, size: file.size });
    setStatus("running");

    addMessage("user", `📎 Đã chọn tài liệu: ${file.name}`);

    addMessage(
      "agent",
      "Cảm ơn Sếp! Tôi đã ghi nhận tài liệu cho phiên mô phỏng. Tôi sẽ tiếp tục khảo sát các phòng ban.\n\nLưu ý: bản demo chưa đọc hoặc phân tích nội dung thực tế của file."
    );

    addLog(
      "tool",
      `Đã chọn file "${file.name}" — chưa tải lên server, chưa phân tích nội dung.`
    );

    schedule(() => {
      addLog(
        "review",
        "Mô phỏng bước đối chiếu tiêu chí A.6.1; chờ bộ phân tích tài liệu thật ở backend."
      );
      setVisited(["hr"]);
    }, 900);

    schedule(() => {
      setActiveRoom("accounting");

      addLog(
        "action",
        "Agent bay đến Phòng Kế toán."
      );
    }, 1700);

    schedule(() => {
      addLog(
        "tool",
        "Mô phỏng: accounting.collect_documents()"
      );

      addLog(
        "execute",
        "Đang khảo sát tài liệu tài chính và quyền truy cập."
      );
    }, 2550);

    schedule(() => {
      setVisited(["hr", "accounting"]);
      setActiveRoom("management");

      addLog(
        "action",
        "Agent chuyển đến Phòng Quản lý."
      );
    }, 3550);

    schedule(() => {
      addLog(
        "execute",
        "Mô phỏng kiểm tra chính sách, trách nhiệm và phê duyệt."
      );
    }, 4300);

    schedule(() => {
      setVisited(["hr", "accounting", "management"]);
      setActiveRoom("warehouse");

      addLog(
        "action",
        "Agent di chuyển đến Nhà Kho."
      );
    }, 5200);

    schedule(() => {
      addLog(
        "tool",
        "Mô phỏng: physical.inspect_asset_inventory()"
      );
    }, 6050);

    schedule(() => {
      setVisited(ROOMS.map(room => room.id));
      setStatus("completed");

      addLog(
        "success",
        "Hoàn thành mô phỏng khảo sát 4 phòng ban. Chưa có kết luận tuân thủ ISO chính thức."
      );

      addMessage(
        "agent",
        "🎉 Báo cáo Sếp!\n\nTôi đã hoàn thành hành trình mô phỏng qua 4 phòng ban.\n\nĐể có kết quả đánh giá ISO thực tế, cần kết nối với FastAPI, kiểm chứng evidence và lưu kết luận vào PostgreSQL."
      );
    }, 7250);
  }

  function handleDrop(event) {
    event.preventDefault();
    setDragging(false);

    receiveEvidence(event.dataTransfer.files?.[0]);
  }

  function sendMessage(event) {
    event.preventDefault();

    const value = chatInput.trim();
    if (!value) return;

    addMessage("user", value);
    setChatInput("");

    schedule(() => {
      if (status === "waiting") {
        addMessage(
          "agent",
          "Tôi đã ghi nhận lời nhắn của Sếp. Hiện mục A.6.1 vẫn đang thiếu tài liệu. Sếp có thể cung cấp file ngay trong khung chat nhé!"
        );
      } else {
        addMessage(
          "agent",
          "Tôi đã ghi nhận tin nhắn trong giao diện demo. Chức năng hội thoại AI thật sẽ được kết nối với backend sau."
        );
      }
    }, 450);
  }

  const activeRoomName =
    ROOMS.find(room => room.id === activeRoom)?.name ||
    "Trung tâm điều hành";

  const isBusy = status === "running";
  const awaitingEvidence = status === "waiting";

  return (
    <div
      className="relative min-h-screen overflow-hidden bg-[#111E30] text-white"
      style={{
        fontFamily:
          'ui-rounded, "Trebuchet MS", Inter, system-ui, sans-serif',
      }}
    >
      <style>{`
        @keyframes robotBob {
          0%,100% { transform:translateY(0); }
          50% { transform:translateY(-9px); }
        }
        @keyframes roomPulse {
          0%,100% { opacity:.25; }
          50% { opacity:.75; }
        }
        @keyframes spinSlow {
          to { transform:rotate(360deg); }
        }
        @keyframes dots {
          0%,60%,100% { opacity:.25; }
          30% { opacity:1; }
        }
        .agent-bob { animation:robotBob 2s ease-in-out infinite; }
        .room-pulse { animation:roomPulse 1.7s ease-in-out infinite; }
        .spin-slow {
          transform-box:fill-box;
          transform-origin:center;
          animation:spinSlow 5s linear infinite;
        }
        .agent-halo { animation:roomPulse 2s infinite; }
        .scroll-soft::-webkit-scrollbar { width:5px; height:5px; }
        .scroll-soft::-webkit-scrollbar-thumb {
          background:#566779; border-radius:12px;
        }
        @media(prefers-reduced-motion:reduce) {
          .agent-bob,.room-pulse,.spin-slow,.agent-halo { animation:none; }
        }
      `}</style>

      {/* Background */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_50%_45%,#2C3B54_0%,#152339_65%,#101B2D_100%)]"/>

      {/* HEADER */}
      <header className="relative z-20 mx-auto flex max-w-[1900px] flex-wrap items-center justify-between gap-4 px-5 py-5">
        <div className="flex items-center gap-3">
          <div className="flex h-13 w-13 items-center justify-center rounded-[19px] bg-[#FF8F44] shadow-lg">
            <Bot size={29}/>
          </div>

          <div>
            <h1 className="text-lg font-black tracking-wide md:text-xl">
              ISO ENTERPRISE LAB
            </h1>
            <p className="text-[11px] font-bold text-[#A7BACB]">
              AUTONOMOUS AI TYCOON • ISO/IEC 27001:2022
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-full border border-white/10 bg-[#2B4054] px-4 py-2.5 text-xs font-bold">
          <span
            className={`h-2.5 w-2.5 rounded-full ${
              status === "waiting" ? "bg-amber-400" :
              status === "running" ? "animate-pulse bg-orange-400" :
              "bg-emerald-400"
            }`}
          />
          {STATUS_NAMES[status]}
        </div>
      </header>

      {/* RESOURCE HUD */}
      <div className="relative z-10 mx-auto mb-4 grid max-w-[1900px] grid-cols-2 gap-3 px-4 md:grid-cols-4">
        {[
          { label: "Phạm vi kiểm toán", value: "56 Controls", Icon: ShieldCheck },
          { label: "Phòng ban", value: "4 khu vực", Icon: Building2 },
          { label: "Agent đang hoạt động", value: isBusy ? "1" : "0", Icon: Bot },
          { label: "Khu vực đã khảo sát", value: `${visited.length}/4`, Icon: CheckCircle2 },
        ].map(metric => (
          <Panel key={metric.label} className="flex items-center gap-3 p-3 md:p-4">
            <div className="rounded-2xl bg-white/[.07] p-2.5 text-[#FFBC83]">
              <metric.Icon size={23}/>
            </div>
            <div>
              <div className="text-[10px] font-semibold text-slate-400 md:text-xs">
                {metric.label}
              </div>
              <div className="mt-1 text-lg font-black">
                {metric.value}
              </div>
            </div>
          </Panel>
        ))}
      </div>

      {/* MAIN INTERFACE */}
      <main className="relative z-10 mx-auto grid max-w-[1900px] grid-cols-1 gap-4 px-4 pb-8 xl:grid-cols-[275px_minmax(0,1fr)_350px]">

        {/* LEFT — EXECUTION LOG */}
        <Panel className="order-2 flex min-h-[360px] flex-col overflow-hidden p-4 xl:order-1 xl:h-[690px]">
          <div className="flex items-center gap-3 border-b border-white/10 pb-4">
            <div className="rounded-2xl bg-[#FF9147]/15 p-2.5 text-[#FFC18D]">
              <Terminal size={22}/>
            </div>
            <div>
              <h2 className="text-sm font-black">
                NÃO BỘ AI
              </h2>
              <p className="text-[11px] text-slate-400">
                Nhật ký thực thi · Demo
              </p>
            </div>
          </div>

          <div className="mt-3 flex items-center justify-between rounded-xl bg-[#0E1B2A] px-3 py-2 text-[10px]">
            <span className="font-mono text-slate-400">
              auto-audit / events
            </span>
            <span className="flex items-center gap-1.5 text-emerald-300">
              <span className="h-2 w-2 rounded-full bg-emerald-400"/>
              MONITOR
            </span>
          </div>

          <div
            ref={logBox}
            className="scroll-soft mt-3 min-h-0 flex-1 space-y-3 overflow-y-auto rounded-2xl bg-[#0D1927]/70 p-3 font-mono"
            aria-live="polite"
          >
            {logs.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
                <BrainCircuit size={33} className="text-slate-500"/>
                <p className="text-xs leading-relaxed text-slate-400">
                  Não bộ AI đang chờ lệnh.
                  <br/>
                  Khởi động Auto-Audit để xem nhật ký.
                </p>
              </div>
            ) : (
              logs.map(log => {
                const style = LOG_STYLES[log.type];

                return (
                  <div key={log.id} className="border-l-2 border-white/10 pl-3">
                    <div className="flex items-center gap-2">
                      <span className={`h-1.5 w-1.5 rounded-full ${style.dot}`}/>
                      <span className={`text-[10px] font-bold ${style.color}`}>
                        [{style.name}]
                      </span>
                      <span className="ml-auto text-[9px] text-slate-500">
                        {log.time}
                      </span>
                    </div>

                    <p className="mt-1.5 break-words text-[11px] leading-relaxed text-[#D3DEE8]">
                      {log.text}
                    </p>
                  </div>
                );
              })
            )}

            {isBusy && (
              <div className="flex items-center gap-2 text-[11px] text-orange-300">
                <Loader2 size={13} className="animate-spin"/>
                Đang xử lý nhiệm vụ...
              </div>
            )}
          </div>

          <div className="mt-3 rounded-xl border border-amber-300/15 bg-amber-300/5 p-3 text-[10px] leading-relaxed text-[#ADBCC9]">
            <AlertCircle size={13} className="mr-1 inline text-amber-300"/>
            Đây là log sự kiện mô phỏng, không phải suy luận nội bộ hoặc lệnh tool thực tế từ LLM.
          </div>
        </Panel>

        {/* CENTER — AUTONOMOUS ENTERPRISE */}
        <div className="order-1 flex min-w-0 flex-col gap-3 xl:order-2">
          <div className="relative h-[540px] overflow-x-auto overflow-y-hidden rounded-[34px] border-[3px] border-[#F4B47F]/50 bg-[#EBA36B] shadow-xl xl:h-[620px]">
            <div className="absolute left-5 top-5 z-10 rounded-full bg-[#FFF8E9]/95 px-4 py-2.5 text-xs font-black text-[#9B6445] shadow-md">
              🪐 DOANH NGHIỆP SAO HỎA
            </div>

            <EnterpriseMap
              activeRoom={activeRoom}
              visited={visited}
            />

            <div className="absolute bottom-4 left-4 z-10 rounded-2xl bg-[#FFF9EB]/95 px-4 py-3 text-[#83583F] shadow-md">
              <p className="text-[10px] font-black uppercase tracking-widest">
                Vị trí AI Agent
              </p>
              <p className="mt-1 text-sm font-black">
                {activeRoomName}
              </p>
            </div>
          </div>

          {/* NÚT AUTO-AUDIT DUY NHẤT */}
          <button
            type="button"
            onClick={startAudit}
            disabled={isBusy || awaitingEvidence}
            className={
              "group flex w-full items-center justify-center gap-3 " +
              "rounded-full border-[3px] border-[#FFC590] " +
              "bg-gradient-to-r from-[#FF7E29] via-[#FF933D] to-[#FFA353] " +
              "px-5 py-5 text-center text-sm font-black text-white " +
              "shadow-[0_7px_0_#B65D2D,0_15px_34px_rgba(255,130,50,.19)] " +
              "transition-transform hover:-translate-y-0.5 active:translate-y-1 " +
              "disabled:cursor-not-allowed disabled:opacity-65 " +
              "md:text-base"
            }
          >
            {isBusy ? (
              <>
                <Loader2 size={25} className="shrink-0 animate-spin"/>
                AGENT ĐANG TỰ ĐỘNG KIỂM TOÁN...
              </>
            ) : awaitingEvidence ? (
              <>
                <Paperclip size={23}/>
                ĐANG CHỜ SẾP CUNG CẤP BẰNG CHỨNG
              </>
            ) : (
              <>
                <Rocket size={27} className="shrink-0 transition-transform group-hover:-translate-y-1"/>
                🚀 KHỞI ĐỘNG KIỂM TOÁN TOÀN DIỆN (AUTO-AUDIT)
              </>
            )}
          </button>

          <div className="text-center text-[11px] text-[#A9BACA]">
            {status === "completed"
              ? "Đã hoàn tất bản trình diễn. Có thể chạy lại để thử workflow."
              : "Một nút khởi động • AI Agent tự xử lý • Chỉ hỏi khi thiếu bằng chứng"}
            <span className="ml-1 text-orange-300">· DEMO</span>
          </div>
        </div>

        {/* RIGHT — AGENT CHAT */}
        <Panel className="order-3 flex min-h-[550px] flex-col overflow-hidden p-4 xl:h-[690px]">
          <div className="flex items-center gap-3 border-b border-white/10 pb-4">
            <div className="relative flex h-12 w-12 items-center justify-center rounded-[19px] bg-[#FF9758]">
              <Bot size={27}/>
              <span className="absolute -bottom-0.5 -right-0.5 h-3.5 w-3.5 rounded-full border-[3px] border-[#203348] bg-emerald-400"/>
            </div>

            <div className="min-w-0 flex-1">
              <h2 className="font-black">
                ISO-BOT
              </h2>
              <p className="text-[11px] text-slate-400">
                Chuyên viên kiểm toán AI
              </p>
            </div>

            <div className="rounded-full bg-white/[.07] px-2.5 py-1.5 text-[10px] font-bold text-emerald-300">
              {status === "waiting" ? "CẦN SẾP" : "ONLINE"}
            </div>
          </div>

          <div className="my-3 flex items-center gap-2 rounded-2xl bg-[#2B3E54] p-3 text-[11px] text-slate-300">
            <Activity size={16} className="text-orange-300"/>
            <span>
              {STATUS_NAMES[status]}
            </span>
          </div>

          {/* Chat history */}
          <div
            ref={chatBox}
            className="scroll-soft min-h-0 flex-1 space-y-4 overflow-y-auto pr-1"
            aria-live="polite"
          >
            {messages.map(message => (
              <ChatMessage
                key={message.id}
                message={message}
              />
            ))}

            {isBusy && (
              <div className="flex items-center gap-2 text-xs text-[#B9C8D8]">
                <Bot size={16} className="text-[#FFB57C]"/>
                <Loader2 size={15} className="animate-spin"/>
                ISO-BOT đang làm việc...
              </div>
            )}

            {/* EVIDENCE DROPZONE INSIDE CHAT */}
            {awaitingEvidence && (
              <div
                onDragOver={event => {
                  event.preventDefault();
                  setDragging(true);
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
                className={
                  "rounded-[22px] border-2 border-dashed p-4 text-center transition-colors " +
                  (dragging
                    ? "border-[#FFB87B] bg-[#FF994F]/20"
                    : "border-[#FFB87B]/60 bg-[#FF9649]/10")
                }
              >
                <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#FF974D]/20 text-[#FFC28D]">
                  <UploadCloud size={27}/>
                </div>

                <h3 className="text-sm font-black">
                  Cung cấp bằng chứng A.6.1
                </h3>

                <p className="mt-2 text-xs leading-relaxed text-slate-300">
                  Kéo thả quy trình kiểm tra lý lịch nhân viên hoặc chọn file PDF/Word.
                </p>

                <button
                  type="button"
                  onClick={() => inputFile.current?.click()}
                  className="mt-3 inline-flex items-center gap-2 rounded-full bg-[#FF9148] px-5 py-2.5 text-xs font-black text-white hover:bg-[#F47B35]"
                >
                  <FileUp size={16}/>
                  TẢI FILE CHO AGENT
                </button>

                <input
                  ref={inputFile}
                  className="hidden"
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={event => {
                    receiveEvidence(event.target.files?.[0]);
                    event.target.value = "";
                  }}
                />

                <p className="mt-2 text-[10px] text-slate-400">
                  PDF, DOC, DOCX • Tối đa 15 MB
                </p>

                {fileError && (
                  <p className="mt-2 text-xs font-bold text-red-300">
                    {fileError}
                  </p>
                )}
              </div>
            )}

            {evidence && (
              <div className="rounded-xl border border-emerald-400/20 bg-emerald-400/10 p-3">
                <div className="flex items-center gap-2 text-xs text-emerald-300">
                  <CheckCircle2 size={17}/>
                  Đã nhận file trong demo
                </div>

                <p className="mt-1 break-all text-[11px] text-slate-300">
                  {evidence.name}
                </p>
              </div>
            )}
          </div>

          {/* Chat input */}
          <form onSubmit={sendMessage} className="mt-4 border-t border-white/10 pt-3">
            <div className="flex items-center gap-2 rounded-[22px] border border-white/10 bg-[#102034] p-2">
              <MessageCircle size={17} className="ml-2 shrink-0 text-slate-400"/>

              <input
                value={chatInput}
                onChange={event => setChatInput(event.target.value)}
                placeholder="Nhắn tin cho ISO-BOT..."
                aria-label="Tin nhắn cho ISO-BOT"
                className="min-w-0 flex-1 bg-transparent px-1 py-2 text-xs text-white outline-none placeholder:text-slate-500"
              />

              <button
                type="submit"
                disabled={!chatInput.trim()}
                className="flex h-9 w-9 items-center justify-center rounded-full bg-[#FF8B43] disabled:opacity-40"
                aria-label="Gửi tin nhắn"
              >
                <ArrowUp size={18}/>
              </button>
            </div>

            <p className="mt-2 text-center text-[10px] text-slate-500">
              Chat demo • Chưa kết nối mô hình ngôn ngữ
            </p>
          </form>
        </Panel>
      </main>

      <footer className="relative z-10 mx-auto flex max-w-[1900px] flex-wrap justify-between gap-2 px-5 pb-5 text-[10px] text-slate-500">
        <span>ISO ENTERPRISE LAB • AUTONOMOUS AI TYCOON</span>
        <span>Prototype UI · Dữ liệu và nhiệm vụ mô phỏng</span>
      </footer>
    </div>
  );
}
