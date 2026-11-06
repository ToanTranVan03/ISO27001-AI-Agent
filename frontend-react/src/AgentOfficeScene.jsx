import { ROLES, STATUS_LABELS, activeRole, roleFeedback, roleStatus } from "./missionView";

function lines(text,max=32) {
  const words=text.split(/\s+/);const rows=[""];
  for(const word of words){const last=rows.length-1;if((rows[last]+" "+word).trim().length>max&&rows[last])rows.push(word);else rows[last]=(rows[last]+" "+word).trim();}
  return rows.slice(0,2).map((row,index)=>index===1&&rows.length>2?row.slice(0,max-1)+"…":row);
}

export default function AgentOfficeScene({mission,focused,onFocus}) {
  const running=activeRole(mission);
  const currentIndex=ROLES.findIndex(role=>role.id===running);
  const positions=[[35,38],[535,38],[35,262],[535,262]];
  const courier=currentIndex<0?[500,240]:[currentIndex%2===0?478:520,currentIndex<2?138:362];
  const completed=(mission?.subtasks||mission?.tasks||[]).filter(task=>task.status==="completed").length;
  return <div className="mw-map"><div className="mw-map-heading"><span><i className={running?"is-live":""}/>{running?`${ROLES.find(role=>role.id===running).agent} đang thực hiện` : mission?STATUS_LABELS[mission.status]:"Đội Agent sẵn sàng"}</span><small>Chọn nhân vật hoặc phòng để xem công việc</small></div>
    <div className="mw-map-scroll"><svg viewBox="0 0 1000 488" role="group" aria-label="Văn phòng Agent; bốn phòng với trạng thái từ backend">
      <defs><pattern id="agent-office-floor" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#b3c7cb" strokeWidth=".45" opacity=".45"/></pattern></defs>
      <rect width="1000" height="488" rx="20" fill="#dce7e8"/>
      <rect x="14" y="16" width="972" height="455" rx="20" fill="#eef2ed" stroke="#becfd0" strokeWidth="2"/>
      <rect x="18" y="20" width="964" height="447" rx="18" fill="url(#agent-office-floor)"/>
      <path d="M500 36V448M28 244H972" stroke="#b9cdd0" strokeWidth="3" strokeDasharray="5 9"/>
      {ROLES.map((role,index)=>{
        const [x,y]=positions[index];const state=roleStatus(mission,role.id);const working=state==="running";
        const stopped=["blocked","failed"].includes(state);const selected=focused===role.id;
        const badge=stopped?"#d47970":working?"#d5a04f":["completed","approved","awaiting_review"].includes(state)?"#4f9d86":"#8b9fa5";
        const speech=lines(roleFeedback(mission,role.id));const px=working?194:94,py=working?126:147;
        return <g key={role.id} transform={`translate(${x} ${y})`} role="button" tabIndex={0} aria-label={`Xem ${role.agent}: ${STATUS_LABELS[state]}`} aria-pressed={selected} onClick={()=>onFocus(role.id)} onKeyDown={event=>{if(event.key==="Enter"||event.key===" "){event.preventDefault();onFocus(role.id);}}} className="mw-room">
          <title>{`${role.agent} · ${STATUS_LABELS[state]}`}</title>
          <path d="M0 12L16 0H430L414 12Z" fill="#ccdadd"/><rect y="12" width="430" height="179" rx="12" fill={selected?"#fffef7":"#f7f8f2"} stroke={selected?role.color:"#d0dcdc"} strokeWidth={selected?3:1.5}/><path d="M430 12L439 3V181L430 191Z" fill="#bdcfd1"/>
          <rect x="14" y="26" width="5" height="22" rx="2" fill={role.color}/><text x="27" y="41" fontSize="13" fontWeight="800" fill="#294953">{role.agent}</text>
          <rect x="276" y="24" width="139" height="24" rx="12" fill={badge} opacity=".15"/><circle cx="288" cy="36" r="3" fill={badge}/><text x="300" y="40" fontSize="10" fontWeight="700" fill={badge}>{STATUS_LABELS[state]}</text>
          <g transform="translate(170 91)"><path d="M0 7H83V39H0Z" fill="#c5bca8"/><rect width="83" height="32" rx="5" fill="#e2d7bf"/><rect x="26" y="-29" width="33" height="26" rx="3" fill="#345463"/><rect x="29" y="-26" width="27" height="20" rx="2" fill={working?role.color:"#799499"}/><path d="M40-3v5" stroke="#52737c" strokeWidth="4"/><rect x="23" y="12" width="39" height="5" rx="2" fill="#9eaea7"/></g>
          <g transform="translate(31 107)"><rect width="81" height="37" rx="9" fill="#c2cfc7"/><rect x="7" y="-8" width="67" height="30" rx="7" fill="#dce4d7"/></g>
          <g transform="translate(396 150)"><ellipse cy="13" rx="12" ry="4" fill="#a9b9ae" opacity=".4"/><path d="M-8 0H8L5 15H-5Z" fill="#c79d79"/><path d="M0 2V-24M0-5Q-22-28-14-25Q-1-24 0-5M0-12Q22-34 19-20Q16-9 0-4" fill="#79a58c" stroke="#5c8b76" strokeWidth="1.5"/></g>
          <g className="mw-avatar" style={{transform:`translate(${px}px,${py}px)`}}>{working&&<ellipse cy="15" rx="24" ry="9" fill={role.color} opacity=".18" className="mw-work-pulse"/>}<ellipse cy="17" rx="18" ry="6" fill="#6e8c88" opacity=".2"/><g className={working?"mw-avatar-working":""}><path d="M-6 7v10m12-10v10" stroke="#36535f" strokeWidth="6" strokeLinecap="round"/><rect x="-12" y="-8" width="24" height="20" rx="7" fill={role.color}/><rect x="-15" y="-31" width="30" height="27" rx="10" fill="#fcfcf4" stroke="#a8babb"/><rect x="-10" y="-25" width="20" height="13" rx="5" fill="#2d5361"/><circle cx="-4" cy="-19" r="2" fill={role.color}/><circle cx="4" cy="-19" r="2" fill={role.color}/><path d="M0-31v-6" stroke="#739299" strokeWidth="2"/><circle cy="-39" r="3" fill={badge}/><path d="M-13-4l-7 8m33-8l7 8" stroke={role.color} strokeWidth="5" strokeLinecap="round"/></g></g>
          <g transform="translate(266 78)"><rect width="149" height="58" rx="9" fill="#eaf0e9" stroke="#d5e0d8"/><text x="10" y="18" fontSize="8" fontWeight="800" fill="#789185">PHẢN HỒI TỪ THỰC THI</text>{speech.map((line,i)=><text key={i} x="10" y={33+i*13} fontSize="8" fill="#35554c">{line}</text>)}</g>
          <text x="18" y="176" fontSize="9" fill="#769096">{role.job}</text>
        </g>;
      })}
      <g className="mw-courier" style={{transform:`translate(${courier[0]}px,${courier[1]}px)`}}><circle r="14" fill="#315668"/><path d="M-7-4H1L4-1H8V6H-7Z" fill="#f3cb84"/></g>
      <rect x="384" y="231" width="232" height="25" rx="12" fill="#eef2ed" stroke="#bdcfd0"/><text x="500" y="247" textAnchor="middle" fontSize="9" fill="#577681">{mission?`${completed} công việc đã lưu kết quả` : "GIAO VIỆC → CÔNG CỤ → KẾT QUẢ"}</text>
    </svg></div>
  </div>;
}
