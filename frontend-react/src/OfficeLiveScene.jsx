import { useEffect, useMemo, useState } from "react";
import { Radio, ScanLine, Users, ZoomIn, ZoomOut } from "lucide-react";
import { employeePhase, employeePosition, employeeStatus, recentSpeech, latestByEmployee } from "./officeLive";
import "./office-live.css";

const COLORS = ["#6c9e9b", "#df976c", "#8b83b8", "#628fb7", "#b38b5c", "#bd798d"];
const PHASES = {idle:"Chờ lệnh", routine:"Đã thực hiện", pending:"Chờ Agent kiểm tra", resolved:"Đã xử lý", review:"Cần rà soát"};

function Plant({x,y}) {
  return <g transform={`translate(${x} ${y})`}><ellipse cy="16" rx="17" ry="7" fill="#223c39" opacity=".12"/><path d="M-10 0h20l-3 18H-7z" fill="#c69975"/><path d="M0 4V-28M0-8Q-29-36-14-34Q0-32 0-8M0-15Q12-45 23-30Q24-15 0-8M0-2Q-29-17-22-24Q-10-30 0-2" fill="#568e70" stroke="#3c6e54" strokeWidth="2"/></g>;
}

function Person({employee,index,position,entry,selected,onSelect,workstation,now}) {
  const phase = employeePhase(entry,workstation);
  const color = phase === "resolved" ? "#219b79" : phase === "review" ? "#ce6659" : phase === "pending" ? "#cc8d39" : COLORS[index % COLORS.length];
  const name = employee.display_name || employee.employee_id;
  const shortName = name.includes("mô phỏng") ? `Nhân viên ${employee.employee_id.slice(-3)}` : name.split(" ").slice(-2).join(" ");
  return <g className={`office-person ${selected ? "is-selected" : ""}`} style={{transform:`translate(${position[0]}px,${position[1]}px)`}} role="button" tabIndex={0} aria-label={`Chọn ${name} ${employee.employee_id}`} aria-pressed={selected} onClick={()=>onSelect(employee.employee_id)} onKeyDown={e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();onSelect(employee.employee_id);}}}>
    <g transform={workstation?.state.location==="reception"?"scale(.65)":undefined}>
    <title>{`${name} · ${employee.employee_id} · ${employeeStatus(workstation)}`}</title>
    <ellipse cy="23" rx="22" ry="8" fill="#26483f" opacity=".14"/>
    {(selected || phase==="pending" || phase==="review") && <ellipse className={phase==="pending"?"office-signal":""} cy="23" rx="27" ry="11" fill="none" stroke={color} strokeWidth="2" strokeDasharray={selected?undefined:"4 3"}/>}
    <g className={workstation?.state.location==="desk" && workstation?.state.screen_state==="unlocked" ? "office-person-action" : ""}>
      <path d="M-8 8v14m16-14v14" stroke="#324958" strokeWidth="8" strokeLinecap="round"/>
      <path d="M-12-8q12-9 24 0l2 20h-28z" fill={color}/>
      <path d="M-12-5l-6 14m30-14l7 12" stroke={color} strokeWidth="7" strokeLinecap="round"/>
      <circle cy="-21" r="13" fill={index%3===0?"#c99172":"#efc4a0"}/>
      <path d="M-13-23q-1-19 17-12q12 4 8 16l-4-9q-7 3-12-1l-6 8z" fill={index%2?"#6a4a3f":"#33434c"}/>
      <circle cx="-4" cy="-20" r="1.2" fill="#34424b"/><circle cx="5" cy="-20" r="1.2" fill="#34424b"/>
      <path d="M-3-14q4 3 7-1" fill="none" stroke="#9f6555" strokeWidth="1.2"/>
      <rect x="1" y="-7" width="5" height="8" rx="1" fill="#fff3cf"/>
      {entry?.command==="/usb-la" && phase!=="resolved" && <g transform="translate(22 6) rotate(-30)"><rect width="8" height="15" rx="2" fill="#e79b48"/><rect x="1" y="-5" width="6" height="6" fill="#d8e1e5"/></g>}
      {entry?.command==="/nghi" && <g transform="translate(16 5)"><rect width="11" height="11" rx="2" fill="#fff6db"/><path d="M11 2q9 0 0 7" fill="none" stroke="#fff6db" strokeWidth="2"/></g>}
    </g>
    <rect x="-51" y="32" width="102" height="21" rx="10" fill={selected?"#21453f":"#f9f5e9"} stroke={selected?"#21453f":"#d9d5c7"}/>
    <text y="46" textAnchor="middle" fontSize="10" fontWeight="700" fill={selected?"#fff9ed":"#38554d"}>{shortName}</text>
    <circle cx="-43" cy="42" r="3" fill={workstation?.pending_count ? "#cc8d39" : workstation?.state.location==="break" ? "#df976c" : workstation?.state.shift==="on" ? "#219b79" : "#9ba69c"}/>
    {entry && (selected || recentSpeech(entry,now)) && <g transform="translate(-58 -67)"><rect width="116" height="29" rx="10" fill="#fffdf4" stroke={color}/><path d="M49 29l9 7 8-7" fill="#fffdf4" stroke={color}/><text x="58" y="19" textAnchor="middle" fontSize="10" fill="#3c534b">{entry.command}</text></g>}
    {entry?.incident_id && <g transform="translate(23 -39)"><circle r="10" fill={color}/><text textAnchor="middle" y="4" fill="white" fontSize="12" fontWeight="bold">{entry.verified?"✓":"!"}</text></g>}
    </g>
  </g>;
}

