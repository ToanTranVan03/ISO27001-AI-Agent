import BaseLife, { AgentCrewPanel } from "./BaseLife";
import React, { useCallback, useEffect, useState } from "react";
import {
  Activity, BarChart3, Bot, Building2, CheckCircle2,
  ChevronRight, Clock3, FileCheck2, FileUp, LayoutDashboard,
  Loader2, Map as MapIcon, Radar, Rocket, Shield, Sparkles, Target,
  Thermometer, UploadCloud, Users, X
} from "lucide-react";

// =========================================================
// ISO CONTROL DATA — 8 + 14 + 34 = 56
// =========================================================

const CONTROLS = {
  "A.6": [
    "Screening",
    "Terms and conditions of employment",
    "Information security awareness, education and training",
    "Disciplinary process",
    "Responsibilities after termination or change of employment",
    "Confidentiality or non-disclosure agreements",
    "Remote working",
    "Information security event reporting",
  ],
  "A.7": [
    "Physical security perimeters",
    "Physical entry",
    "Securing offices, rooms and facilities",
    "Physical security monitoring",
    "Protecting against physical and environmental threats",
    "Working in secure areas",
    "Clear desk and clear screen",
    "Equipment siting and protection",
    "Security of assets off-premises",
    "Storage media",
    "Supporting utilities",
    "Cabling security",
    "Equipment maintenance",
    "Secure disposal or re-use of equipment",
  ],
  "A.8": [
    "User endpoint devices",
    "Privileged access rights",
    "Information access restriction",
    "Access to source code",
    "Secure authentication",
    "Capacity management",
    "Protection against malware",
    "Management of technical vulnerabilities",
    "Configuration management",
    "Information deletion",
    "Data masking",
    "Data leakage prevention",
    "Information backup",
    "Redundancy of information processing facilities",
    "Logging",
    "Monitoring activities",
    "Clock synchronization",
    "Use of privileged utility programs",
    "Installation of software on operational systems",
    "Networks security",
    "Security of network services",
    "Segregation of networks",
    "Web filtering",
    "Use of cryptography",
    "Secure development life cycle",
    "Application security requirements",
    "Secure system architecture and engineering principles",
    "Secure coding",
    "Security testing in development and acceptance",
    "Outsourced development",
    "Separation of development, test and production environments",
    "Change management",
    "Test information",
    "Protection of information systems during audit testing",
  ],
};

const ZONES = [
  {
    id: "A.6",
    title: "Con người",
    name: "Tòa nhà Nhân sự",
    subtitle: "Phòng làm việc HR",
    Icon: Users,
    main: "#F4A66C",
    light: "#FFE0B5",
    position: { left: "7%", top: "34%" },
    defaultControl: "A.6.1",
  },
  {
    id: "A.7",
    title: "Môi trường vật lý",
    name: "Khu vực An ninh",
    subtitle: "Trạm bảo vệ",
    Icon: Shield,
    main: "#A3CDB5",
    light: "#DBF2DC",
    position: { left: "54%", top: "25%" },
    defaultControl: "A.7.1",
  },
  {
    id: "A.8",
    title: "Công nghệ",
    name: "Trung tâm Dữ liệu",
    subtitle: "Phòng điều khiển",
    Icon: Building2,
    main: "#B9B2E5",
    light: "#E9E4FF",
    position: { left: "35%", top: "57%" },
    defaultControl: "A.8.5",
  },
];

const ALL_CONTROLS = Object.entries(CONTROLS).flatMap(
  ([group, titles]) =>
    titles.map((title, i) => ({
      id: `${group}.${i + 1}`,
      title,
      group,
    }))
);

const DESCRIPTIONS = {
  "A.6.1":
    "Thẩm tra lý lịch và năng lực của nhân sự trước khi tuyển dụng để đảm bảo sự tin cậy.",
  "A.7.1":
    "Thiết lập và bảo vệ khu vực vật lý chứa thông tin, thiết bị và các tài sản quan trọng.",
  "A.8.5":
    "Triển khai quy trình và công nghệ xác thực an toàn phù hợp với yêu cầu kiểm soát truy cập.",
  "A.8.13":
    "Duy trì, kiểm tra và bảo vệ các bản sao lưu thông tin và hệ thống.",
};



// =========================================================
// UI COMPONENTS
// =========================================================

function Panel({ children, className = "" }) {
  return (
    <section
      className={
        "rounded-[30px] border border-white/10 " +
        "bg-[#203044]/95 shadow-xl shadow-[#18212b]/20 " +
        "backdrop-blur-xl " + className
      }
    >
      {children}
    </section>
  );
}

function TinyStars() {
  const dots = Array.from({ length: 35 }, (_, i) => ({
    x: (i * 67.7) % 100,
    y: (i * 39.3) % 100,
  }));

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {dots.map((dot, i) => (
        <span
          key={i}
          className="absolute h-[2px] w-[2px] rounded-full bg-white/60"
          style={{ left: `${dot.x}%`, top: `${dot.y}%` }}
        />
      ))}
    </div>
  );
}

// =========================================================
// CUTE DIORAMA ROOM — SVG WITH GLASS WALLS
// =========================================================

