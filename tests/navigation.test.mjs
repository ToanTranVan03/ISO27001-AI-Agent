import test from 'node:test';
import assert from 'node:assert/strict';
import {readNavigation,navigationHash,mergeNavigation,sourceRunIds,controlReferencesEmployee,controlRunIds} from '../frontend-react/src/navigation.js';
const run='00000000-0000-0000-0000-000000000012';
test('context survives round trip without token, payload or arbitrary fields',()=>{
 const n={view:'a8',controlId:'A.8.13',employeeId:'EMP-001',runId:run,assessmentId:run};
 assert.deepEqual(readNavigation(navigationHash({...n,token:'secret'})),n);
 assert.ok(!navigationHash({...n,token:'secret'}).includes('secret'));
 assert.equal(readNavigation('#view=other&control=A.8.99&run=../../private&employee=bad').view,'scope56');
 assert.equal(readNavigation('#control=A.8.99').controlId,'');
});
test('navigation preserves context except explicitly cleared fields',()=>{
 const n=readNavigation(navigationHash({controlId:'A.6.1',employeeId:'EMP-001',runId:run}));
 assert.equal(mergeNavigation(n,{view:'dossier'}).employeeId,'EMP-001');
 assert.equal(mergeNavigation(n,{runId:'',controlId:''}).controlId,'');
 assert.equal(mergeNavigation(n,{employeeId:undefined}).employeeId,'EMP-001');
});
test('source links and employee scope use explicit evidence references only',()=>{
 const c={control_id:'A.8.13',evidence:[{source:`a8-capture://${run}/A.8.13`,entity_refs:{employees:['EMP-001']}},{source:`a8-capture://${run}/A.8.13`},{source:`a8-capture://${run}/A.8.1`}]};
 assert.deepEqual(sourceRunIds(c),[run]);
 assert.deepEqual(controlRunIds({...c,experiment_results:[{run_id:run},{run_id:'../../bad'}]}),[run]);
 assert.equal(controlReferencesEmployee(c,'EMP-001'),true);
 assert.equal(controlReferencesEmployee(c,'EMP-002'),false);
 assert.equal(controlReferencesEmployee({evidence:[]},'EMP-001'),false);
});

test('finding links survive page changes and clear on scope changes',()=>{
 const finding='00000000-0000-0000-0000-000000000034';
 const n=readNavigation(navigationHash({controlId:'A.8.8',assessmentId:run,findingId:finding}));
 assert.equal(n.findingId,finding);
 assert.equal(mergeNavigation(n,{view:'company'}).findingId,finding);
 assert.equal(mergeNavigation(n,{controlId:'A.8.5'}).findingId,undefined);
 assert.equal(mergeNavigation(n,{assessmentId:finding}).findingId,undefined);
 assert.equal(readNavigation('#finding=../../private').findingId,undefined);
});
