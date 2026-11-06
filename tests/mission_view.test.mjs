import test from 'node:test';
import assert from 'node:assert/strict';
import {activeRole,outputOf,roleStatus,subtasksOf,messagesOf,sourceForRole} from '../frontend-react/src/missionView.js';

test('avatar follows actual running subtask, including diagnostic work',()=>{
  const mission={status:'running',subtasks:[{role:'coordination',status:'completed'},{role:'inventory',tool:'workstations',status:'running'},{role:'security',status:'waiting'}]};
  assert.equal(activeRole(mission),'inventory');
  assert.equal(roleStatus(mission,'inventory'),'running');
  assert.equal(roleStatus(mission,'security'),'waiting');
});

test('failure and human review are never displayed as autonomous completion',()=>{
  assert.equal(roleStatus({status:'blocked',subtasks:[{role:'coordination',status:'blocked'}]},'security'),'blocked');
  assert.equal(roleStatus({status:'awaiting_review',subtasks:[{role:'report',status:'completed'}]},'report'),'awaiting_review');
  assert.equal(activeRole({status:'awaiting_review',subtasks:[{role:'report',status:'completed'}]}),null);
});

test('artifact lookup uses actual whitelisted references and never guesses output',()=>{
  const mission={tasks:[{output:{plan:'real'}}],diagnostics:[{workstations:[1]}]};
  assert.deepEqual(outputOf(mission,{output_ref:'tasks.0.output'}),{plan:'real'});
  assert.deepEqual(outputOf(mission,{output_ref:'diagnostics.0'}),{workstations:[1]});
  assert.equal(outputOf(mission,{output_ref:'__proto__.polluted'}),undefined);
  assert.equal(outputOf(mission,{status:'running'}),undefined);
});

test('old missions expose saved phase outputs without invented feedback',()=>{
  const mission={mission_id:'old',tasks:[{id:'security',status:'completed',output:{reports:[]}}]};
  const task=subtasksOf(mission)[0];
  assert.deepEqual(outputOf(mission,task),{reports:[]});
  assert.deepEqual(messagesOf(mission),[]);
  assert.equal(sourceForRole(mission,'security'),'Chưa có kết quả ứng phó');
});

test('policy fallback remains visible separately from coordinator model',()=>{
  const mission={tasks:[{id:'coordination',output:{model:'qwen2.5:7b'}},{id:'security',output:{reports:[{model:'policy-fallback'}]}}]};
  assert.equal(sourceForRole(mission,'coordination'),'qwen2.5:7b');
  assert.equal(sourceForRole(mission,'security'),'Quy tắc dự phòng');
});
