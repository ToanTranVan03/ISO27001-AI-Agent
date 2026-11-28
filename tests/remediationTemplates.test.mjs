import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import {remediationDraft,remediationTemplates} from '../frontend-react/src/remediationTemplates.js';

test('the 56-control catalog has exactly one actionable remediation template per control',()=>{
 const catalog=JSON.parse(readFileSync(new URL('../docs/56_controls_scope.json',import.meta.url),'utf8'));
 const ids=catalog.map(control=>control.control_id);
 assert.equal(ids.length,56);
 assert.deepEqual(Object.keys(remediationTemplates).sort(),ids.sort());
 for(const control of catalog){
  assert.ok(control.pass_criteria.length,control.control_id);
  const draft=remediationDraft(control.control_id);
  for(const field of ['title','department','steps','required_evidence','recheck_method','acceptance','tasks']){
   assert.ok(draft[field].trim(),`${control.control_id}: ${field}`);
  }
 }
});
