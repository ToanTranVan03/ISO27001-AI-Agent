
import React from "react";
import {
  Bot,
  BrainCircuit,
  CheckCircle2,
  ClipboardCheck,
  FileSearch,
  FileText,
  Loader2,
} from "lucide-react";

// Đường đi của robot khi được giao nhiệm vụ
const MISSION_PATHS = {
  "A.6": "M 405 670 Q 290 590 205 485",
  "A.7": "M 405 670 Q 545 560 575 380",
  "A.8": "M 405 670 Q 465 620 435 570",
};

// Robot chibi được dựng bằng SVG.
// Có mắt, miệng, chân, tay và antenna.
function ChibiRobot({ color = "#FFA75B", scale = 1 }) {
  return (
    <g transform={`scale(${scale})`}>
      <ellipse cx="0" cy="18" rx="15" ry="5" fill="#8C674E" opacity=".2" />

      <g>
        <animateTransform
          attributeName="transform"
          type="translate"
          values="0 0;0 -3;0 0"
          dur=".65s"
          repeatCount="indefinite"
        />

        <rect x="-10" y="8" width="7" height="12" rx="3" fill="#788EA8"/>
        <rect x="3" y="8" width="7" height="12" rx="3" fill="#788EA8"/>

        <rect
          x="-14" y="-10" width="28" height="27" rx="10"
          fill={color} stroke="#FFF9E8" strokeWidth="2"
        />
        <rect x="-20" y="-5" width="7" height="16" rx="3" fill={color}/>
        <rect x="13" y="-5" width="7" height="16" rx="3" fill={color}/>

        <rect
          x="-19" y="-35" width="38" height="29" rx="12"
          fill="#FFF7E8" stroke={color} strokeWidth="3"
        />

        <rect x="-14" y="-29" width="28" height="17" rx="8" fill="#415A69"/>
        <ellipse cx="-6" cy="-22" rx="2.5" ry="3" fill="#FFF"/>
        <ellipse cx="6" cy="-22" rx="2.5" ry="3" fill="#FFF"/>
        <path
          d="M-4 -16 Q0 -13 4 -16"
          fill="none" stroke="#FFD694" strokeWidth="2"
          strokeLinecap="round"
        />

        <path d="M0 -35 V-43" stroke="#6F8195" strokeWidth="2"/>
        <circle cx="0" cy="-45" r="4" fill="#FFBF78"/>
      </g>
    </g>
  );
}

function Drone({ color = "#FFF9EA" }) {
  return (
    <g>
      <ellipse cx="0" cy="22" rx="25" ry="4" fill="#7B634E" opacity=".16"/>
      <path
        d="M-24 0 L-11 -10 H11 L24 0 L12 12 H-12 Z"
        fill={color} stroke="#C9AC91" strokeWidth="2"
      />
      <rect x="-9" y="-5" width="18" height="12" rx="6" fill="#7CC8DC"/>
      <circle cx="-4" cy="0" r="2" fill="white"/>
      <circle cx="4" cy="0" r="2" fill="white"/>

      <path d="M-18 -5 H-35 M18 -5 H35" stroke="#8397A2" strokeWidth="3"/>
      <ellipse cx="-35" cy="-6" rx="15" ry="3" fill="#F6F0E8" opacity=".9"/>
      <ellipse cx="35" cy="-6" rx="15" ry="3" fill="#F6F0E8" opacity=".9"/>

      <circle cx="0" cy="13" r="3" fill="#FFAF63"/>
    </g>
  );
}