export default function OfficeLiveScene({employees,entries,selectedEmployee,onSelect,monitoring,workspace=[],onSuggest=()=>{}}) {
  const [patrol,setPatrol] = useState(0);
  const [zoom,setZoom] = useState(false);
  const [now,setNow] = useState(Date.now);
  useEffect(()=>{const timer=setInterval(()=>setNow(Date.now()),1000);return ()=>clearInterval(timer);},[]);
  useEffect(()=>{
    if (!monitoring.active) return;
    const timer=setInterval(()=>setPatrol(value=>(value+1)%4),4000);
    return ()=>clearInterval(timer);
  },[monitoring.active]);
  const machines=useMemo(()=>Object.fromEntries(workspace.map(item=>[item.employee_id,item])),[workspace]);
  const latest=useMemo(()=>({...latestByEmployee(entries),...Object.fromEntries(workspace.map(item=>[item.employee_id,item.state.last_receipt || null]))}),[entries,workspace]);
  const people=useMemo(()=>[...employees].sort((a,b)=>a.employee_id.localeCompare(b.employee_id)),[employees]);
  const current=latest[selectedEmployee];
  const focus=monitoring.state==="processing"?monitoring.current_finding:null;
  const targetIndex=people.findIndex(item=>item.employee_id===focus?.employee_id);
  const target=targetIndex>=0?employeePosition(targetIndex,latest[focus.employee_id],machines[focus.employee_id]?.state):null;
  const route=[[605,185],[605,395],[735,660],[395,660]];
  const agent=target?[target[0]+45,target[1]+25]:route[patrol];
  const resolved=entries.filter(item=>item.incident_id&&item.verified).length;
  return <section className="office-live" aria-label="Văn phòng tương tác trực tiếp">
    <div className="office-live-heading"><div><div className="office-eyebrow"><Radio size={13}/> VIỆT TÍN · OFFICE LIVE</div><h2>Hôm nay ở văn phòng</h2><p>Mỗi nhân viên một câu chuyện. Mỗi hành động một dấu vết.</p></div><span className="office-live-badge"><span/>{monitoring.active?"ĐANG GIÁM SÁT":"CHỜ BẮT ĐẦU"}</span></div>
    <div className="office-toolbar"><span><Users size={13}/>{people.length} nhân viên</span><span><ScanLine size={13}/>{workspace.reduce((sum,item)=>sum+item.pending_count,0)} sự kiện chờ kiểm tra</span><span>{resolved} đã xác minh / {entries.length} lệnh gần nhất</span><button onClick={()=>setZoom(!zoom)} aria-label={zoom?"Xem toàn văn phòng":"Phóng to khu làm việc"}>{zoom?<ZoomOut size={15}/>:<ZoomIn size={15}/>}</button></div>
    <div className="office-map"><svg viewBox={zoom?"35 65 600 550":"0 0 1000 740"} role="group" aria-label="Bản đồ văn phòng; chọn nhân viên để gửi bình luận">
      <defs><pattern id="office-floor" width="35" height="35" patternUnits="userSpaceOnUse"><path d="M35 0H0V35" fill="none" stroke="#b8c9ba" strokeWidth=".7" opacity=".35"/></pattern><linearGradient id="office-beam" x1="0" x2="1"><stop stopColor="#65c6ac" stopOpacity=".05"/><stop offset="1" stopColor="#65c6ac" stopOpacity=".45"/></linearGradient></defs>
      <rect width="1000" height="740" fill="#dce7dc"/>
      <rect x="22" y="24" width="956" height="694" rx="23" fill="#bdcbbf"/>
      <rect x="22" y="18" width="956" height="690" rx="23" fill="#e9eddf" stroke="#c3d0c2" strokeWidth="2"/>
      <rect x="35" y="75" width="580" height="535" rx="14" fill="#f5f0df" stroke="#d9d3bd" strokeWidth="2"/>
      <rect x="35" y="75" width="580" height="535" rx="14" fill="url(#office-floor)"/>
      <path d="M35 105h580" stroke="#d9d3bd"/><text x="59" y="95" fontSize="11" fill="#74816b" fontWeight="800" letterSpacing="2">KHÔNG GIAN LÀM VIỆC</text>
      {[0,1,2,3].map(i=><g key={i}><rect x={85+i*127} y="37" width="80" height="27" rx="5" fill="#9fbab2"/><rect x={89+i*127} y="40" width="72" height="20" rx="3" fill="#d7e9e5"/><path d={`M${125+i*127} 40v20`} stroke="#9fbab2" strokeWidth="3"/></g>)}
      <rect x="645" y="75" width="316" height="260" rx="14" fill="#dde6eb" stroke="#b8cbd0" strokeWidth="2"/>
      <text x="669" y="103" fontSize="11" fill="#607f8a" fontWeight="800" letterSpacing="2">TRUNG TÂM GIÁM SÁT</text>
      {[0,1,2].map(i=><g key={i} transform={`translate(${676+i*86} 129)`}><rect width="63" height="94" rx="7" fill="#405965"/><rect x="5" y="6" width="53" height="80" rx="4" fill="#2b414d"/>{[0,1,2,3].map(j=><g key={j}><rect x="10" y={14+j*17} width="35" height="10" rx="2" fill="#526b74"/><circle cx="49" cy={19+j*17} r="2" fill="#84d2ae"/></g>)}</g>)}
      <rect x="675" y="249" width="255" height="58" rx="9" fill="#edf4f2"/>
      <text x="695" y="272" fontSize="11" fill="#345d52" fontWeight="bold">AI AUDITOR</text><text x="695" y="290" fontSize="10" fill="#668079">{monitoring.active?"Quan sát → đối chiếu → xử lý":"Chờ lệnh để bắt đầu giám sát"}</text>
      <rect x="645" y="355" width="316" height="255" rx="14" fill="#f1e3cf" stroke="#d8c5aa" strokeWidth="2"/>
      <text x="669" y="380" fontSize="11" fill="#a18460" fontWeight="800" letterSpacing="2">GÓC NGHỈ</text>
      <text x="669" y="398" fontSize="9" fill="#a18460">Nhớ khóa màn hình trước khi rời bàn</text>
      <rect x="680" y="420" width="170" height="25" rx="9" fill="#ba9d7f"/><rect x="680" y="414" width="170" height="24" rx="9" fill="#d9bc91"/>
      <Plant x={917} y={429}/><Plant x={58} y={660}/><Plant x={932} y={660}/>
      <rect x="95" y="636" width="220" height="48" rx="10" fill="#537e70"/><text x="115" y="657" fill="#f3f0db" fontSize="11" fontWeight="bold">LỄ TÂN · VÀO CA</text><text x="115" y="673" fill="#cbded2" fontSize="9">Gõ /vao-ca để nhân viên nhận ca</text>
      <path d="M350 655H590V120M590 655H900" stroke="#a5b7a7" strokeWidth="2" strokeDasharray="6 8" fill="none"/>
      <text x="660" y="695" fill="#829381" fontSize="10" letterSpacing="3">VIỆT TÍN LOGISTICS / SIMULATION</text>
      {people.map((employee,index)=>{const [x,y]=employeePosition(index,null); const state=machines[employee.employee_id]?.state;return <g key={employee.employee_id} transform={`translate(${x-41} ${y-60})`}><rect x="0" y="4" width="83" height="37" rx="6" fill="#d0b996"/><rect width="83" height="35" rx="6" fill="#e3d0ad"/><rect x="24" y="-12" width="35" height="25" rx="3" fill="#415960"/><rect x="27" y="-9" width="29" height="19" rx="1" fill={state?.screen_state==="unlocked"&&state?.location!=="desk"?"#e6b76c":state?.screen_state==="locked"?"#758d91":"#a7c5c6"}/><rect x="36" y="13" width="11" height="4" rx="1" fill="#6e8785"/><rect x="19" y="21" width="40" height="6" rx="2" fill="#b0b7ab"/><circle cx="70" cy="18" r="4" fill="#f6f2de"/></g>;})}
      {target&&<path d={`M${agent[0]} ${agent[1]}L${target[0]-23} ${target[1]-25}L${target[0]+23} ${target[1]-25}Z`} fill="url(#office-beam)" className="office-signal"/>}
      {people.map((employee,index)=>{const [x,y]=employeePosition(index,null);return <text key={employee.employee_id} x={x+26} y={y-28} textAnchor="middle" fontSize="7" fill="#70877c">{employee.employee_id.slice(-3)}</text>;})}
      {people.map((employee,index)=><Person key={employee.employee_id} employee={employee} index={index} position={employeePosition(index,latest[employee.employee_id],machines[employee.employee_id]?.state)} entry={latest[employee.employee_id]} workstation={machines[employee.employee_id]} selected={employee.employee_id===selectedEmployee} onSelect={onSelect} now={now}/>)}
      <g className="office-robot" style={{transform:`translate(${agent[0]}px,${agent[1]}px)`}}><ellipse cy="19" rx="23" ry="9" fill="#264a40" opacity=".13"/><circle r="30" fill="none" stroke="#50ad91" strokeDasharray="4 5" className={monitoring.active?"office-signal":""}/><rect x="-17" y="-24" width="34" height="34" rx="12" fill="#fff9e7" stroke="#5d9d86" strokeWidth="2"/><rect x="-12" y="-17" width="24" height="15" rx="6" fill="#315952"/><circle cx="-5" cy="-10" r="2.3" fill="#9cebc0"/><circle cx="5" cy="-10" r="2.3" fill="#9cebc0"/><path d="M0-25v-8" stroke="#598b75" strokeWidth="2"/><circle cy="-34" r="4" fill="#e9b360"/><rect x="-9" y="9" width="18" height="9" rx="4" fill="#4f8571"/><text y="42" textAnchor="middle" fontSize="9" fontWeight="bold" fill="#2e6955">AI AUDITOR</text></g>
    </svg></div>
    <div className="office-toolbar" aria-label="Chọn nhiệm vụ theo khu vực"><span>Giao việc cho {selectedEmployee}:</span>{[{text:"/vao-ca",label:"Lễ tân · vào ca"},{text:"/lam-viec",label:"Bàn làm việc"},{text:"/nghi",label:"Góc nghỉ"},{text:"/tan-ca",label:"Tan ca"}].map(task=><button key={task.text} onClick={()=>onSuggest(task.text)} title="Điền lệnh vào bảng bình luận; nhấn Gửi để thực hiện">{task.label}</button>)}</div>
    <div className="office-bottom"><div><b>{current?.employee_name || people.find(p=>p.employee_id===selectedEmployee)?.display_name || "Chọn một nhân viên"}</b><span>{current ? `${current.text} · ${PHASES[employeePhase(current,machines[selectedEmployee])]}` : "Bấm vào nhân vật trên bản đồ để ra lệnh"}</span></div><span className="office-synthetic">DOANH NGHIỆP GIẢ LẬP</span></div>
  </section>;
}
