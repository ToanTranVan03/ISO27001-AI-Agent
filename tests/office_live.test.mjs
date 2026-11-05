import test from 'node:test';
import assert from 'node:assert/strict';
import {commandPhase, employeePhase, commandRecipient, latestByEmployee, employeePosition} from '../frontend-react/src/officeLive.js';

test('pending command is never presented as detected before evidence is linked', () => {
  assert.equal(commandPhase({event_type:'unattended_screen_unlocked'}), 'pending');
  assert.equal(commandPhase({event_type:'unattended_screen_unlocked',incident_id:'case',verified:false}), 'review');
  assert.equal(commandPhase({incident_id:'case',verified:true}), 'resolved');
  for(const type of ['approved_work_session','employee_shift_started','approved_break_started','screen_locked_by_employee']) {
    assert.equal(commandPhase({event_type:type}), 'routine');
  }
});
test('latest command wins by event time, not array order', () => {
  const older={employee_id:'EMP-006',observed_at:'2026-11-05T09:00:00Z',command:'/nghi'};
  const newer={...older,observed_at:'2026-11-05T09:01:00Z',command:'/lam-viec'};
  assert.equal(latestByEmployee([older,newer])['EMP-006'].command,'/lam-viec');
  assert.equal(latestByEmployee([newer,older])['EMP-006'].command,'/lam-viec');
});

test('persisted state overrides animation and retains unresolved risk', () => {
  assert.deepEqual(employeePosition(0,{command:'/lam-viec'},{location:'break'}),employeePosition(0,{command:'/nghi'}));
  assert.equal(employeePhase({event_type:'approved_work_session'},{pending_count:1,state:{}}),'pending');
  assert.equal(employeePhase({incident_id:'old',verified:true},{pending_count:0,state:{software_status:'unapproved'}}),'review');
});
test('explicit recipient is extracted only at start of comment', () => {
  assert.equal(commandRecipient('@emp-025 /cai-app-la','EMP-006'),'EMP-025');
  assert.equal(commandRecipient('/lam-viec','EMP-006'),'EMP-006');
  assert.equal(commandRecipient('hello @EMP-025','EMP-006'),'EMP-006');
});
test('break moves an employee to lounge and work returns to their own desk', () => {
  for(let i=0;i<14;i++) {
    const desk=employeePosition(i,{command:'/lam-viec'});
    const lounge=employeePosition(i,{command:'/nghi'});
    assert.ok(desk[0]<615 && desk[1]<545);
    assert.ok(lounge[0]>645 && lounge[0]<961 && lounge[1]<610);
    assert.deepEqual(employeePosition(i,{command:'/vao-ca'}),desk);
  }
});