function SmallFacility({ x, y, color, label, symbol }) {
  return (
    <g transform={`translate(${x} ${y})`}>
      <ellipse cx="0" cy="17" rx="49" ry="13" fill="#98613F" opacity=".16"/>
      <path
        d="M-45 0 L0 -24 L45 0 L0 24 Z"
        fill="#FFF1D7" stroke="#D3A17E" strokeWidth="2"
      />
      <path
        d="M-25 -3 L0 -17 L25 -3 L0 11 Z"
        fill={color} stroke="#FFF8E8" strokeWidth="2"
      />
      <path d="M-25 -3 V12 L0 26 V11 Z" fill="#C78E70"/>
      <path d="M0 11 L25 -3 V12 L0 26 Z" fill="#B9876C"/>

      <text
        x="0" y="3"
        textAnchor="middle"
        fill="#604C45"
        fontSize="14"
        fontWeight="bold"
      >
        {symbol}
      </text>

      <rect
        x="-49" y="30" width="98" height="22" rx="11"
        fill="#FFF9EC" stroke="#E9C9A9"
      />
      <text
        x="0" y="44"
        textAnchor="middle"
        fill="#90674C"
        fontSize="10"
        fontWeight="bold"
      >
        {label}
      </text>
    </g>
  );
}

// Các nhân vật và cơ sở phụ nằm trên bản đồ 3D.
// SVG viewBox giúp chuyển động theo cùng hệ tọa độ bản đồ.
export default function BaseLife({ runningZone }) {
  return (
    <svg
      viewBox="0 0 850 760"
      preserveAspectRatio="none"
      className="pointer-events-none absolute inset-0 z-20 h-full w-full"
      aria-hidden="true"
    >
      {/* Các công trình phụ của doanh nghiệp */}
      <SmallFacility
        x={118}
        y={320}
        color="#F4C88C"
        label="Bến Drone"
        symbol="✈"
      />
      <SmallFacility
        x={704}
        y={615}
        color="#A7D5BD"
        label="Trạm Năng Lượng"
        symbol="⚡"
      />
      <SmallFacility
        x={715}
        y={475}
        color="#CABBE7"
        label="Kho Bằng Chứng"
        symbol="▤"
      />

      {/* Tuyến tuần tra HR -> Data Center */}
      <g>
        <animateMotion
          path="M 205 510 C 270 520 350 565 425 610 C 355 560 275 520 205 510"
          dur="17s"
          repeatCount="indefinite"
          rotate="0"
        />
        <ChibiRobot color="#FFB16B" scale={0.75}/>
      </g>

      {/* Robot an ninh */}
      <g>
        <animateMotion
          path="M 620 440 C 590 500 510 565 460 585 C 515 525 600 465 620 440"
          dur="19s"
          repeatCount="indefinite"
          rotate="0"
        />
        <ChibiRobot color="#A2D1AD" scale={0.7}/>
      </g>

      {/* Robot vận chuyển dữ liệu */}
      <g>
        <animateMotion
          path="M 295 630 C 365 650 520 655 675 555 C 600 680 400 700 295 630"
          dur="22s"
          repeatCount="indefinite"
          rotate="0"
        />
        <ChibiRobot color="#B9AFE9" scale={0.68}/>
      </g>

      {/* Drone 1: bay trên bầu trời */}
      <g>
        <animateMotion
          path="M 75 235 C 280 125 520 155 755 250 C 540 125 290 150 75 235"
          dur="21s"
          repeatCount="indefinite"
          rotate="auto"
        />
        <Drone/>
      </g>

      {/* Drone 2: tuần tra phía sau */}
      <g opacity=".85">
        <animateMotion
          path="M 760 335 Q 450 175 170 330 Q 450 240 760 335"
          dur="28s"
          repeatCount="indefinite"
          rotate="auto"
        />
        <g transform="scale(.65)">
          <Drone color="#E7F4F1"/>
        </g>
      </g>

      {/* Robot được phái đi làm nhiệm vụ */}
      {runningZone && MISSION_PATHS[runningZone] && (
        <g key={runningZone}>
          <animateMotion
            path={MISSION_PATHS[runningZone]}
            dur="3.2s"
            fill="freeze"
            repeatCount="1"
            rotate="0"
          />

          <circle
            cx="0"
            cy="0"
            r="26"
            fill="#FFF4C6"
            opacity=".45"
          >
            <animate
              attributeName="r"
              values="22;30;22"
              dur="1s"
              repeatCount="indefinite"
            />
          </circle>

          <ChibiRobot color="#FF812F" scale={1.15}/>
        </g>
      )}

      {/* Hạt bụi Sao Hỏa bay nhẹ */}
      {[
        [130, 460], [360, 320], [600, 540], [740, 340],
        [280, 710], [550, 680], [95, 580],
      ].map(([x, y], index) => (
        <circle key={index} cx={x} cy={y} r="3" fill="#FFF3CF">
          <animate
            attributeName="cy"
            values={`${y};${y - 18};${y}`}
            dur={`${3 + index % 3}s`}
            repeatCount="indefinite"
          />
          <animate
            attributeName="opacity"
            values=".15;.8;.15"
            dur={`${3 + index % 3}s`}
            repeatCount="indefinite"
          />
        </circle>
      ))}
    </svg>
  );
}