function DioramaRoom({ zone, active, onClick, running }) {
  const uid = zone.id.replaceAll(".", "");
  const isHR = zone.id === "A.6";
  const isSecurity = zone.id === "A.7";
  const isTech = zone.id === "A.8";

  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={`Chọn ${zone.name}`}
      className={
        "group absolute z-10 w-[270px] cursor-pointer " +
        "transition-transform duration-300 hover:z-30 hover:scale-105"
      }
      style={zone.position}
    >
      {/* Floating white tooltip */}
      <div className="absolute bottom-[94%] left-1/2 z-40 w-[235px] -translate-x-1/2 pb-3">
        <div
          className={
            "relative rounded-[20px] border-2 border-white " +
            "bg-[#FFFDF8] px-4 py-3 text-left text-[#34404D] " +
            "shadow-[0_8px_0_rgba(92,61,43,.10),0_12px_24px_rgba(86,60,48,.18)]"
          }
        >
          <div className="flex items-start gap-2">
            <span className="mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full bg-[#6BBF93]" />
            <div>
              <div className="text-[13px] font-black">
                {zone.name}
              </div>
              <div className="mt-1 text-[11px] font-semibold leading-relaxed text-[#84909B]">
                {running
                  ? "🤖 AI Agent đang làm việc..."
                  : isHR
                    ? "Nhân viên đang xử lý hồ sơ"
                    : isSecurity
                      ? "Robot đang tuần tra an ninh"
                      : "Robot đang vận hành máy chủ"}
              </div>
            </div>
          </div>
          <span className="absolute -bottom-2 left-1/2 h-4 w-4 -translate-x-1/2 rotate-45 bg-[#FFFDF8]" />
        </div>
      </div>

      <svg
        viewBox="0 0 300 250"
        className="relative z-10 w-full overflow-visible"
        style={{
          filter: "drop-shadow(0 18px 10px rgba(91,65,48,.23))",
          transform: active ? "translateY(-8px)" : "translateY(0)",
          transition: "transform .25s ease",
        }}
      >
        <defs>
          <linearGradient id={`floor-${uid}`} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#FFF4DA" />
            <stop offset="100%" stopColor={zone.light} />
          </linearGradient>

          <linearGradient id={`glass-${uid}`} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#FFFFFF" stopOpacity=".45" />
            <stop offset="100%" stopColor="#DDF5F9" stopOpacity=".08" />
          </linearGradient>
        </defs>

        {/* Soft shadow on Martian ground */}
        <ellipse
          cx="151"
          cy="207"
          rx="125"
          ry="25"
          fill="#8D4F31"
          opacity=".15"
        />

        {/* Thick, rounded-looking isometric platform */}
        <polygon
          points="14,152 147,85 287,153 153,224"
          fill="#FDF2DD"
          stroke="#D9AE84"
          strokeWidth="3"
          strokeLinejoin="round"
        />
        <polygon
          points="14,152 153,224 153,234 14,163"
          fill="#C99A75"
        />
        <polygon
          points="153,224 287,153 287,163 153,234"
          fill="#DEB08A"
        />

        {/* Transparent back walls */}
        <polygon
          points="38,149 38,84 149,27 149,91"
          fill={`url(#glass-${uid})`}
          stroke="#F4FDFF"
          strokeWidth="4"
          strokeOpacity=".8"
        />
        <polygon
          points="149,27 265,87 265,150 149,91"
          fill="#D1EFF6"
          fillOpacity=".3"
          stroke="#F4FDFF"
          strokeWidth="4"
          strokeOpacity=".8"
        />

        {/* Room floor */}
        <polygon
          points="38,149 149,91 265,150 153,208"
          fill={`url(#floor-${uid})`}
          stroke="#F6D9B9"
          strokeWidth="2"
        />

        {/* Floor mat */}
        <polygon
          points="67,154 143,114 228,157 151,197"
          fill={zone.light}
          opacity=".7"
        />

        {/* Decoration on the glass */}
        <path
          d="M38 118 L149 61 L265 120"
          stroke="#FFFFFF"
          strokeWidth="1.5"
          strokeOpacity=".8"
          fill="none"
        />

        {/* Bookshelf / server rack / security desk */}
        {isTech && (
          <g>
            <polygon
              points="208,122 229,111 246,120 224,132"
              fill="#8494B4"
            />
            <polygon
              points="224,132 246,120 246,164 224,177"
              fill="#677A9B"
            />
            <polygon
              points="208,122 224,132 224,177 208,167"
              fill="#8F9FC0"
            />
            {[137, 149, 161].map((y) => (
              <g key={y}>
                <rect
                  x="212"
                  y={y}
                  width="7"
                  height="3"
                  rx="1.5"
                  fill="#9EF0C1"
                />
                <circle cx="222" cy={y + 1} r="1.5" fill="#FFE2A4" />
              </g>
            ))}
          </g>
        )}

        {isSecurity && (
          <g>
            <rect x="201" y="110" width="28" height="29" rx="6" fill="#D7E5D9" />
            <rect x="206" y="115" width="18" height="15" rx="3" fill="#91BCA6" />
            <circle cx="215" cy="122" r="5" fill="#F8F1CD" />
            <rect x="205" y="136" width="20" height="4" rx="2" fill="#7EA88D" />
          </g>
        )}

        {isHR && (
          <g>
            <rect x="211" y="124" width="24" height="25" rx="4" fill="#E4B78C" />
            <rect x="215" y="129" width="5" height="14" rx="1" fill="#FFF2DB" />
            <rect x="223" y="132" width="5" height="11" rx="1" fill="#91C9A2" />
            <rect x="231" y="127" width="3" height="16" rx="1" fill="#F58B75" />
          </g>
        )}

        {/* Small plant */}
        <g>
          <polygon
            points="71,157 87,149 102,157 86,165"
            fill="#D78B6A"
          />
          <polygon
            points="71,157 86,165 86,177 71,168"
            fill="#E5A17C"
          />
          <polygon
            points="86,165 102,157 102,168 86,177"
            fill="#C77B60"
          />
          <path
            d="M86 154 L86 125 M86 145 Q66 128 74 119 M86 141 Q109 126 101 118"
            stroke="#548F66"
            strokeWidth="4"
            fill="none"
            strokeLinecap="round"
          />
          <ellipse cx="76" cy="123" rx="10" ry="5" fill="#82BB82" transform="rotate(28 76 123)" />
          <ellipse cx="99" cy="120" rx="10" ry="5" fill="#A4D89B" transform="rotate(-32 99 120)" />
          <ellipse cx="86" cy="126" rx="9" ry="13" fill="#6CA976" />
        </g>

        {/* Cute robot employee */}
        <g>
          {/* Legs */}
          <rect x="150" y="150" width="9" height="15" rx="4" fill="#8F9FC4" />
          <rect x="166" y="150" width="9" height="15" rx="4" fill="#8F9FC4" />

          {/* Body */}
          <rect x="146" y="116" width="35" height="39" rx="13" fill={zone.main} stroke="#FFF9EF" strokeWidth="3" />
          <rect x="156" y="125" width="15" height="12" rx="5" fill="#FFF4E4" />
          <circle cx="163" cy="131" r="3" fill="#F7A679" />

          {/* Arms */}
          <rect x="135" y="125" width="12" height="26" rx="6" fill={zone.main} transform="rotate(20 141 138)" />
          <rect x="179" y="122" width="12" height="25" rx="6" fill={zone.main} transform="rotate(-20 185 135)" />

          {/* Ears */}
          <circle cx="143" cy="101" r="9" fill={zone.main} />
          <circle cx="185" cy="101" r="9" fill={zone.main} />

          {/* Robot head */}
          <rect x="138" y="83" width="51" height="42" rx="18" fill="#FFF7EA" stroke={zone.main} strokeWidth="4" />

          {/* Face */}
          <rect x="147" y="94" width="33" height="21" rx="10" fill="#4B6372" />
          <ellipse cx="157" cy="103" rx="3" ry="4" fill="#FFFFFF" />
          <ellipse cx="171" cy="103" rx="3" ry="4" fill="#FFFFFF" />
          <path d="M159 110 Q164 114 169 110" stroke="#FFDC9D" strokeWidth="2" fill="none" strokeLinecap="round" />

          {/* Blush */}
          <circle cx="150" cy="111" r="3" fill="#F7A1A3" opacity=".8" />
          <circle cx="177" cy="111" r="3" fill="#F7A1A3" opacity=".8" />

          {/* Antenna */}
          <path d="M164 83 L164 73" stroke="#7990A0" strokeWidth="3" />
          <circle cx="164" cy="71" r="5" fill="#F9B663" />
        </g>

        {/* Cute desk */}
        <g>
          <polygon
            points="115,154 152,135 202,159 162,181"
            fill="#F6C48E"
            stroke="#D8A779"
            strokeWidth="2"
          />
          <polygon
            points="115,154 162,181 162,188 115,161"
            fill="#DBA779"
          />
          <polygon
            points="162,181 202,159 202,166 162,188"
            fill="#C88F68"
          />

          {/* Laptop */}
          <polygon
            points="142,143 159,134 177,143 160,153"
            fill="#768B9D"
          />
          <polygon
            points="159,134 159,113 177,122 177,143"
            fill="#556B80"
          />
          <polygon
            points="162,119 173,125 173,136 162,130"
            fill="#C8EBDD"
          />
        </g>

        {/* Glass wall framing */}
        <path
          d="M38 149 V84 L149 27 L265 87 V150"
          stroke="#E8FAFC"
          strokeWidth="4"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />

        <path
          d="M149 27 V91"
          stroke="#FFFFFF"
          strokeWidth="3"
          opacity=".7"
        />

        {/* Bottom plate label */}
        <rect x="119" y="217" width="66" height="24" rx="12" fill="#FFF7E9" stroke="#E2BB90" strokeWidth="2" />
        <text
          x="152"
          y="233"
          textAnchor="middle"
          fill="#9E5D3C"
          fontSize="13"
          fontWeight="900"
        >
          {zone.id}
        </text>

        {/* Task status indicator */}
        {active && (
          <circle cx="270" cy="189" r="9" fill="#FF873B" stroke="#FFF4E4" strokeWidth="3" />
        )}
      </svg>
    </button>
  );
}

