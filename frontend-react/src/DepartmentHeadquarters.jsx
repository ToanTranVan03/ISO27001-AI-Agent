const ROOMS=[
  {id:"coordination",name:"ĐIỀU PHỐI",color:"#78d7e9"},
  {id:"inventory",name:"TÀI SẢN & NHÂN SỰ",color:"#ffca91"},
  {id:"security",name:"SOC · ỨNG PHÓ",color:"#c4b5ff"},
  {id:"report",name:"KIỂM SOÁT NỘI BỘ",color:"#6ee7b7"},
];

export default function DepartmentHeadquarters({tasks=[],focused,onFocus}) {
  return <div className="overflow-x-auto border-b border-white/10 bg-[#0c1a29] px-4"><svg viewBox="0 0 1000 260" className="mx-auto block w-full min-w-[620px] max-w-6xl" role="group" aria-label="Sơ đồ trụ sở; chọn phòng để xem đầu ra">
    <defs><pattern id="hq-grid" width="30" height="30" patternUnits="userSpaceOnUse"><path d="M30 0H0V30" fill="none" stroke="#274253" strokeWidth=".6"/></pattern></defs>
    <rect width="1000" height="260" fill="url(#hq-grid)"/>
    <path d="M18 192L170 40H910L985 162L840 240H90Z" fill="#182d3a" stroke="#36535c"/>
    <path d="M140 203H845" fill="none" stroke="#50766e" strokeWidth="3" strokeDasharray="6 8"/>
    {[0,1,2].map(i=><text key={i} x={255+i*230} y="207" fill="#78ae9d" fontSize="20">→</text>)}
    {ROOMS.map((room,index)=>{
      const task=tasks.find(item=>item.id===room.id);
      const running=task?.status==="running",complete=task?.status==="completed";
      const status=running?"ĐANG THỰC HIỆN":complete?"ĐÃ BÀN GIAO":task?.status==="failed"?"GẶP LỖI":task?.status==="blocked"?"BỊ CHẶN":"CHỜ NHIỆM VỤ";
      return <g key={room.id} transform={`translate(${55+index*230} 38)`} role="button" tabIndex={0} aria-label={`Mở phòng ${room.name}`} aria-pressed={focused===room.id} onClick={()=>onFocus(room.id)} onKeyDown={event=>{if(event.key==="Enter"||event.key===" "){event.preventDefault();onFocus(room.id);}}} className="cursor-pointer outline-none focus-visible:opacity-75">
        <title>{`${room.name} · ${status}`}</title>
        <ellipse cx="100" cy="134" rx="91" ry="17" fill="#07121d" opacity=".45"/>
        <path d="M25 50L63 18H176L145 50Z" fill={room.color} opacity=".75"/>
        <path d="M145 50L176 18V112L145 143Z" fill={room.color} opacity=".3"/>
        <rect x="25" y="50" width="120" height="93" rx="3" fill="#203e4b" stroke={room.color} strokeWidth={focused===room.id?3:1}/>
        <rect x="36" y="59" width="98" height="17" rx="3" fill="#102632"/>
        <text x="85" y="71" textAnchor="middle" fontSize="8" fontWeight="800" fill={room.color}>{room.name}</text>
        <rect x="39" y="88" width="28" height="23" rx="2" fill={running?room.color:"#496b76"} opacity=".7"/>
        <rect x="78" y="88" width="25" height="23" rx="2" fill={running?room.color:"#496b76"} opacity=".7"/>
        <path d="M53 88V111M39 99H67M90 88V111M78 99H103" stroke="#254653"/>
        <rect x="111" y="92" width="23" height="51" rx="3" fill="#112632"/>
        <circle cx="130" cy="52" r="7" fill={running?"#fbbf24":complete?"#6ee7b7":"#526876"}>{running&&<animate attributeName="opacity" values="1;.35;1" dur="1.5s" repeatCount="indefinite"/>}</circle>
        <g transform="translate(80 145)"><ellipse cy="15" rx="17" ry="5" fill="#06141a" opacity=".4"/><rect x="-10" y="-5" width="20" height="20" rx="5" fill={room.color}/><rect x="-13" y="-23" width="26" height="23" rx="8" fill="#eaf6ef"/><rect x="-9" y="-17" width="18" height="11" rx="4" fill="#244a50"/><circle cx="-4" cy="-12" r="1.5" fill={room.color}/><circle cx="4" cy="-12" r="1.5" fill={room.color}/></g>
        <text x="85" y="198" textAnchor="middle" fill={running?"#fcd34d":complete?"#6ee7b7":"#8ca5ae"} fontSize="9" fontWeight="700">{status}</text>
      </g>;
    })}
  </svg></div>;
}