// Bảng hiển thị các vai trò trong đội AI Agent.
// Các bước ở chế độ demo là tiến trình mô phỏng,
// KHÔNG phải kết quả kiểm toán ISO thật.
const MISSION_STEPS = [
  { name: "Planner Agent", detail: "Lập kế hoạch", Icon: BrainCircuit },
  { name: "Collector Agent", detail: "Thu thập evidence", Icon: FileSearch },
  { name: "Evaluator Agent", detail: "Đối chiếu tiêu chí", Icon: Bot },
  { name: "Verifier Agent", detail: "Xác minh dữ liệu", Icon: ClipboardCheck },
  { name: "Reporter Agent", detail: "Tổng hợp báo cáo", Icon: FileText },
];

export function AgentCrewPanel({
  running = false,
  stage = -1,
  completed = false,
  live = false,
  realStatus = "Chưa bắt đầu",
  controlId = "A.6.1",
}) {
  return (
    <section className="mt-5 rounded-[25px] border border-white/10 bg-[#2C3C50] p-4">
      <div className="mb-2 flex items-center gap-2 font-black text-[#FFD0A5]">
        <Bot className="h-5 w-5"/>
        ĐỘI AI AGENT
      </div>

      <p className="mb-4 text-xs text-[#BFC9D5]">
        Nhiệm vụ {controlId} • {live ? "Theo dõi job FastAPI" : "Chế độ trình diễn"}
      </p>

      <div className="space-y-2">
        {MISSION_STEPS.map((step, index) => {
          const done = !live && ((running && stage > index) || (!running && completed));

          const active = running && stage === index;

          return (
            <div
              key={step.name}
              className={`flex items-center gap-3 rounded-[17px] p-3 transition-colors ${
                active
                  ? "bg-[#FF914D]/20"
                  : "bg-[#203044]"
              }`}
            >
              <div
                className={`rounded-[13px] p-2 ${
                  active
                    ? "bg-[#FF914D] text-white"
                    : done
                      ? "bg-[#6AAB87]/25 text-[#BCE4BF]"
                      : "bg-white/5 text-[#94A5B9]"
                }`}
              >
                <step.Icon className="h-4 w-4"/>
              </div>

              <div className="min-w-0 flex-1">
                <div className="text-xs font-black">
                  {step.name}
                </div>
                <div className="text-[11px] text-[#BFC9D5]">
                  {step.detail}
                </div>
              </div>

              {active ? (
                <Loader2 className="h-4 w-4 animate-spin text-[#FFA965]"/>
              ) : done ? (
                <CheckCircle2 className="h-4 w-4 text-[#A9DBB3]"/>
              ) : (
                <span className="h-2 w-2 rounded-full bg-[#53667B]"/>
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-4 rounded-[15px] bg-[#1C2B3A] p-3 text-[11px] text-[#D8E0E8]">
        {live
          ? (running
              ? "Agent job đang RUNNING trong PostgreSQL. Vòng sáng qua các vai trò chỉ là minh họa; backend chưa phát sự kiện từng node."
              : `Trạng thái thật: ${realStatus}. Xem kết luận ISO và bằng chứng ở phía trên / lịch sử.`)
          : running
            ? `Robot đang thực hiện bước ${Math.min(stage + 1, 5)}/5...`
            : completed
              ? "Đã kết thúc mô phỏng. Chưa xác định tuân thủ ISO."
              : "Đội Agent đang chờ nhiệm vụ mới."}
      </div>
    </section>
  );
}
