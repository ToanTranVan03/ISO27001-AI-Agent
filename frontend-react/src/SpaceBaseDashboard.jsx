
"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  Activity,
  BarChart3,
  Bot,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Database,
  FileCheck2,
  FileUp,
  LayoutDashboard,
  Loader2,
  Orbit,
  Radar,
  Rocket,
  Satellite,
  Server,
  Shield,
  ShieldCheck,
  Sparkles,
  Target,
  Thermometer,
  UploadCloud,
  Users,
  Zap,
} from "lucide-react";

// ======================================================
// ISO CONTROL CATALOG - 8 + 14 + 34 = 56
// ======================================================

const CONTROL_CATALOG = {
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

const GROUPS = [
  {
    id: "A.6",
    label: "Con người",
    building: "Tòa nhà Nhân sự",
    Icon: Users,
    defaultControl: "A.6.1",
    color: "#52e5eb",
  },
  {
    id: "A.7",
    label: "Môi trường vật lý",
    building: "Khu vực An ninh",
    Icon: Shield,
    defaultControl: "A.7.1",
    color: "#ffbd78",
  },
  {
    id: "A.8",
    label: "Công nghệ",
    building: "Trung tâm Dữ liệu",
    Icon: Server,
    defaultControl: "A.8.5",
    color: "#a293ff",
  },
];

const DESCRIPTIONS = {
  "A.6.1":
    "Thẩm tra lý lịch và năng lực của nhân sự trước khi tuyển dụng để đảm bảo sự tin cậy.",
  "A.7.1":
    "Xác định và sử dụng các vành đai bảo vệ nhằm bảo vệ các khu vực chứa thông tin và tài sản liên quan.",
  "A.8.5":
    "Triển khai công nghệ và quy trình xác thực an toàn phù hợp với yêu cầu kiểm soát truy cập.",
  "A.8.13":
    "Duy trì bản sao lưu thông tin, phần mềm và hệ thống; kiểm tra hoạt động sao lưu theo yêu cầu.",
  "A.8.20":
    "Bảo vệ, quản lý và kiểm soát mạng cùng các thiết bị mạng nhằm bảo vệ thông tin trong hệ thống.",
};

const EVIDENCE_TYPES = [
  "EVID_PPL_HR_RECORD",
  "EVID_PPL_TRAINING",
  "EVID_PHY_ACCESS_LOG",
  "EVID_PHY_ASSET",
  "EVID_TECH_IAM",
  "EVID_TECH_BACKUP",
  "EVID_TECH_CONFIG",
];

const ALL_CONTROLS = Object.entries(CONTROL_CATALOG).flatMap(
  ([group, titles]) =>
    titles.map((title, index) => ({
      id: `${group}.${index + 1}`,
      title,
      group,
    }))
);

// ======================================================
// DECORATIVE COMPONENTS
// ======================================================

function GlassPanel({ children, className = "" }) {
  return (
    <div
      className={
        "rounded-[24px] border border-sky-300/20 " +
        "bg-slate-950/65 backdrop-blur-xl " +
        "shadow-[0_22px_75px_rgba(0,0,0,0.38)] " +
        className
      }
    >
      {children}
    </div>
  );
}

function StarField() {
  const stars = Array.from({ length: 95 }, (_, index) => ({
    left: `${(index * 71.7) % 100}%`,
    top: `${(index * 37.3) % 100}%`,
    size: index % 8 === 0 ? 3 : 1.5,
    opacity: 0.18 + ((index * 17) % 60) / 100,
  }));

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {stars.map((star, index) => (
        <span
          key={index}
          className="absolute rounded-full bg-white"
          style={{
            left: star.left,
            top: star.top,
            width: star.size,
            height: star.size,
            opacity: star.opacity,
          }}
        />
      ))}
    </div>
  );
}