// =========================================================
// MAIN DASHBOARD
// =========================================================

export default function SpaceBaseDashboard({ user, assessment, request, onLogout }) {
  const [selectedGroup, setSelectedGroup] = useState("A.6");
  const [selectedId, setSelectedId] = useState("A.6.1");
  const [activeTab, setActiveTab] = useState("Tổng quan");
  const [board, setBoard] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [dataError, setDataError] = useState("");
  const [runningId, setRunningId] = useState(null);
  const [activeJobId, setActiveJobId] = useState(null);
  const [launching, setLaunching] = useState(false);
  const [missionStep, setMissionStep] = useState(-1);
  const [marsTemp, setMarsTemp] = useState(-45);
  const [evidenceType, setEvidenceType] = useState("");
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [history, setHistory] = useState([]);
  const [notification, setNotification] = useState("");
  const [showMemberForm, setShowMemberForm] = useState(false);
  const [member, setMember] = useState({ username: "", display_name: "", password: "" });
  const [memberBusy, setMemberBusy] = useState(false);

  const assessmentId = assessment.assessment_id;
  const boardById = new Map(board.map(item => [item.control_id, item]));
  const currentProgress = boardById.get(selectedId);
  const control = currentProgress
    ? { ...currentProgress, id: currentProgress.control_id, title: currentProgress.name }
    : ALL_CONTROLS.find((item) => item.id === selectedId) || ALL_CONTROLS[0];
  const zone = ZONES.find((item) => item.id === selectedGroup) || ZONES[0];
  const totalCompleted = board.filter(c => c.workflow_status === "COMPLETED").length;
  const totalRunning = board.filter(c => c.workflow_status === "RUNNING").length;
  const runningOnMap = board.find(c => c.workflow_status === "RUNNING")?.control_id || runningId;
  const countCompleted = group => board.filter(c =>
    c.control_id.startsWith(group + ".") && c.workflow_status === "COMPLETED").length;
  const statusLabels = {
    NOT_STARTED: "Chưa bắt đầu", RUNNING: "Đang chạy", FAILED: "Chạy lỗi",
    WAITING_EVIDENCE: "Chờ bằng chứng", NEEDS_REVIEW: "Cần xác nhận",
    COMPLETED: "Đã hoàn tất quy trình",
  };

  const reloadBoard = useCallback(async (silent = false) => {
    try {
      const data = await request(`/api/assessments/${assessmentId}/progress`);
      setBoard(data.controls || []);
      setDataError("");
    } catch (err) {
      setDataError(err.message);
      if (!silent) setNotification(`⚠️ ${err.message}`);
    } finally { setDataLoading(false); }
  }, [assessmentId, request]);

  const reloadHistory = useCallback(async (id) => {
    if (!id) return;
    try {
      const rows = await request(`/api/assessments/${assessmentId}/controls/${encodeURIComponent(id)}/history`);
      setHistory(rows.map(row => ({
        control: id, time: row.created_at ? new Date(row.created_at).toLocaleString("vi-VN") : "",
        text: `${row.status} · ${(row.rationale || "").slice(0, 220)}`,
        evidence: Array.isArray(row.evidence_ids) ? row.evidence_ids : [],
      })));
    } catch (err) { setDataError(err.message); }
  }, [assessmentId, request]);

  useEffect(() => {
    reloadBoard();
    const poll = setInterval(() => reloadBoard(true), 3000);
    return () => clearInterval(poll);
  }, [reloadBoard]);

  useEffect(() => { reloadHistory(selectedId); }, [selectedId, reloadHistory]);
  useEffect(() => {
    setEvidenceType(currentProgress?.expected_evidence_types?.[0] || "");
    setFile(null);
  }, [selectedId, currentProgress?.expected_evidence_types?.join("|")]);

  useEffect(() => {
    const weather = setInterval(() => setMarsTemp(n =>
      Math.max(-48, Math.min(-42, n + (Math.random() > 0.5 ? 1 : -1)))), 6000);
    return () => clearInterval(weather);
  }, []);

  // Illustration only. The backend currently exposes job status, not internal LangGraph nodes.
  useEffect(() => {
    if (!runningId) return;
    const animation = setInterval(() => setMissionStep(n => Math.min(4, n + 1)), 1800);
    return () => clearInterval(animation);
  }, [runningId]);

  useEffect(() => {
    if (!activeJobId) return;
    let cancelled = false;
    const pollJob = async () => {
      try {
        const job = await request(`/api/jobs/${activeJobId}`);
        if (cancelled || job.status === "RUNNING") return;
        setRunningId(null);
        setActiveJobId(null);
        setMissionStep(-1);
        setNotification(job.status === "SUCCEEDED"
          ? `✅ Agent đã xử lý ${job.control_id}. Xem kết luận và bằng chứng trong tiến độ.`
          : `⚠️ Agent ${job.control_id} thất bại: ${job.error_message || "Xem log FastAPI"}`);
        reloadBoard(true);
        reloadHistory(job.control_id);
      } catch (err) { if (!cancelled) setDataError(err.message); }
    };
    pollJob();
    const timer = setInterval(pollJob, 3000);
    return () => { cancelled = true; clearInterval(timer); };
  }, [activeJobId, request, reloadBoard, reloadHistory]);

  function selectZone(item) {
    setSelectedGroup(item.id);
    setSelectedId(item.defaultControl);
    setActiveTab("Bản đồ Sao Hỏa");
  }

  function selectControl(item) {
    setSelectedId(item.id);
    setSelectedGroup(item.group);
  }

  async function launchAgent() {
    if (launching || currentProgress?.workflow_status === "RUNNING") return;
    setLaunching(true);
    setDataError("");
    try {
      const job = await request(`/api/assessments/${assessmentId}/controls/${encodeURIComponent(selectedId)}/run`, {
        method: "POST",
      });
      setRunningId(selectedId);
      setMissionStep(0);
      setActiveJobId(job.job_id);
      setNotification(`🚀 Đã tạo job ${job.job_id} cho ${selectedId}. Robot đang di chuyển minh họa.`);
      await reloadBoard(true);
    } catch (err) {
      setDataError(err.message);
      setNotification(`⚠️ Không khởi động được Agent: ${err.message}`);
      await reloadBoard(true);
    } finally { setLaunching(false); }
  }

  async function addEvidence() {
    if (!file || !evidenceType) {
      setNotification("Hãy chọn PDF/DOCX và loại bằng chứng hợp lệ.");
      return;
    }
    if (!/\.(pdf|docx)$/i.test(file.name)) {
      setNotification("Backend chỉ chấp nhận tệp PDF hoặc DOCX.");
      return;
    }
    if (file.size > 15 * 1024 * 1024) {
      setNotification("Tệp phải không vượt quá 15MB.");
      return;
    }
    setUploading(true);
    try {
      const body = new FormData();
      body.append("evidence_type", evidenceType);
      body.append("file", file);
      const result = await request(`/api/assessments/${assessmentId}/controls/${encodeURIComponent(selectedId)}/evidence`, {
        method: "POST", body,
      });
      setUploadedFiles(prev => [{ name: file.name, type: evidenceType, control: selectedId, id: result.evidence_id }, ...prev]);
      setFile(null);
      setNotification(`✅ Đã lưu evidence ${result.evidence_id} trên PostgreSQL.`);
      await reloadBoard(true);
    } catch (err) { setNotification(`⚠️ Upload thất bại: ${err.message}`); }
    finally { setUploading(false); }
  }

  async function createMember(event) {
    event.preventDefault();
    setMemberBusy(true);
    try {
      await request("/api/team/users", { method: "POST", body: JSON.stringify(member) });
      setShowMemberForm(false);
      setMember({ username: "", display_name: "", password: "" });
      setNotification("✅ Đã tạo thành viên và thêm vào đợt đánh giá chung.");
    } catch (err) { setNotification(`⚠️ ${err.message}`); }
    finally { setMemberBusy(false); }
  }

  const metrics = [
    { name: "Nhiệt độ Sao Hỏa", value: `${marsTemp}°C`, hint: "Thời tiết giả lập", Icon: Thermometer, color: "#F5B078" },
    { name: "Phạm vi kiểm toán", value: `${board.length || 56} Controls`, hint: "A.6 • A.7 • A.8", Icon: Target, color: "#EDC57F" },
    { name: "Agents đang chạy", value: totalRunning, hint: "Job thực trong PostgreSQL", Icon: Bot, color: "#B8D6F3" },
    { name: "Hoàn tất quy trình", value: totalCompleted,
      hint: `${board.length ? Math.round(totalCompleted / board.length * 100) : 0}% đã đánh giá · không đồng nghĩa tuân thủ`,
      Icon: CheckCircle2, color: "#A3D2AA" },
  ];

  const tabs = [
    { name: "Tổng quan", Icon: LayoutDashboard },
    { name: "Bản đồ Sao Hỏa", Icon: MapIcon },
    { name: "Báo cáo tiến độ", Icon: BarChart3 },
  ];

  return (
    <div
      className="relative min-h-screen overflow-hidden bg-[#172337] text-[#FFF7EB]"
      style={{
        fontFamily:
          'ui-rounded, "Trebuchet MS", Inter, system-ui, sans-serif',
      }}
    >
      <style>{`
        @keyframes cuteBob {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-7px); }
        }
        .cute-bob {
          animation: cuteBob 3s ease-in-out infinite;
        }
        .cute-scroll::-webkit-scrollbar {
          width: 6px;
          height: 6px;
        }
        .cute-scroll::-webkit-scrollbar-thumb {
          background: #53616f;
          border-radius: 20px;
        }
        button { touch-action: manipulation; }
      `}</style>

      {/* Soft space background */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_50%_70%,#4F4350_0%,#293247_43%,#172337_85%)]" />
      <TinyStars />

      <div className="relative z-10 mx-auto max-w-[1900px] p-3 sm:p-5">

        {/* HEADER */}
        <header className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-13 w-13 items-center justify-center rounded-[20px] border border-white/20 bg-[#FF914D] shadow-md">
              <Sparkles className="h-7 w-7 text-white" />
            </div>

            <div>
              <h1 className="text-xl font-black tracking-wide">
                ISO ENTERPRISE LAB
              </h1>
              <p className="text-xs font-semibold text-[#B8BFCA]">
                MARS TYCOON • SECURITY COMMAND • ISO 27001
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-[#334457] px-3 py-2 text-xs text-[#FFE0B7]">👤 {user.display_name} · {user.role}</span>
            {user.role === "admin" && <button onClick={() => setShowMemberForm(true)} className="rounded-full bg-[#374e60] px-4 py-2 text-xs font-bold hover:bg-[#456175]">+ Thành viên</button>}
            <button onClick={onLogout} className="rounded-full bg-[#FF914D] px-4 py-2 text-xs font-bold text-white hover:bg-[#F77D32]">Đăng xuất</button>
          </div>
          <div className="flex items-center gap-2 rounded-full bg-[#334457] px-4 py-2.5 text-xs font-bold text-[#B7E6C0]">
            <span className="h-2.5 w-2.5 rounded-full bg-[#85D5A1]" />
            CĂN CỨ ĐANG HOẠT ĐỘNG
          </div>
        </header>

        {dataError && <div role="alert" className="mb-3 rounded-2xl bg-red-500/15 p-3 text-sm text-red-100">⚠️ {dataError} <button className="ml-2 underline" onClick={() => reloadBoard()}>Thử lại</button></div>}
        {dataLoading && <div className="mb-3 text-sm text-[#FFCB9C]">Đang tải 56 controls và tiến độ từ PostgreSQL...</div>}
        {/* TOP HUD */}
        <div className="cute-scroll mb-4 flex gap-3 overflow-x-auto pb-1">
          {metrics.map((metric) => (
            <Panel
              key={metric.name}
              className="min-w-[185px] flex-1 px-4 py-3"
            >
              <div className="flex items-center gap-3">
                <div
                  className="rounded-[17px] bg-white/10 p-2.5"
                  style={{ color: metric.color }}
                >
                  <metric.Icon className="h-6 w-6" />
                </div>

                <div>
                  <div className="text-[11px] font-semibold text-[#AEBACA]">
                    {metric.name}
                  </div>
                  <div className="mt-0.5 text-xl font-black">
                    {metric.value}
                  </div>
                  <div className="text-[10px] text-[#8997A9]">
                    {metric.hint}
                  </div>
                </div>
              </div>
            </Panel>
          ))}
        </div>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[260px_minmax(0,1fr)_350px]">

          {/* LEFT PANEL */}
          <Panel className="cute-scroll flex max-h-[760px] flex-col overflow-y-auto p-4 xl:h-[760px]">

            <div className="mb-6 flex items-center gap-3">
              <div className="rounded-[17px] bg-[#FF914D]/20 p-3">
                <Radar className="h-5 w-5 text-[#FFB780]" />
              </div>
              <div>
                <h2 className="text-sm font-black">
                  TRUNG TÂM NHIỆM VỤ
                </h2>
                <p className="text-xs text-[#AEBACA]">
                  ISO Enterprise Lab
                </p>
              </div>
            </div>

            <div className="mb-3 text-[11px] font-black tracking-widest text-[#AEBACA]">
              CHỌN KHU VỰC
            </div>

            <div className="space-y-3">
              {ZONES.map((item) => {
                const active = selectedGroup === item.id;
                const done = countCompleted(item.id);
                const total = CONTROLS[item.id].length;

                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => selectZone(item)}
                    className={`w-full rounded-[20px] border p-3 text-left transition-all ${
                      active
                        ? "border-[#F4A46D]/70 bg-[#F4A46D]/15"
                        : "border-white/10 bg-[#2A3A4E] hover:bg-[#35465A]"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className="rounded-[13px] p-2"
                        style={{
                          background: item.main + "28",
                          color: item.light,
                        }}
                      >
                        <item.Icon className="h-5 w-5" />
                      </div>

                      <div className="min-w-0 flex-1">
                        <div className="text-sm font-black">
                          {item.id} — {item.title}
                        </div>
                        <div className="mt-1 text-xs text-[#B9C2CE]">
                          {done}/{total} hoàn tất quy trình
                        </div>
                      </div>

                      <ChevronRight className="h-4 w-4 text-[#AEBACA]" />
                    </div>

                    <div className="mt-3 h-2 overflow-hidden rounded-full bg-[#152234]">
                      <div
                        className="h-full rounded-full bg-[#FF984F]"
                        style={{ width: `${done / total * 100}%` }}
                      />
                    </div>
                  </button>
                );
              })}
            </div>

            <div className="my-5 h-px bg-white/10" />

            <div className="mb-3 flex items-center justify-between text-xs font-black text-[#B9C2CE]">
              <span>DANH SÁCH CONTROL</span>
              <span className="rounded-full bg-[#F49C63]/20 px-2 py-1 text-[#FFC38C]">
                {selectedGroup}
              </span>
            </div>

            <div className="cute-scroll min-h-[130px] flex-1 space-y-1 overflow-y-auto pr-1">
              {ALL_CONTROLS.filter(
                (item) => item.group === selectedGroup
              ).map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => selectControl(item)}
                  className={`flex w-full items-center gap-2 rounded-[12px] px-3 py-2.5 text-left text-xs transition-colors ${
                    selectedId === item.id
                      ? "bg-[#F49C63]/20 text-[#FFCB9C]"
                      : "text-[#C6CED8] hover:bg-white/10"
                  }`}
                >
                  {boardById.get(item.id)?.workflow_status === "COMPLETED" ? (
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-[#A4D8AA]" />
                  ) : (
                    <span className="h-3 w-3 shrink-0 rounded-full border-2 border-[#8392A6]" />
                  )}

                  <span className="w-12 shrink-0 font-black">{item.id}</span>
                  <span className="truncate">{item.title}</span>
                </button>
              ))}
            </div>

            {/* Cute mascot */}
            <div className="mt-4 flex items-center gap-3 rounded-[22px] bg-[#30455A] p-3">
              <div className="cute-bob flex h-15 w-15 shrink-0 items-center justify-center rounded-[22px] bg-[#F7B879]">
                <Bot className="h-10 w-10 text-[#624C5D]" />
              </div>
              <div>
                <div className="font-black text-[#FFE0A9]">
                  ISO-BOT 🧡
                </div>
                <div className="mt-1 text-[11px] leading-relaxed text-[#C5D1DD]">
                  Mình sẵn sàng khám phá căn cứ cùng bạn!
                </div>
              </div>
            </div>
          </Panel>

          {/* CENTER SPACE BASE */}
          <div className="cute-scroll relative h-[760px] overflow-x-auto overflow-y-hidden rounded-[36px] border-4 border-[#B58164]/30 bg-[#EAA167] shadow-2xl shadow-black/20">
            <div className="relative h-full min-w-[850px] overflow-hidden">

              {/* Warm planet background */}
              <div className="absolute inset-0 bg-[linear-gradient(180deg,#686C82_0%,#E3A270_38%,#F6BA7B_75%,#EFA464_100%)]" />

              <TinyStars />

              {/* Martian planet surface */}
              <div className="absolute -bottom-[470px] left-1/2 h-[1100px] w-[1450px] -translate-x-1/2 rounded-[50%] border-[12px] border-[#F9C997]/40 bg-[radial-gradient(ellipse_at_46%_20%,#FFD8A0_0%,#F7BD80_37%,#E89E63_67%,#C87F53_100%)] shadow-[inset_0_25px_100px_rgba(255,255,255,.18)]" />

              {/* Sandy isometric tiles */}
              <div
                className="pointer-events-none absolute -left-[25%] top-[13%] h-[1100px] w-[150%] opacity-[.12]"
                style={{
                  backgroundImage:
                    "linear-gradient(#A86442 1px,transparent 1px),linear-gradient(90deg,#A86442 1px,transparent 1px)",
                  backgroundSize: "58px 58px",
                  transform:
                    "perspective(750px) rotateX(55deg) rotateZ(-23deg)",
                }}
              />

              {/* Craters */}
              {[
                { x: "9%", y: "52%", w: 100 },
                { x: "80%", y: "70%", w: 120 },
                { x: "67%", y: "22%", w: 65 },
                { x: "27%", y: "83%", w: 75 },
              ].map((c, i) => (
                <div
                  key={i}
                  className="pointer-events-none absolute rounded-full border-[10px] border-[#C98057]/30 bg-[#DEA075]/30 shadow-[inset_5px_7px_14px_rgba(148,82,42,.18)]"
                  style={{
                    left: c.x,
                    top: c.y,
                    width: c.w,
                    height: c.w * .48,
                    transform: "rotate(-20deg)",
                  }}
                />
              ))}

              {/* Soft pathway between buildings */}
              <svg
                viewBox="0 0 850 760"
                preserveAspectRatio="none"
                className="pointer-events-none absolute inset-0 h-full w-full"
              >
                <path
                  d="M210 455 L560 355 L670 470 L455 625 L210 455"
                  fill="none"
                  stroke="#FDF0CF"
                  strokeWidth="8"
                  strokeDasharray="16 17"
                  strokeLinecap="round"
                  opacity=".65"
                />
              </svg>

              {/* Map heading */}
              <div className="absolute left-6 top-6 z-20 rounded-full bg-[#FFF9EC]/90 px-5 py-3 text-[#815236] shadow-md">
                <div className="flex items-center gap-2 text-sm font-black">
                  <MapIcon className="h-5 w-5" />
                  MARS BASE • SECTOR 27001
                </div>
              </div>

              {/* Planet */}
              <div className="absolute right-9 top-12 h-24 w-24 rounded-full bg-gradient-to-br from-[#B5E1DA] via-[#78BAD1] to-[#6897C2] shadow-xl">
                <div className="absolute left-3 top-5 h-5 w-12 -rotate-20 rounded-full bg-white/30" />
                <div className="absolute bottom-5 right-3 h-4 w-9 rounded-full bg-[#8ED8AD]/65" />
              </div>

              {/* Rooms */}
              {ZONES.map((item) => (
                <DioramaRoom
                  key={item.id}
                  zone={item}
                  active={selectedGroup === item.id}
                  running={runningOnMap?.startsWith(item.id)}
                  onClick={() => selectZone(item)}
                />
              ))}
              <BaseLife runningZone={runningOnMap ? runningOnMap.split(".").slice(0, 2).join(".") : null} />
              {/* Current mission */}
              {activeTab === "Tổng quan" && (
                <div className="absolute bottom-28 left-6 z-30 max-w-[290px] rounded-[22px] border border-white/70 bg-[#FFF9EB]/95 p-4 text-[#76513C] shadow-xl">
                  <div className="flex items-center gap-2 text-xs font-black text-[#D07843]">
                    <Sparkles className="h-4 w-4" />
                    NHIỆM VỤ HIỆN TẠI
                  </div>
                  <div className="mt-2 text-sm font-black">
                    {control.id} — {control.title}
                  </div>
                  <div className="mt-1 text-xs font-semibold text-[#9C806E]">
                    {zone.name}
                  </div>
                </div>
              )}

              {activeTab === "Bản đồ Sao Hỏa" && (
                <div className="absolute bottom-28 left-6 z-30 rounded-full bg-[#FFF9EC]/95 px-5 py-3 text-xs font-black text-[#986144] shadow-md">
                  🪐 3 KHU VỰC ĐANG HOẠT ĐỘNG
                </div>
              )}

              {activeTab === "Báo cáo tiến độ" && (
                <div className="absolute left-1/2 top-[15%] z-40 w-[360px] -translate-x-1/2 rounded-[30px] border border-white/60 bg-[#FFF9EC]/95 p-5 text-[#76513C] shadow-xl">
                  <h3 className="flex items-center gap-2 text-base font-black">
                    <BarChart3 className="h-5 w-5 text-[#F38C4B]" />
                    Tiến độ căn cứ
                  </h3>
                  <p className="my-3 text-xs text-[#997C68]">
                    {totalCompleted}/{board.length || 56} controls đã xử lý xong
                  </p>

                  {ZONES.map((item) => {
                    const done = countCompleted(item.id);
                    const total = CONTROLS[item.id].length;

                    return (
                      <div key={item.id} className="mb-4">
                        <div className="mb-2 flex justify-between text-xs font-bold">
                          <span>{item.id} — {item.title}</span>
                          <span>{done}/{total}</span>
                        </div>
                        <div className="h-3 rounded-full bg-[#EEDAC6]">
                          <div
                            className="h-full rounded-full bg-[#F69C5B]"
                            style={{ width: `${done / total * 100}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                  <p className="text-[11px] text-[#A08C7D]">
                    Số liệu từ PostgreSQL; hoàn tất quy trình không đồng nghĩa đạt ISO.
                  </p>
                </div>
              )}

              {/* Bottom pill toolbar */}
              <div className="absolute bottom-5 left-1/2 z-40 flex max-w-[97%] -translate-x-1/2 gap-1 rounded-full border-2 border-[#E8B98F] bg-[#FFF9EE] p-1.5 shadow-lg">
                {tabs.map((tab) => (
                  <button
                    key={tab.name}
                    type="button"
                    onClick={() => setActiveTab(tab.name)}
                    className={`flex items-center gap-2 rounded-full px-4 py-3 text-xs font-black transition-all ${
                      activeTab === tab.name
                        ? "bg-[#FF984F] text-white"
                        : "text-[#8B6A55] hover:bg-[#FCE4CE]"
                    }`}
                  >
                    <tab.Icon className="h-4 w-4" />
                    <span>{tab.name}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* RIGHT PANEL */}
          <Panel className="cute-scroll max-h-[760px] overflow-y-auto p-5 xl:h-[760px]">

            <div className="mb-5 flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 text-sm font-black text-[#FFC18D]">
                <Activity className="h-5 w-5" />
                COMMAND CENTER
              </div>
              <span className="rounded-full bg-[#3F6657] px-3 py-1.5 text-[11px] font-black text-[#C2E6C7]">
                ● ONLINE
              </span>
            </div>

            {/* Control detail */}
            <div className="rounded-[25px] border border-white/10 bg-[#2C3C50] p-5">
              <div className="text-xs font-black tracking-wider text-[#FFBE85]">
                CHI TIẾT CONTROL
              </div>

              <h2 className="mt-3 text-3xl font-black">
                {control.id}
              </h2>

              <h3 className="mt-1 text-lg font-black text-[#FFE0C0]">
                {control.title}
              </h3>

              <p className="mt-3 text-sm font-medium leading-relaxed text-[#C8D2DF]">
                {currentProgress?.objective || DESCRIPTIONS[control.id] ||
                  `Đánh giá biện pháp kiểm soát ${control.id} dựa trên bằng chứng của doanh nghiệp.`}
              </p>

              <div className="my-5 h-px bg-white/10" />

              <div className="flex items-center justify-between gap-2">
                <span className="text-xs text-[#B9C6D2]">
                  Trạng thái
                </span>

                <span
                  className={`rounded-full px-3 py-2 text-[11px] font-black ${
                    currentProgress?.workflow_status === "RUNNING"
                      ? "bg-[#E8B97D]/20 text-[#FFD7A1]"
                      : currentProgress?.workflow_status === "COMPLETED"
                        ? "bg-[#83BD90]/20 text-[#BCE5B9]"
                        : "bg-[#F5BA72]/15 text-[#FFE0A0]"
                  }`}
                >
                  {statusLabels[currentProgress?.workflow_status] || "Chưa có kết luận"}
                </span>
              </div>
              <div className="mt-3 text-xs text-[#E6C2A5]">Kết luận ISO: {currentProgress?.compliance_status || "Chưa có kết luận"}</div>
              <div className="mt-2 text-xs text-[#B9C6D2]">Phụ trách: {currentProgress?.assigned_to || "Chưa phân công"}</div>
            </div>

            {/* Orange launch button */}
            <button
              type="button"
              disabled={launching || dataLoading || !currentProgress || currentProgress.workflow_status === "RUNNING"}
              onClick={launchAgent}
              className={
                "mt-5 flex w-full items-center justify-center gap-3 " +
                "rounded-full bg-[#FF842F] px-5 py-5 text-sm font-black text-white " +
                "shadow-[0_5px_0_#D66222] transition-all " +
                "hover:bg-[#F77926] hover:-translate-y-0.5 " +
                "active:translate-y-1 active:shadow-none " +
                "disabled:cursor-wait disabled:opacity-70"
              }
            >
              {launching || currentProgress?.workflow_status === "RUNNING" ? (
                <>
                  <Loader2 className="h-6 w-6 animate-spin" />
                  <span>Agent đang chạy trên backend...</span>
                </>
              ) : (
                <>
                  <Rocket className="h-6 w-6" />
                  <span>🚀 PHÁI AI AGENT ĐI KIỂM TOÁN</span>
                </>
              )}
            </button>
              <AgentCrewPanel
                running={currentProgress?.workflow_status === "RUNNING"}
                stage={missionStep}
                completed={false}
                live={true}
                realStatus={statusLabels[currentProgress?.workflow_status] || "Chưa bắt đầu"}
                controlId={selectedId}
              />
            <p className="mt-3 text-center text-[11px] font-semibold text-[#AAB6C5]">
              🤖 AI Agent chạy trên FastAPI · chuyển động robot chỉ minh họa
            </p>

            {/* Evidence */}
            <div className="mt-7">
              <div className="mb-3 flex items-center gap-2 text-sm font-black">
                <FileCheck2 className="h-5 w-5 text-[#FFC18D]" />
                EVIDENCE REPOSITORY
              </div>

              <div className="rounded-[26px] border-2 border-dashed border-[#A0ADBA]/30 bg-[#2B3B4F] p-4">
                <label className="mb-2 block text-xs font-bold text-[#C4CDD8]">
                  Loại bằng chứng
                </label>

                <select
                  value={evidenceType}
                  onChange={(e) => setEvidenceType(e.target.value)}
                  className="mb-4 w-full rounded-[15px] border border-white/10 bg-[#1B2A3B] px-3 py-3 text-xs font-semibold text-white outline-none focus:border-[#FFAB70]"
                >
                  {(currentProgress?.expected_evidence_types || []).map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>

                <label className="flex cursor-pointer flex-col items-center rounded-[22px] bg-[#3A4A5D] p-5 text-center transition hover:bg-[#435367]">
                  <UploadCloud className="mb-3 h-9 w-9 text-[#FFBF8E]" />

                  <span className="max-w-full truncate text-sm font-black">
                    {file ? file.name : "Chọn tài liệu"}
                  </span>

                  <span className="mt-1 text-xs text-[#B8C4D1]">
                    PDF hoặc DOCX · Tối đa 15MB
                  </span>

                  <input
                    type="file"
                    className="hidden"
                    accept=".pdf,.docx"
                    onChange={(e) =>
                      setFile(e.target.files?.[0] || null)
                    }
                  />
                </label>

                <button
                  type="button"
                  onClick={addEvidence}
                  disabled={uploading || currentProgress?.workflow_status === "RUNNING"}
                  className="mt-4 flex w-full items-center justify-center gap-2 rounded-full bg-[#F7B477] px-4 py-3 text-xs font-black text-[#624631] transition hover:bg-[#FFC591]"
                >
                  <FileUp className="h-4 w-4" />
                  {uploading ? "Đang lưu bằng chứng..." : "TẢI LÊN TÀI LIỆU"}
                </button>

                {uploadedFiles.length > 0 && (
                  <div className="mt-4 space-y-2">
                    {uploadedFiles.slice(0, 3).map((item, i) => (
                      <div
                        key={`${item.name}-${i}`}
                        className="rounded-[14px] bg-[#1D2C3C] p-3 text-xs"
                      >
                        <div className="truncate font-black">
                          {item.name}
                        </div>
                        <div className="mt-1 text-[#B8C4D1]">
                          {item.type} • {item.control} • ID {item.id}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Mission status */}
            <div className="mt-5 rounded-[22px] bg-[#324657] p-4">
              <div className="mb-2 flex items-center gap-2 font-black text-[#FFD2A7]">
                <CheckCircle2 className="h-5 w-5" />
                TIẾN ĐỘ NHIỆM VỤ
              </div>
              <div className="text-2xl font-black">
                {totalCompleted} / {board.length || 56}
              </div>
              <div className="mt-1 text-xs text-[#BFC9D5]">
                Hoàn tất quy trình đánh giá · chưa có nghĩa đạt ISO
              </div>
            </div>

            {/* Activity log */}
            <div className="mt-6">
              <div className="mb-3 flex items-center gap-2 font-black">
                <Clock3 className="h-4 w-4 text-[#FFC18D]" />
                NHẬT KÝ HOẠT ĐỘNG
              </div>

              {history.length === 0 ? (
                <div className="rounded-[18px] bg-[#2B3B4F] p-4 text-xs text-[#B8C4D1]">
                  Chưa có kết quả đánh giá trong PostgreSQL cho control này.
                </div>
              ) : (
                <div className="space-y-2">
                  {history.map((item, i) => (
                    <div
                      key={`${item.control}-${i}`}
                      className="rounded-[16px] bg-[#2B3B4F] p-3 text-xs"
                    >
                      <div className="font-black text-[#BCDFBD]">
                        ✓ {item.control} — {item.text}
                      </div>
                      <div className="mt-1 text-[#AEBAC9]">
                        {item.time}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

          </Panel>
        </div>

        <footer className="mt-4 flex flex-wrap justify-between gap-2 px-3 text-[11px] text-[#A6B0BD]">
          <span>🪐 ISO ENTERPRISE LAB — MARS TYCOON EDITION</span>
          <span>FastAPI + PostgreSQL · ISO workflow thực · Trái đất/Sao Hỏa minh họa</span>
        </footer>
      </div>

      {showMemberForm && <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 p-4">
        <form onSubmit={createMember} className="w-full max-w-md rounded-[28px] bg-[#26394e] p-6 text-white shadow-2xl">
          <div className="mb-4 text-lg font-black text-[#FFD3A9]">Tạo thành viên mới</div>
          <label className="block text-sm">Tên đăng nhập<input className="mb-3 mt-1 w-full rounded-xl bg-[#142335] p-3" required minLength={3} maxLength={40} value={member.username} onChange={e=>setMember({...member,username:e.target.value})}/></label>
          <label className="block text-sm">Tên hiển thị<input className="mb-3 mt-1 w-full rounded-xl bg-[#142335] p-3" required maxLength={100} value={member.display_name} onChange={e=>setMember({...member,display_name:e.target.value})}/></label>
          <label className="block text-sm">Mật khẩu (ít nhất 12 ký tự)<input className="mb-4 mt-1 w-full rounded-xl bg-[#142335] p-3" type="password" required minLength={12} value={member.password} onChange={e=>setMember({...member,password:e.target.value})}/></label>
          <div className="flex gap-3"><button type="button" className="flex-1 rounded-full bg-[#41566b] p-3" onClick={()=>setShowMemberForm(false)}>Hủy</button><button disabled={memberBusy} className="flex-1 rounded-full bg-[#FF914D] p-3 font-black">{memberBusy ? "Đang tạo..." : "Tạo thành viên"}</button></div>
        </form>
      </div>}
      {/* Notification */}
      {notification && (
        <div
          role="status"
          aria-live="polite"
          className="fixed bottom-5 right-5 z-50 flex max-w-sm items-start gap-3 rounded-[24px] border-2 border-[#F4C49A] bg-[#FFF9EC] px-5 py-4 text-sm font-bold text-[#8A5A3D] shadow-xl"
        >
          <Bot className="h-6 w-6 shrink-0 text-[#ED8B50]" />
          <span>{notification}</span>
          <button
            type="button"
            onClick={() => setNotification("")}
            aria-label="Đóng thông báo"
            className="ml-auto rounded-full p-1 hover:bg-[#F7E6D5]"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
}
