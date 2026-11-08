import { employeePhase, employeeStatus, latestByEmployee } from './officeLive.js';
import { roleStatus, subtasksOf } from './missionView.js';

export const OFFICE_ROLES = [
  {id:'coordination',title:'ĐIỀU PHỐI',color:'#439bac',x:-9},
  {id:'inventory',title:'TÀI SẢN & NHÂN SỰ',color:'#c79a54',x:-3},
  {id:'security',title:'SOC · GIÁM SÁT',color:'#8c79bd',x:3},
  {id:'report',title:'KIỂM SOÁT NỘI BỘ',color:'#4a987e',x:9},
];
export const DESKS=Array.from({length:14},(_,i)=>({x:-11+(i%4)*3.65,z:-1.8+Math.floor(i/4)*2.65}));
export const NAV_OBSTACLES = [
  ...DESKS.map(d=>({x:d.x,z:d.z,w:2.7,d:1.25})),
  ...OFFICE_ROLES.flatMap(r=>[{x:r.x-2.8,z:-7,w:.14,d:5.3},{x:r.x+2.8,z:-7,w:.14,d:5.3},
    {x:r.x,z:-9.6,w:5.6,d:.14},{x:r.x,z:-7.6,w:2.4,d:1.15},
    {x:r.x-1.95,z:-4.42,w:1.7,d:.07},{x:r.x+1.95,z:-4.42,w:1.7,d:.07}]),
  {x:8.5,z:1.5,w:5,d:1.4},{x:8.5,z:5.1,w:3.1,d:1.8},
  {x:8.5,z:3.2,w:1.5,d:1.5},
  {x:-9.7,z:9.65,w:4.3,d:1.1},
];

export function employeeDestination(index,state={}) {
  if(state.shift==='off'||state.location==='reception')return {x:-5.8+(index%7)*2.65,z:9.45+Math.floor(index/7)*1.15};
  if(state.location==='break')return {x:[5.6,6.8,10.2,11.5][index%4],z:[3,3.8,6.8,7.6][Math.floor(index/4)]};
  return {x:DESKS[index].x,z:DESKS[index].z+1.02};
}

export function office3dSnapshot(employees,workspace,entries,selectedEmployee,mission) {
  const all=[...employees].sort((a,b)=>a.employee_id.localeCompare(b.employee_id));
  const page=Math.floor(Math.max(0,all.findIndex(p=>p.employee_id===selectedEmployee))/14);
  const machines=Object.fromEntries(workspace.map(m=>[m.employee_id,m]));
  const latest=latestByEmployee(entries);
  const people=all.slice(page*14,(page+1)*14).map((person,index)=>{
    const machine=machines[person.employee_id];
    const receipt=machine?.state.last_receipt||latest[person.employee_id];
    return {id:person.employee_id,name:person.display_name,index,person,machine,receipt,
      phase:employeePhase(receipt,machine),status:employeeStatus(machine),
      destination:employeeDestination(index,machine?.state),selected:person.employee_id===selectedEmployee};
  });
  const roles=OFFICE_ROLES.map(role=>({...role,status:roleStatus(mission,role.id),
    tasks:subtasksOf(mission).filter(t=>t.role===role.id)}));
  return {page,total:all.length,pageCount:Math.ceil(all.length/14),all,people,roles};
}

// Shared grid navigation: employees cannot walk through desks, glass walls or sofas.
export function walkable(x,z,obstacles=NAV_OBSTACLES) {
  return x>=-13.4&&x<=13.4&&z>=-9.8&&z<=11.1&&!obstacles.some(o=>
    Math.abs(x-o.x)<o.w/2+.22&&Math.abs(z-o.z)<o.d/2+.22);
}

export function officeRoute(start,end,obstacles=NAV_OBSTACLES) {
  const step=.35,cols=77,rows=61;
  const point=(x,z)=>({x:-13.3+x*step,z:-9.8+z*step});
  function nearest(p){
    const cx=Math.round((p.x+13.3)/step),cz=Math.round((p.z+9.8)/step);
    let best=null,dist=Infinity;
    for(let r=0;r<=5;r++)for(let dx=-r;dx<=r;dx++)for(let dz=-r;dz<=r;dz++){
      const x=cx+dx,z=cz+dz,q=point(x,z),d=Math.hypot(q.x-p.x,q.z-p.z);
      if(x>=0&&x<cols&&z>=0&&z<rows&&d<dist&&walkable(q.x,q.z,obstacles)){best=[x,z];dist=d;}
    }
    return best;
  }
  const from=nearest(start),to=nearest(end);
  if(!from||!to)return [];
  const key=(x,z)=>z*cols+x;
  const origin=key(...from),goal=key(...to),queue=[from],parents=new Map([[origin,null]]);
  for(let head=0;head<queue.length;head++){
    const [x,z]=queue[head],id=key(x,z);
    if(id===goal){
      const route=[];let current=id;
      while(current!==null){route.push(point(current%cols,Math.floor(current/cols)));current=parents.get(current);}
      return route.reverse();
    }
    for(const [dx,dz] of [[1,0],[-1,0],[0,1],[0,-1]]){
      const nx=x+dx,nz=z+dz,nid=key(nx,nz),q=point(nx,nz);
      if(nx<0||nx>=cols||nz<0||nz>=rows||parents.has(nid)||!walkable(q.x,q.z,obstacles))continue;
      parents.set(nid,id);queue.push([nx,nz]);
    }
  }
  return [];
}

export function employeeVisualState(record) {
  if(record.machine?.pending_count>0)return {label:'Chờ Agent kiểm tra',color:'#d59a42'};
  if(record.receipt?.incident_id)return record.receipt.verified?
    {label:'Đã xác minh',color:'#459c7e'}:{label:'Cần kiểm tra hồ sơ',color:'#cc695e'};
  if(record.phase==='review')return {label:'Máy cần kiểm tra',color:'#cc695e'};
  return {label:record.status,color:record.machine?.state.shift==='on'?'#4f9b87':'#9ba8a3'};
}

export function agentSubmission(role,goal,mode,allowFallback,target) {
  if(!OFFICE_ROLES.some(r=>r.id===role))throw new Error('Chọn vai trò Agent hợp lệ.');
  const text=goal.trim();
  if(text.length<8||text.length>600)throw new Error('Mục tiêu cần từ 8 đến 600 ký tự.');
  if(!['agent','workflow'].includes(mode))throw new Error('Chọn chế độ thực thi hợp lệ.');
  if(!target?.employee_id||!target?.asset_id)throw new Error('Chọn nhân viên và máy đã đồng bộ trước khi giao việc.');
  return {goal:text,scope:'all',mode,allow_fallback:mode==='agent'&&Boolean(allowFallback),requested_role:role,
    target:{employee_id:target.employee_id,asset_id:target.asset_id}};
}
