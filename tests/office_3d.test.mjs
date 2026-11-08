import test from 'node:test';
import assert from 'node:assert/strict';
import {employeeDestination,officeRoute,walkable,office3dSnapshot,employeeVisualState,agentSubmission} from '../frontend-react/src/office3dModel.js';

test('all 50 employees remain selectable with stable machine identity across four office sections',()=>{
  const employees=Array.from({length:50},(_,i)=>({employee_id:`EMP-${String(i+1).padStart(3,'0')}`,display_name:`Employee ${i+1}`}));
  const result=office3dSnapshot(employees,[],[],'EMP-050',null);
  assert.equal(result.page,3);assert.equal(result.pageCount,4);assert.equal(result.people.length,8);
  assert.equal(result.people.at(-1).id,'EMP-050');assert(result.people.at(-1).selected);
  assert(result.roles.every(r=>r.status==='idle'));
});

test('every desk and break destination is reachable without walking through office furniture',()=>{
  for(let i=0;i<14;i++)for(const state of [{shift:'on',location:'desk'},{shift:'on',location:'break'}]){
    const start=employeeDestination(i,{shift:'off',location:'reception'}),target=employeeDestination(i,state);
    assert(walkable(start.x,start.z));assert(walkable(target.x,target.z),JSON.stringify({i,target}));
    const route=officeRoute(start,target);assert(route.length>0);
    assert(route.every(p=>walkable(p.x,p.z)));assert(Math.hypot(route.at(-1).x-target.x,route.at(-1).z-target.z)<.6);
  }
});

test('no route is invented for an entirely blocked office',()=>{
  assert.deepEqual(officeRoute({x:0,z:0},{x:1,z:1},[{x:0,z:0,w:100,d:100}]),[]);
});

test('SOC leaves its glass office through the doorway',()=>{
  const route=officeRoute({x:3,z:-6.55},{x:-7,z:3});
  assert(route.length>0);
  const crossing=route.filter(p=>p.z>-4.7&&p.z<-4.1);
  assert(crossing.length>0);
  assert(crossing.every(p=>Math.abs(p.x-3)<.9));
});

test('pending comments never become a verified incident in the scene before backend confirmation',()=>{
  const pending={id:'EMP-006',machine:{pending_count:1,state:{shift:'on'}},receipt:{command:'/usb-la'},status:'Waiting'};
  assert.equal(employeeVisualState(pending).label,'Chờ Agent kiểm tra');
  assert.equal(employeeVisualState({...pending,machine:{pending_count:0},receipt:{incident_id:'i',verified:true}}).label,'Đã xác minh');
});

test('Agent comments keep one explicit employee target and never silently enable model fallback',()=>{
  const target={employee_id:'EMP-006',asset_id:'OFFICE-EMP-006',employee_name:'Ignored'};
  const result=agentSubmission('security','Kiểm tra USB lạ trên máy đang chọn','agent',false,target);
  assert.deepEqual(result.target,{employee_id:'EMP-006',asset_id:'OFFICE-EMP-006'});
  assert.equal(result.allow_fallback,false);assert.equal(result.requested_role,'security');
  assert.equal(agentSubmission('security',result.goal,'workflow',true,target).allow_fallback,false);
  assert.throws(()=>agentSubmission('security','USB','agent',false,target));
  assert.throws(()=>agentSubmission('security',result.goal,'agent',false,null));
});

test('role activity is taken from saved tasks, not the presence of a typed comment',()=>{
  const mission={status:'running',subtasks:[{id:'t',tool:'security',role:'security',status:'running'}]};
  const result=office3dSnapshot([],[],[],'',mission);
  assert.equal(result.roles.find(r=>r.id==='security').status,'running');
  assert.notEqual(result.roles.find(r=>r.id==='inventory').status,'running');
});