function IsometricBuilding({ id, color, active, label, tooltip, onClick, position }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={`Chọn ${label}`}
      className="absolute z-10 w-[225px] text-left transition-all duration-300 hover:z-20 hover:scale-105 focus:outline-none"
      style={{
        left: position.left,
        top: position.top,
        transform: active ? "translateY(-10px)" : "translateY(0)",
      }}
    >
      <div className="absolute bottom-[89%] left-1/2 z-30 w-max max-w-[220px] -translate-x-1/2">
        <div className="relative rounded-2xl border border-white/80 bg-white px-3 py-2.5 text-slate-900 shadow-[0_10px_35px_rgba(0,0,0,0.35)]">
          <div className="flex items-start gap-2">
            <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-emerald-500" />
            <div>
              <div className="text-[11px] font-black">{label}</div>
              <div className="mt-0.5 text-[10px] font-medium text-slate-500">
                {tooltip}
              </div>
            </div>
          </div>
          <div className="absolute -bottom-2 left-1/2 h-4 w-4 -translate-x-1/2 rotate-45 bg-white" />
        </div>
      </div>

      <svg
        viewBox="0 0 250 235"
        className="relative z-10 w-full drop-shadow-[0_20px_18px_rgba(0,0,0,0.5)]"
      >
        <defs>
          <linearGradient id={`roof-${id}`} x1="0" x2="1" y1="0" y2="1">
            <stop offset="0%" stopColor={color} />
            <stop offset="100%" stopColor="#152846" />
          </linearGradient>
          <linearGradient id={`wall-${id}`} x1="0" x2="0.7" y1="0" y2="1">
            <stop offset="0%" stopColor="#536d91" />
            <stop offset="100%" stopColor="#16263e" />
          </linearGradient>
          <filter id={`glow-${id}`}>
            <feGaussianBlur stdDeviation="7" />
          </filter>
        </defs>

        {active && (
          <ellipse
            cx="128"
            cy="189"
            rx="110"
            ry="36"
            fill={color}
            opacity="0.33"
            filter={`url(#glow-${id})`}
          />
        )}

        {/* Isometric ground platform */}
        <polygon
          points="17,162 119,104 238,166 133,225"
          fill="#101d32"
          stroke={color}
          strokeWidth={active ? 3 : 1.5}
          strokeOpacity=".8"
        />
        <polygon
          points="17,162 133,225 133,232 17,169"
          fill="#243047"
        />
        <polygon
          points="133,225 238,166 238,174 133,232"
          fill="#263b56"
        />

        {/* Main building */}
        <polygon
          points="63,106 128,70 204,108 137,148"
          fill={`url(#roof-${id})`}
          stroke="#e8fcff"
          strokeOpacity=".5"
          strokeWidth="2"
        />
        <polygon
          points="63,106 137,148 137,198 63,155"
          fill={`url(#wall-${id})`}
        />
        <polygon
          points="137,148 204,108 204,159 137,198"
          fill="#263953"
        />

        {/* Roof inset */}
        <polygon
          points="91,107 130,86 173,108 134,130"
          fill="#102137"
          stroke={color}
          strokeOpacity=".8"
        />
        <polygon
          points="106,107 130,94 158,108 134,122"
          fill={color}
          opacity=".8"
        />

        {/* Left illuminated windows */}
        {[119, 138, 157].map((y) => (
          <React.Fragment key={y}>
            <polygon
              points={`74,${y} 93,${y + 10} 93,${y + 18} 74,${y + 8}`}
              fill={color}
              opacity=".85"
            />
            <polygon
              points={`101,${y + 15} 120,${y + 25} 120,${y + 33} 101,${y + 23}`}
              fill="#b1f4ff"
              opacity=".8"
            />
          </React.Fragment>
        ))}

        {/* Right windows */}
        {[143, 163].map((y) => (
          <React.Fragment key={y}>
            <polygon
              points={`148,${y} 169,${y - 12} 169,${y - 3} 148,${y + 9}`}
              fill={color}
              opacity=".9"
            />
            <polygon
              points={`176,${y - 16} 195,${y - 27} 195,${y - 18} 176,${y - 7}`}
              fill="#b1f4ff"
              opacity=".8"
            />
          </React.Fragment>
        ))}

        {/* Antenna / scan light */}
        <path
          d="M130 86 V52"
          stroke="#bcecff"
          strokeWidth="3"
          strokeLinecap="round"
        />
        <circle cx="130" cy="49" r="7" fill={color} />
        <circle
          cx="130"
          cy="49"
          r="14"
          fill="none"
          stroke={color}
          strokeDasharray="4 6"
          opacity=".75"
        />

        {/* Small satellite units */}
        <polygon points="20,148 40,137 61,149 41,161" fill="#659bb2" />
        <polygon points="195,180 215,168 234,180 214,192" fill="#659bb2" />

        <text
          x="132"
          y="215"
          fill="#e8faff"
          fontSize="12"
          fontWeight="900"
          textAnchor="middle"
        >
          {id}
        </text>
      </svg>

      {active && (
        <div className="absolute bottom-3 left-1/2 h-1 w-28 -translate-x-1/2 rounded-full bg-cyan-300 shadow-[0_0_22px_#22d3ee]" />
      )}
    </button>
  );
}

// ======================================================
// MAIN APP
// ======================================================

