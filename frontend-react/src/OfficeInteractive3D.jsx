import { useEffect, useMemo, useRef, useState } from 'react';
import { RotateCcw, Move, ScanLine, Users, ArrowUpRight, Bot } from 'lucide-react';
import { office3dSnapshot, employeeVisualState } from './office3dModel';
import './office-interactive-3d.css';

export default function OfficeInteractive3D({employees,workspace,entries,selectedEmployee,onSelect,monitoring,liveFocus,
  mission,selectedRole,onSelectRole,onSuggest,linkedRecord,onOpenIncident,onFallback}) {
  const host=useRef(null),engine=useRef(null),latest=useRef(null);
  const [ready,setReady]=useState(false),[error,setError]=useState(''),[camera,setCamera]=useState('iso');
  const snapshot=useMemo(()=>office3dSnapshot(employees,workspace,entries,selectedEmployee,mission),[employees,workspace,entries,selectedEmployee,mission]);
  const current=snapshot.people.find(p=>p.id===selectedEmployee);
  const shortcuts=[
    {text:current?.machine?.state.shift==='on'?'làm việc':'đi làm',command:current?.machine?.state.shift==='on'?'/lam-viec':'/di-lam'},
    {text:'nghỉ',command:'/nghi'},{text:'cắm USB lạ',command:'/usb-la'},{text:'rời máy không khóa',command:'/roi-may'},
  ];
  useEffect(()=>{
    latest.current={snapshot,selectedEmployee,selectedRole,monitoring,liveFocus,onSelect,onSelectRole};
    engine.current?.update(latest.current);
  },[snapshot,selectedEmployee,selectedRole,monitoring,liveFocus,onSelect,onSelectRole]);
  useEffect(()=>{
    let cancelled=false;
    import('./office3dEngine').then(({createOffice3D})=>{
      if(cancelled)return;
      try {engine.current=createOffice3D(host.current,latest.current,{onPick:pick=>{
        if(pick.employeeId)latest.current.onSelect(pick.employeeId);
        if(pick.roleId)latest.current.onSelectRole(pick.roleId);
      },onError:setError});setReady(true);}catch(e){setError(`Không khởi tạo được 3D: ${e.message}`);}
    }).catch(e=>{if(!cancelled)setError(e.message);});
    return()=>{cancelled=true;engine.current?.dispose();engine.current=null;};
  },[]);
  useEffect(()=>{if(ready)engine.current?.setCamera(camera);},[camera,ready]);
  const focusOffPage=liveFocus?.employee_id&&!snapshot.people.some(p=>p.id===liveFocus.employee_id);
  return <section className="oi3d" aria-label="Văn phòng tương tác 3D">
    <header className="oi3d-head"><div><span className="oi3d-eyebrow">VIỆT TÍN · AGENT OFFICE</span><h2>Một văn phòng. Những công việc thật.</h2><p>Chọn nhân viên để bình luận lệnh · Chọn phòng Agent để giao mục tiêu</p></div><span className={`oi3d-live ${liveFocus?.active?'is-working':''}`}><i/>{liveFocus?.active?'SOC ĐANG XỬ LÝ':monitoring.active?'ĐANG GIÁM SÁT':'SẴN SÀNG'}</span></header>
    <div className="oi3d-toolbar"><div className="oi3d-pages">{Array.from({length:snapshot.pageCount},(_,i)=><button key={i} aria-pressed={snapshot.page===i} onClick={()=>onSelect(snapshot.all[i*14].employee_id)}>Khu {i+1}<small>{snapshot.all.slice(i*14,(i+1)*14).length} người</small></button>)}</div><div className="oi3d-cameras"><button onClick={()=>{setCamera('iso');engine.current?.setCamera('iso');}} title="Góc nhìn ban đầu"><RotateCcw size={14}/>Toàn cảnh</button><button aria-pressed={camera==='top'} onClick={()=>setCamera('top')}>Từ trên</button><button aria-pressed={camera==='follow'} onClick={()=>setCamera('follow')}>Theo nhân viên</button></div></div>
    <div className="oi3d-role-tabs" aria-label="Chọn phòng Agent">{snapshot.roles.map(role=><button key={role.id} aria-pressed={selectedRole===role.id} onClick={()=>onSelectRole(role.id)} style={{'--role-color':role.color}}><Bot size={13}/>{role.title}<span className={role.status==='running'?'is-running':''}/></button>)}</div>
    <div className="oi3d-stage"><div ref={host} className="oi3d-canvas"/>{!ready&&!error&&<div className="oi3d-loading">Đang dựng văn phòng 3D…</div>}{error&&<div className="oi3d-loading" role="alert"><p>{error}</p><button onClick={onFallback}>Mở sơ đồ 2D để tiếp tục</button></div>}<div className="oi3d-hint"><Move size={13}/>Kéo để xoay · Cuộn để phóng to · Bấm nhân vật hoặc bàn</div><div className="oi3d-stage-count"><Users size={13}/>{snapshot.total} nhân viên · {workspace.length} máy riêng</div></div>
    <div className="oi3d-focus"><ScanLine size={17}/><p>{liveFocus?.text||(monitoring.active?'Agent theo dõi nhật ký; chỉ xử lý khi có dấu hiệu mới.':'Gửi bình luận cho nhân viên sẽ bật giám sát tự động.')}<small>Hoạt động và xác minh lấy từ backend. Nhân vật di chuyển để thể hiện trạng thái đã ghi nhận.</small></p>{focusOffPage&&<button onClick={()=>onSelect(liveFocus.employee_id)}>Theo dõi {liveFocus.employee_id}<ArrowUpRight size={14}/></button>}</div>
    <div className="oi3d-roster" aria-label="Nhân viên trong khu, hỗ trợ bàn phím">{snapshot.people.map(person=><button key={person.id} aria-pressed={!selectedRole&&person.selected} onClick={()=>onSelect(person.id)}><span style={{background:employeeVisualState(person).color}}/><b>{person.id}</b><small>{person.status}</small></button>)}</div>
    {current&&<div className="oi3d-selected"><div><span>NHÂN VIÊN ĐANG CHỌN</span><h3>{current.name}</h3><p>{current.id} · {current.machine?.asset_id||'Đang đồng bộ máy'} · {current.status}</p></div><div className="oi3d-shortcuts">{shortcuts.map(({text,command})=>{const action=current.machine?.actions?.find(a=>a.command===command);const enabled=action?(action.prepared_enabled??action.enabled):Boolean(current.machine);return <button key={text} disabled={!enabled} title={enabled?'Điền bình luận để gửi':action?.prepared_reason||action?.reason||'Chờ đồng bộ máy'} onClick={()=>{onSelectRole(null);onSuggest(text);}}>Điền “{text}”</button>;})}<button className="oi3d-primary" onClick={()=>onSelectRole('security')}>Giao SOC kiểm tra</button></div></div>}
    {linkedRecord?.employee_id===selectedEmployee&&<div className="oi3d-linked"><b>Hồ sơ liên kết · {linkedRecord.asset_id}</b><span>{linkedRecord.event_id||'Đang đối chiếu sự kiện'}</span>{linkedRecord.incident_id&&<button onClick={()=>onOpenIncident(linkedRecord)}>Mở hồ sơ sự cố ↗</button>}</div>}
    <footer className="oi3d-note">Doanh nghiệp giả lập · Bốn vai trò dùng chung hệ thống điều phối · Giao việc → thực thi → bằng chứng → người duyệt</footer>
  </section>;
}
