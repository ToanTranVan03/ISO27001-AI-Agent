import test from 'node:test';
import assert from 'node:assert/strict';
import {employeeTarget,missionLiveFocus,linkedRecord,refreshLinkedRecord} from '../frontend-react/src/missionLink.js';

test('employee selection produces explicit machine target, no target before data arrives',()=>{
  assert.equal(employeeTarget({employee_id:'EMP-006'},null),null);
  assert.deepEqual(employeeTarget({employee_id:'EMP-006',display_name:'Name'},{asset_id:'OFFICE-EMP-006'},'event'),{employee_id:'EMP-006',employee_name:'Name',asset_id:'OFFICE-EMP-006',event_id:'event'});
});

test('mission SOC and automatic monitor share explicit focus while historical result never animates as running',()=>{
  const activity={employee_id:'EMP-006',asset_id:'OFFICE-EMP-006',event_id:'event',state:'processing',active:true};
  assert.equal(missionLiveFocus({status:'running',current_activity:activity},null).source,'mission');
  assert.equal(missionLiveFocus({status:'awaiting_review',current_activity:activity},null),null);
  assert.equal(missionLiveFocus({status:'running',current_activity:{...activity,active:false}},null),null);
  const monitor={state:'processing',current_finding:activity};
  assert.equal(missionLiveFocus(null,monitor).source,'monitor');
});

test('incident navigation preserves event, asset and employee references',()=>{
  const finding={employee_id:'EMP-006',asset_id:'OFFICE-EMP-006',event_id:'event'};
  const record=linkedRecord({incident_id:'case',event_id:'event'},[finding]);
  assert.equal(record.employee_id,'EMP-006');assert.equal(record.asset_id,'OFFICE-EMP-006');assert.equal(record.incident_id,'case');
});

test('live selection gains final incident without switching to a different event',()=>{
  const selected={employee_id:'EMP-006',asset_id:'OFFICE-EMP-006',event_id:'chosen'};
  const wrong={...selected,event_id:'other',incident_id:'wrong-case'};
  const result={...selected,incident_id:'right-case',verified:true};
  const mission={tasks:[{id:'security',output:{reports:[wrong,result]}}]};
  assert.equal(refreshLinkedRecord(selected,[wrong],[mission]).incident_id,'right-case');
  assert.equal(refreshLinkedRecord(selected,[wrong],[]).incident_id,undefined);
});