export default function SpaceBaseDashboard() {
  const [selectedGroup, setSelectedGroup] = useState("A.6");
  const [selectedId, setSelectedId] = useState("A.6.1");
  const [activeTab, setActiveTab] = useState("Tổng quan");
  const [completed, setCompleted] = useState({});
  const [runningId, setRunningId] = useState(null);
  const [agentsRunning, setAgentsRunning] = useState(1);
  const [approvedCount, setApprovedCount] = useState(12);
  const [selectedEvidence, setSelectedEvidence] = useState(EVIDENCE_TYPES[0]);
  const [file, setFile] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [history, setHistory] = useState([]);
  const [toast, setToast] = useState("");
  const timerRef = useRef(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const selectedControl =
    ALL_CONTROLS.find((control) => control.id === selectedId) ||
    ALL_CONTROLS[0];

  const selectedZone =
    GROUPS.find((group) => group.id === selectedGroup) || GROUPS[0];

  const totalCompleted = Object.keys(completed).length;

  const countCompleted = (groupId) =>
    Object.keys(completed).filter((id) => id.startsWith(groupId + ".")).length;

  const selectGroup = (group) => {
    setSelectedGroup(group.id);
    setSelectedId(group.defaultControl);
    setActiveTab("Bản đồ Sao Hỏa");
  };

  const selectControl = (control) => {
    setSelectedId(control.id);
    setSelectedGroup(control.group);
  };

  const launchAgent = () => {
    if (runningId) return;

    const targetId = selectedControl.id;
    const zone = selectedZone.building;

    setRunningId(targetId);
    setAgentsRunning((previous) => previous + 1);
    setToast(`🚀 AI Agent đang bay đến ${zone}...`);

    timerRef.current = setTimeout(() => {
      setCompleted((previous) => ({
        ...previous,
        [targetId]: true,
      }));

      setAgentsRunning((previous) => Math.max(1, previous - 1));
      setApprovedCount((previous) => previous + 1);
      setRunningId(null);

      setHistory((previous) =>
        [
          {
            id: targetId,
            time: new Date().toLocaleTimeString("vi-VN"),
            text: "Đã hoàn tất tác vụ demo",
          },
          ...previous,
        ].slice(0, 8)
      );

      setToast(
        `✅ Agent đã hoàn tất mô phỏng ${targetId}. Chưa có kết luận ISO thực tế.`
      );
    }, 3000);
  };

  const attachEvidence = () => {
    if (!file) {
      setToast("Vui lòng chọn tài liệu trước.");
      return;
    }

    setUploadedFiles((previous) => [
      {
        id: selectedEvidence,
        name: file.name,
        control: selectedId,
      },
      ...previous,
    ]);

    setToast(`Đã thêm ${file.name} vào danh sách demo. Chưa upload lên server.`);
    setFile(null);
  };

  const tabItems = [
    { title: "Tổng quan", Icon: LayoutDashboard },
    { title: "Bản đồ Sao Hỏa", Icon: Orbit },
    { title: "Báo cáo tiến độ", Icon: BarChart3 },
  ];

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#070e1e] font-sans text-white">
      <style>{`
        @keyframes spaceFloat {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-9px); }
        }

        @keyframes scanPulse {
          0%, 100% { opacity: .2; transform: scale(1); }
          50% { opacity: .65; transform: scale(1.12); }
        }

        .space-float {
          animation: spaceFloat 5s ease-in-out infinite;
        }

        .scan-pulse {
          animation: scanPulse 3s ease-in-out infinite;
        }

        .space-scroll::-webkit-scrollbar {
          width: 5px;
          height: 5px;
        }

        .space-scroll::-webkit-scrollbar-thumb {
          background: rgba(125,211,252,.23);
          border-radius: 99px;
        }
      `}</style>

      {/* Cosmic background */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_50%_55%,#29375b_0%,#121b35_42%,#070e1e_78%)]" />
      <StarField />

      <div className="relative z-10 mx-auto max-w-[1900px] px-3 py-4 sm:px-5">
        {/* HEADER */}
        <header className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-cyan-300/30 bg-cyan-400/10 shadow-[0_0_30px_rgba(34,211,238,.16)]">
              <Satellite className="h-7 w-7 text-cyan-300" />
            </div>

            <div>
              <h1 className="text-lg font-black tracking-wide sm:text-xl">
                ISO ENTERPRISE LAB
              </h1>
              <p className="text-xs text-cyan-200/60">
                MARS SECURITY COMMAND • ISO/IEC 27001:2022
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-2 text-[11px] font-bold text-emerald-300">
            <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
            MÔ PHỎNG ĐANG HOẠT ĐỘNG
          </div>
        </header>

        {/* TOP HUD */}
        <div className="space-scroll mb-4 flex gap-3 overflow-x-auto pb-1">
          {[
            {
              label: "Nhiệt độ hệ thống",
              value: "-45°C",
              sub: "Môi trường mô phỏng",
              Icon: Thermometer,
              color: "text-sky-300",
            },
            {
              label: "Phạm vi ISO",
              value: "56 Controls",
              sub: "A.6 · A.7 · A.8",
              Icon: Target,
              color: "text-amber-300",
            },
            {
              label: "Agents đang chạy",
              value: agentsRunning,
              sub: "Thông số demo",
              Icon: Bot,
              color: "text-cyan-300",
            },
            {
              label: "Đã phê duyệt",
              value: approvedCount,
              sub: "Thông số demo",
              Icon: CheckCircle2,
              color: "text-emerald-300",
            },
          ].map((metric) => (
            <GlassPanel
              key={metric.label}
              className="min-w-[190px] flex-1 px-4 py-3"
            >
              <div className="flex items-start gap-3">
                <metric.Icon
                  className={`mt-1 h-6 w-6 shrink-0 ${metric.color}`}
                />
                <div>
                  <div className="text-[11px] text-slate-400">
                    {metric.label}
                  </div>
                  <div className="mt-1 text-xl font-black tracking-tight">
                    {metric.value}
                  </div>
                  <div className="text-[10px] text-slate-500">
                    {metric.sub}
                  </div>
                </div>
              </div>
            </GlassPanel>
          ))}
        </div>

        {/* MAIN 3-COLUMN COMMAND CENTER */}
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[250px_minmax(0,1fr)_345px]">
          {/* LEFT MISSIONS */}
          <GlassPanel className="flex max-h-[760px] min-h-[400px] flex-col p-4 xl:h-[760px]">
            <div className="mb-5 flex items-center gap-2">
              <div className="rounded-xl bg-sky-400/10 p-2">
                <Radar className="h-5 w-5 text-cyan-300" />
              </div>
              <div>
                <div className="text-sm font-black">TRUNG TÂM NHIỆM VỤ</div>
                <div className="text-[11px] text-slate-500">
                  ISO Enterprise Lab
                </div>
              </div>
            </div>

            <p className="mb-3 text-[10px] font-extrabold uppercase tracking-[.18em] text-slate-500">
              Chọn khu vực
            </p>

            <div className="space-y-2">
              {GROUPS.map((group) => {
                const progress = countCompleted(group.id);
                const isActive = selectedGroup === group.id;

                return (
                  <button
                    key={group.id}
                    onClick={() => selectGroup(group)}
                    className={`w-full rounded-xl border p-3 text-left transition-all ${
                      isActive
                        ? "border-cyan-400/50 bg-cyan-400/10 shadow-[inset_0_0_18px_rgba(34,211,238,.05)]"
                        : "border-white/5 bg-white/[.035] hover:border-sky-400/25 hover:bg-white/[.07]"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <group.Icon
                        className="h-5 w-5"
                        style={{ color: group.color }}
                      />
                      <div className="min-w-0 flex-1">
                        <div className="text-sm font-bold">
                          {group.id} — {group.label}
                        </div>
                        <div className="mt-1 text-[11px] text-slate-400">
                          {progress}/{CONTROL_CATALOG[group.id].length} hoàn tất
                        </div>
                      </div>
                      <ChevronRight className="h-4 w-4 text-slate-500" />
                    </div>
                    <div className="mt-3 h-1 overflow-hidden rounded-full bg-slate-700">
                      <div
                        className="h-full rounded-full bg-cyan-400 transition-all"
                        style={{
                          width: `${
                            (progress / CONTROL_CATALOG[group.id].length) * 100
                          }%`,
                        }}
                      />
                    </div>
                  </button>
                );
              })}
            </div>

            <div className="mt-5 min-h-0 flex-1">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-[10px] font-bold tracking-widest text-slate-500">
                  DANH SÁCH CONTROL
                </span>
                <span className="text-[10px] text-cyan-300">
                  {selectedGroup}
                </span>
              </div>

              <div className="space-scroll h-full max-h-[180px] space-y-1 overflow-y-auto pr-1 xl:max-h-none">
                {ALL_CONTROLS.filter(
                  (control) => control.group === selectedGroup
                ).map((control) => (
                  <button
                    key={control.id}
                    onClick={() => selectControl(control)}
                    className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-xs transition-colors ${
                      selectedId === control.id
                        ? "bg-sky-500/20 text-sky-100"
                        : "text-slate-400 hover:bg-white/5 hover:text-white"
                    }`}
                  >
                    {completed[control.id] ? (
                      <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-400" />
                    ) : (
                      <span className="h-2.5 w-2.5 shrink-0 rounded-full border border-slate-600" />
                    )}
                    <span className="w-12 shrink-0 font-bold">
                      {control.id}
                    </span>
                    <span className="truncate">{control.title}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* ROBOT MASCOT */}
            <div className="mt-5 flex items-center gap-3 rounded-2xl border border-cyan-400/20 bg-gradient-to-r from-sky-500/10 to-indigo-500/10 p-3">
              <div className="space-float relative flex h-14 w-14 shrink-0 items-center justify-center rounded-[20px] border-2 border-sky-300/50 bg-gradient-to-br from-sky-400 to-indigo-600 shadow-[0_0_22px_rgba(59,130,246,.28)]">
                <Bot className="h-9 w-9 text-white" />
                <div className="absolute -top-2 left-1/2 h-3 w-1 -translate-x-1/2 rounded-full bg-cyan-300" />
              </div>
              <div>
                <p className="text-xs font-black text-cyan-200">
                  ISO-BOT / V1
                </p>
                <p className="mt-1 text-[10px] leading-relaxed text-slate-400">
                  Sẵn sàng nhận nhiệm vụ bảo vệ căn cứ!
                </p>
              </div>
            </div>
          </GlassPanel>

          {/* CENTER 3D MARS BASE */}
          <div className="space-scroll relative h-[760px] overflow-x-auto overflow-y-hidden rounded-[28px] border border-sky-400/15 bg-[#141b30]">
            <div className="relative h-full min-w-[750px] overflow-hidden">
              <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_65%,#80533c_0%,#3d3441_36%,#19223e_70%,#0d1730_100%)]" />

              <StarField />

              {/* Planet horizon */}
              <div className="pointer-events-none absolute -bottom-[430px] left-1/2 h-[920px] w-[1240px] -translate-x-1/2 rounded-[50%] border border-orange-200/10 bg-[radial-gradient(ellipse_at_45%_25%,#b66f48_0%,#704d44_32%,#393a4f_67%,#152038_88%)] shadow-[inset_0_35px_100px_rgba(255,184,112,.12),0_-30px_100px_rgba(241,113,52,.08)]" />

              {/* Isometric ground grid */}
              <div
                className="pointer-events-none absolute left-[-18%] top-[10%] h-[1000px] w-[140%] opacity-25"
                style={{
                  backgroundImage:
                    "linear-gradient(rgba(255,220,190,.18) 1px,transparent 1px),linear-gradient(90deg,rgba(255,220,190,.18) 1px,transparent 1px)",
                  backgroundSize: "52px 52px",
                  transform:
                    "perspective(760px) rotateX(58deg) rotateZ(-24deg)",
                }}
              />

              {/* Craters */}
              {[
                ["9%", "47%", 78],
                ["76%", "26%", 54],
                ["76%", "79%", 110],
                ["23%", "84%", 42],
              ].map(([left, top, size], i) => (
                <div
                  key={i}
                  className="pointer-events-none absolute rounded-full border-[9px] border-orange-200/10 bg-orange-950/10 shadow-[inset_6px_8px_12px_rgba(14,10,25,.35)]"
                  style={{
                    left,
                    top,
                    width: size,
                    height: size * 0.48,
                    transform: "rotate(-22deg)",
                  }}
                />
              ))}

              {/* Routes between zones */}
              <svg
                viewBox="0 0 850 760"
                preserveAspectRatio="none"
                className="pointer-events-none absolute inset-0 h-full w-full"
              >
                <path
                  d="M240 460 L430 345 L650 420 L520 610 L240 460"
                  stroke="#77dcff"
                  strokeWidth="3"
                  strokeDasharray="9 10"
                  opacity=".32"
                  fill="none"
                />
                <circle cx="430" cy="345" r="48" fill="none" stroke="#67e8f9" strokeOpacity=".12" strokeDasharray="3 12" />
                <circle cx="650" cy="420" r="45" fill="none" stroke="#67e8f9" strokeOpacity=".12" strokeDasharray="3 12" />
              </svg>

              {/* Screen header */}
              <div className="absolute left-5 top-5 z-20">
                <div className="flex items-center gap-2 text-xs font-black tracking-[.22em] text-cyan-200">
                  <Orbit className="h-4 w-4" />
                  MARS BASE / SECTOR 27001
                </div>
                <p className="mt-1 text-[11px] text-white/45">
                  Bấm vào tòa nhà để chọn nhóm ISO
                </p>
              </div>

              {/* Planet decoration */}
              <div className="pointer-events-none absolute right-7 top-8 h-24 w-24 rounded-full bg-gradient-to-br from-cyan-300 via-blue-500 to-indigo-900 opacity-70 shadow-[0_0_35px_rgba(59,130,246,.22)]">
                <div className="absolute left-2 top-6 h-3 w-12 rotate-[-18deg] rounded-full bg-cyan-100/25" />
                <div className="absolute right-2 top-12 h-4 w-6 rounded-full bg-indigo-950/30" />
              </div>

              {/* Three clickable buildings */}
              <IsometricBuilding
                id="A.6"
                label="Tòa nhà Nhân sự"
                tooltip={
                  runningId?.startsWith("A.6")
                    ? "Đang quét hồ sơ ứng viên..."
                    : "Khu Nhân sự: sẵn sàng kiểm tra"
                }
                color="#54e4ea"
                active={selectedGroup === "A.6"}
                position={{ left: "7%", top: "36%" }}
                onClick={() => selectGroup(GROUPS[0])}
              />

              <IsometricBuilding
                id="A.7"
                label="Khu vực An ninh"
                tooltip="Đang giám sát vành đai bảo vệ"
                color="#ffb869"
                active={selectedGroup === "A.7"}
                position={{ left: "48%", top: "25%" }}
                onClick={() => selectGroup(GROUPS[1])}
              />

              <IsometricBuilding
                id="A.8"
                label="Trung tâm Dữ liệu"
                tooltip="15 Agents đang trực (demo)"
                color="#9e94ff"
                active={selectedGroup === "A.8"}
                position={{ left: "34%", top: "57%" }}
                onClick={() => selectGroup(GROUPS[2])}
              />

              {/* Scan marker */}
              <div className="pointer-events-none absolute bottom-24 right-8 flex items-center gap-2 rounded-full border border-sky-300/20 bg-slate-950/50 px-3 py-2 text-[10px] text-cyan-200 backdrop-blur-md">
                <Activity className="h-3.5 w-3.5 animate-pulse" />
                LIVE SIMULATION
              </div>

              {/* Tab-specific overlays */}
              {activeTab === "Báo cáo tiến độ" && (
                <div className="absolute left-1/2 top-[12%] z-30 w-[350px] -translate-x-1/2 rounded-2xl border border-cyan-300/30 bg-slate-950/90 p-5 shadow-2xl backdrop-blur-xl">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 text-cyan-300" />
                    <h3 className="font-black">Báo cáo nhiệm vụ</h3>
                  </div>

                  <p className="mb-4 mt-1 text-xs text-slate-400">
                    {totalCompleted}/56 tác vụ demo hoàn tất
                  </p>

                  {GROUPS.map((group) => (
                    <div key={group.id} className="mb-4">
                      <div className="mb-1 flex justify-between text-xs">
                        <span>{group.id} — {group.label}</span>
                        <span>
                          {countCompleted(group.id)}/
                          {CONTROL_CATALOG[group.id].length}
                        </span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-slate-700">
                        <div
                          className="h-full rounded-full bg-cyan-400"
                          style={{
                            width: `${
                              (countCompleted(group.id) /
                                CONTROL_CATALOG[group.id].length) *
                              100
                            }%`,
                          }}
                        />
                      </div>
                    </div>
                  ))}

                  <p className="text-[10px] text-slate-500">
                    Dữ liệu được lưu trong React State của phiên demo.
                  </p>
                </div>
              )}

              {activeTab === "Tổng quan" && (
                <div className="absolute bottom-28 left-5 z-20 rounded-2xl border border-white/10 bg-slate-950/55 px-4 py-3 backdrop-blur-md">
                  <div className="flex items-center gap-2 text-xs font-black text-cyan-200">
                    <Sparkles className="h-4 w-4" />
                    NHIỆM VỤ HIỆN TẠI
                  </div>
                  <div className="mt-1 text-sm font-bold">
                    {selectedControl.id} — {selectedControl.title}
                  </div>
                  <div className="mt-1 text-[11px] text-slate-400">
                    Khu vực: {selectedZone.building}
                  </div>
                </div>
              )}

              {activeTab === "Bản đồ Sao Hỏa" && (
                <div className="absolute bottom-28 left-5 z-20 rounded-xl border border-cyan-300/20 bg-slate-950/60 px-4 py-2 text-xs text-cyan-200 backdrop-blur-md">
                  <Radar className="mr-2 inline h-4 w-4" />
                  BẢN ĐỒ CĂN CỨ • 3 KHU VỰC HOẠT ĐỘNG
                </div>
              )}

              {/* QUICK ACTION BAR */}
              <div className="absolute bottom-5 left-1/2 z-40 flex w-max max-w-[96%] -translate-x-1/2 items-center gap-1 rounded-full border border-sky-300/20 bg-slate-950/80 p-1.5 shadow-[0_12px_40px_rgba(0,0,0,.45)] backdrop-blur-xl">
                {tabItems.map((tab) => (
                  <button
                    key={tab.title}
                    type="button"
                    onClick={() => setActiveTab(tab.title)}
                    className={`flex items-center gap-2 rounded-full px-3 py-3 text-[11px] font-bold transition-all sm:px-5 ${
                      activeTab === tab.title
                        ? "bg-cyan-400 text-slate-950 shadow-[0_0_20px_rgba(34,211,238,.3)]"
                        : "text-slate-300 hover:bg-white/10"
                    }`}
                  >
                    <tab.Icon className="h-4 w-4" />
                    <span>{tab.title}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* RIGHT COMMAND PANEL */}
          <GlassPanel className="space-scroll max-h-[760px] overflow-y-auto p-5 xl:h-[760px]">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-black tracking-[.16em] text-cyan-300">
                <Zap className="h-4 w-4" />
                COMMAND CENTER
              </div>
              <div className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2.5 py-1 text-[10px] text-emerald-300">
                ONLINE
              </div>
            </div>

            <div className="rounded-2xl border border-sky-300/15 bg-slate-900/65 p-4">
              <div className="text-xs font-black tracking-widest text-cyan-300">
                CHI TIẾT CONTROL
              </div>

              <h2 className="mt-3 text-2xl font-black leading-tight">
                {selectedControl.id}
              </h2>
              <h3 className="mt-1 text-lg font-bold">
                {selectedControl.title}
              </h3>

              <p className="mt-3 text-sm leading-relaxed text-slate-400">
                {DESCRIPTIONS[selectedControl.id] ||
                  `Đánh giá biện pháp kiểm soát ${selectedControl.id} dựa trên tài liệu và bằng chứng được cung cấp.`}
              </p>

              <div className="my-4 h-px bg-white/10" />

              <div className="flex items-center justify-between gap-3">
                <span className="text-xs text-slate-400">
                  Trạng thái
                </span>
                <span
                  className={`rounded-full border px-3 py-1 text-[11px] font-bold ${
                    completed[selectedId]
                      ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-300"
                      : runningId === selectedId
                      ? "border-cyan-400/30 bg-cyan-400/10 text-cyan-300"
                      : "border-amber-300/20 bg-amber-400/10 text-amber-200"
                  }`}
                >
                  {runningId === selectedId
                    ? "Đang thực hiện"
                    : completed[selectedId]
                    ? "Hoàn tất mô phỏng"
                    : "Chưa có kết luận"}
                </span>
              </div>
            </div>

            {/* LAUNCH BUTTON */}
            <button
              type="button"
              disabled={!!runningId}
              onClick={launchAgent}
              className="group relative mt-5 w-full overflow-hidden rounded-2xl border border-cyan-200/40 bg-gradient-to-r from-blue-600 via-sky-500 to-cyan-400 px-4 py-5 text-sm font-black text-white shadow-[0_0_30px_rgba(37,99,235,.36)] transition-all hover:-translate-y-0.5 hover:shadow-[0_0_42px_rgba(34,211,238,.52)] disabled:cursor-wait disabled:opacity-75"
            >
              <div className="absolute inset-0 bg-gradient-to-t from-transparent to-white/15" />
              <span className="relative flex items-center justify-center gap-2">
                {runningId ? (
                  <>
                    <Loader2 className="h-6 w-6 animate-spin" />
                    <span className="text-center">
                      Đang bay đến {GROUPS.find(
                        (group) => group.id === runningId.split(".").slice(0, 2).join(".")
                      )?.building || "khu vực mục tiêu"}...
                    </span>
                  </>
                ) : (
                  <>
                    <Rocket className="h-6 w-6 transition-transform group-hover:-translate-y-1 group-hover:translate-x-1" />
                    🚀 PHÁI AI AGENT ĐI KIỂM TOÁN
                  </>
                )}
              </span>
            </button>

            <div className="mt-2 text-center text-[10px] text-slate-500">
              Chế độ mô phỏng • Thời gian nhiệm vụ 3 giây
            </div>

            {/* EVIDENCE UPLOAD */}
            <div className="mt-6">
              <div className="mb-3 flex items-center gap-2 text-xs font-black tracking-wider">
                <FileCheck2 className="h-4 w-4 text-cyan-300" />
                EVIDENCE REPOSITORY
              </div>

              <div className="rounded-2xl border border-dashed border-sky-300/25 bg-slate-900/50 p-4">
                <label className="mb-2 block text-[11px] text-slate-400">
                  Loại bằng chứng
                </label>

                <select
                  value={selectedEvidence}
                  onChange={(event) =>
                    setSelectedEvidence(event.target.value)
                  }
                  className="mb-3 w-full rounded-xl border border-slate-600 bg-[#101b31] px-3 py-3 text-xs text-white outline-none focus:border-cyan-400"
                >
                  {EVIDENCE_TYPES.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>

                <label
                  htmlFor="iso-evidence-file"
                  className="flex cursor-pointer flex-col items-center justify-center rounded-xl border border-sky-300/15 bg-white/[.04] px-3 py-5 text-center hover:bg-white/[.07]"
                >
                  <UploadCloud className="mb-2 h-8 w-8 text-cyan-300" />
                  <span className="text-xs font-bold">
                    {file ? file.name : "Chọn tài liệu"}
                  </span>
                  <span className="mt-1 text-[10px] text-slate-500">
                    PDF, DOCX, JSON, CSV
                  </span>
                </label>

                <input
                  id="iso-evidence-file"
                  type="file"
                  accept=".pdf,.docx,.doc,.json,.csv"
                  className="sr-only"
                  onChange={(event) =>
                    setFile(event.target.files?.[0] || null)
                  }
                />

                <button
                  type="button"
                  onClick={attachEvidence}
                  className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl border border-cyan-300/20 bg-cyan-400/10 px-4 py-3 text-xs font-bold text-cyan-200 transition hover:bg-cyan-400/20"
                >
                  <FileUp className="h-4 w-4" />
                  Tải lên tài liệu
                </button>
              </div>

              {uploadedFiles.length > 0 && (
                <div className="mt-3 space-y-2">
                  {uploadedFiles.slice(0, 3).map((item, index) => (
                    <div
                      key={`${item.name}-${index}`}
                      className="rounded-lg border border-white/10 bg-slate-900/60 p-2 text-[11px]"
                    >
                      <div className="truncate font-bold text-slate-200">
                        {item.name}
                      </div>
                      <div className="mt-1 text-slate-500">
                        {item.id} • {item.control} • Chờ tích hợp API
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* STATUS */}
            <div className="mt-6 rounded-2xl border border-indigo-400/20 bg-indigo-400/[.07] p-4">
              <div className="flex items-center gap-2 text-xs font-bold text-indigo-200">
                <ShieldCheck className="h-4 w-4" />
                TRẠNG THÁI CĂN CỨ
              </div>
              <div className="mt-3 grid grid-cols-2 gap-3">
                <div>
                  <div className="text-[10px] text-slate-500">
                    Nhiệm vụ hoàn tất
                  </div>
                  <div className="mt-1 text-lg font-black">
                    {totalCompleted} / 56
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-500">
                    AI Agent
                  </div>
                  <div className="mt-1 flex items-center gap-2 text-sm font-bold text-emerald-300">
                    <Activity className="h-4 w-4" />
                    {runningId ? "Đang xử lý" : "Sẵn sàng"}
                  </div>
                </div>
              </div>
            </div>

            {/* ACTIVITY LOG */}
            <div className="mt-5">
              <div className="mb-3 flex items-center gap-2 text-xs font-black tracking-wide">
                <Clock3 className="h-4 w-4 text-cyan-300" />
                NHẬT KÝ HOẠT ĐỘNG
              </div>

              {history.length === 0 ? (
                <div className="rounded-xl border border-white/10 bg-white/[.03] p-4 text-xs text-slate-500">
                  Chưa có nhiệm vụ nào hoàn tất trong phiên demo.
                </div>
              ) : (
                <div className="space-y-2">
                  {history.map((event, index) => (
                    <div
                      key={`${event.id}-${index}`}
                      className="flex items-start gap-2 rounded-lg bg-white/[.04] p-3 text-[11px]"
                    >
                      <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
                      <div>
                        <div className="font-bold text-slate-200">
                          {event.id} — {event.text}
                        </div>
                        <div className="mt-1 text-slate-500">
                          {event.time}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </GlassPanel>
        </div>

        {/* NOTIFICATIONS */}
        {toast && (
          <div
            role="status"
            aria-live="polite"
            className="fixed bottom-5 right-5 z-50 max-w-sm rounded-2xl border border-cyan-300/30 bg-slate-900/95 px-5 py-4 text-sm font-medium text-cyan-100 shadow-2xl backdrop-blur-xl"
          >
            <div className="flex items-start gap-3">
              <Bot className="h-5 w-5 shrink-0 text-cyan-300" />
              <span>{toast}</span>
              <button
                type="button"
                onClick={() => setToast("")}
                className="ml-auto text-slate-400 hover:text-white"
                aria-label="Đóng thông báo"
              >
                ×
              </button>
            </div>
          </div>
        )}

        <footer className="mt-4 flex flex-wrap items-center justify-between gap-2 px-2 text-[10px] text-slate-500">
          <span>ISO ENTERPRISE LAB • MARS SECURITY SIMULATION</span>
          <span>
            UI Prototype · React + Tailwind CSS · Chưa kết nối backend
          </span>
        </footer>
      </div>
    </div>
  );
}
