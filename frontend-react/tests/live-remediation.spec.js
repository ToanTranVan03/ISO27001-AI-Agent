import {test,expect} from '@playwright/test';
import {randomUUID} from 'node:crypto';
test.use({baseURL:process.env.UI_BASE_URL});
test.setTimeout(360000);

test('real remediation: approve, assign, evidence, reject, recheck, verify, preserve and export',async({request})=>{
 test.skip(process.env.ISO_ISOLATED_TEST!=='1'||!/^iso_acceptance_[a-f0-9]{12}$/.test(process.env.ISO_ISOLATED_DBNAME||''),'Disposable database required');
 const login=async(user,password)=>{const r=await request.post('/api/auth/login',{data:{username:user,password}});expect(r.status()).toBe(200);return (await r.json()).access_token;};
 const admin=await login('release_admin',process.env.INITIAL_ADMIN_PASSWORD);
 const call=async(method,url,body,token=admin,expected=200)=>{
  const r=await request.fetch(url,{method,headers:{Authorization:`Bearer ${token}`},data:body,timeout:240000});
  expect(r.status(),await r.text()).toBe(expected);return r.json();
 };
 const aid=(await call('GET','/api/assessments'))[0].assessment_id,base=`/api/assessments/${aid}`;
 const scopePath=base+'/enterprise/scope56',path=base+'/remediation';
 const person=await call('POST','/api/team/users',{username:'remediation_operator',display_name:'SYNTHETIC enterprise operator',password:process.env.ISO_ASSESSOR_PASSWORD},admin,201);
 const operator=await login('remediation_operator',process.env.ISO_ASSESSOR_PASSWORD);
 const helperPerson=await call('POST','/api/team/users',{username:'remediation_helper',display_name:'SYNTHETIC collaborator',password:process.env.ISO_ASSESSOR_PASSWORD},admin,201);
 const helper=await login('remediation_helper',process.env.ISO_ASSESSOR_PASSWORD);
 await call('PUT',path+'/roles',{user_id:person.user_id,role:'operator'});
 await call('PUT',path+'/roles',{user_id:helperPerson.user_id,role:'operator'});
 await call('GET',`/api/assessments/${randomUUID()}/remediation`,undefined,operator,403);
 await call('PUT',path+'/context',{expected_version:0,name:'SYNTHETIC acceptance company',sector:'Software test only',isms_scope:'Disposable test records for one isolated service',locations:'Test location',departments:'Test IT',assets_systems:'Test file system',obligations:'Not assessed; synthetic test only',risks:'Unverified sample risk',contact:'Synthetic test owner'});
 await call('PUT',path+'/context',{expected_version:0,name:'test',sector:'test',isms_scope:'Stale edit should fail',locations:'',departments:'',assets_systems:'',obligations:'',risks:'',contact:''},admin,409);
 const c=(await call('GET',scopePath)).controls.find(c=>c.control_id==='A.6.1');
 let record=await call('POST',path+'/findings',{control_id:c.control_id,expected_review_token:c.review_token,description:'SYNTHETIC test: recorded HR evidence needs further verification',location:'Test HR service',root_cause:'Unconfirmed, requires investigation',risk:'unconfirmed'},admin,201);
 const originalBaseline=structuredClone(record.document.baseline),rid=record.record_id;
 const action={title:'Obtain and verify a synthetic HR record',steps:'Request responsible owner records, inspect scope, upload and independently review.',acceptance:'Reviewer inspects each criterion and cites the new test artifact',department:'Test HR',resources:'Test owner and isolated record',tasks:['Collect test records','Review and submit test records']};
 await call('POST',path+`/findings/${rid}/actions`,{...action,expected_version:record.version},operator,403);
 record=await call('POST',path+`/findings/${rid}/actions`,{...action,expected_version:record.version});
 const act=record.document.actions[0].action_id;
 const event=async(command,payload={},token=admin,expected=200)=>{
  const value=await call('POST',path+`/findings/${rid}/actions/${act}/events`,{command,expected_version:record.version,note:'SYNTHETIC acceptance test, not professional verification',...payload},token,expected);
  if(expected===200)record=value;return value;
 };
 await event('approve',{assignee:person.user_id,collaborator_ids:[person.user_id],due_date:'2099-12-31'},admin,422);
 await event('approve',{assignee:person.user_id,collaborator_ids:[helperPerson.user_id],due_date:'2099-12-31'});
 expect((await call('GET',path,undefined,helper)).records.some(r=>r.record_id===rid)).toBe(true);
 await event('start',{},helper);
 await event('submit',{},helper,403);
 await event('submit',{},operator,409);
 for(const task of record.document.actions[0].tasks)await event('task',{task_id:task.task_id,done:true},operator);
 const upload=await request.post(scopePath+'/controls/A.6.1/sources/upload',{headers:{Authorization:`Bearer ${operator}`},multipart:{evidence_type:c.expected_evidence_types[0],origin:'SYNTHETIC remediation test source',file:{name:'after-remediation.txt',mimeType:'text/plain',buffer:Buffer.from('Synthetic AFTER remediation record for software acceptance only. No real HR claims or signatures.')}}});
 expect(upload.status()).toBe(201);const eid=(await upload.json()).evidence_id;
 await event('attach',{evidence_id:eid},operator);
 await event('submit',{},operator);
 await event('verify',{outcome:'accepted'},operator,403);
 await event('verify',{outcome:'accepted'},admin,409);
 await event('verify',{outcome:'partial'});
 expect(record.document.actions[0].state).toBe('REWORK');
 await event('submit',{},operator);
 const current=(await call('GET',scopePath)).controls.find(c=>c.control_id==='A.6.1');
 await call('POST',scopePath+'/reviews',{control_id:current.control_id,review_token:current.review_token,conclusion:'Insufficient Evidence',rationale:'Synthetic operator should not sign a technical review.',evidence_ids:[],criteria_reviews:current.pass_criteria.map((_,i)=>({criterion_index:i,verdict:'unknown',rationale:'Synthetic role rejection test only.',evidence_ids:[]}))},operator,403);
 await call('POST',scopePath+'/reviews',{control_id:current.control_id,review_token:current.review_token,conclusion:'Compliant',rationale:'SYNTHETIC test confirms validator wiring only; not an actual human assessment.',evidence_ids:[eid],criteria_reviews:current.pass_criteria.map((_,i)=>({criterion_index:i,verdict:'met',rationale:'Synthetic fixture satisfies this test criterion only, not an actual audit judgment.',evidence_ids:[eid]}))});
 await event('verify',{outcome:'accepted'});
 await event('close');
 expect(record.document.baseline).toEqual(originalBaseline);
 expect(record.document.actions[0].state).toBe('CLOSED');
 const report=await call('GET',path+'/report');expect(report.certification_claim).toBe(false);
 expect(report.records.find(r=>r.record_id===rid).document.baseline).toEqual(originalBaseline);
 for(const extension of ['csv','html']){
  const exported=await request.get(path+'/report.'+extension,{headers:{Authorization:`Bearer ${admin}`}});
  expect(exported.status()).toBe(200);expect(await exported.text()).toContain('A.6.1');
  expect(exported.headers()['content-type']).toContain(extension==='csv'?'text/csv':'text/html');
 }
 for(const [extension,signature,mime] of [['xlsx','PK','application/vnd.openxmlformats'],['pdf','%PDF','application/pdf']]){
  const exported=await request.get(path+'/report.'+extension,{headers:{Authorization:`Bearer ${admin}`}});
  expect(exported.status()).toBe(200);expect((await exported.body()).subarray(0,signature.length).toString()).toBe(signature);
  expect(exported.headers()['content-type']).toContain(mime);
 }
 // Exercise real configured model, not a rule/template replacement, on another frozen finding.
 const newControl=(await call('GET',scopePath)).controls.find(c=>c.control_id==='A.6.1');
 const aiCase=await call('POST',path+'/findings',{control_id:'A.6.1',expected_review_token:newControl.review_token,description:'SYNTHETIC test: review future record retention workflow',location:'Test HR',root_cause:'Not confirmed, requires review',risk:'unconfirmed'},admin,201);
 const ai=await call('POST',path+`/findings/${aiCase.record_id}/ai-proposal`,{expected_version:1});
 expect(ai.document.actions[0].proposal_origin).toBe('OLLAMA_DRAFT_REQUIRES_REVIEW');
 expect(ai.document.actions[0].state).toBe('PENDING_APPROVAL');
 const hidden=await call('GET',path,undefined,operator);expect(hidden.records.some(r=>r.record_id===aiCase.record_id)).toBe(false);
 await call('POST','/api/auth/logout',undefined,operator);
 const again=await login('remediation_operator',process.env.ISO_ASSESSOR_PASSWORD);
 const persisted=await call('GET',path,undefined,again);
 expect(persisted.records.find(r=>r.record_id===rid).document.actions[0].state).toBe('CLOSED');
 await call('POST','/api/auth/logout',undefined,again);await call('POST','/api/auth/logout');
});
