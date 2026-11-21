import {test,expect} from '@playwright/test';
import {readFileSync,writeFileSync} from 'node:fs';
const enabled=process.env.ISO_ISOLATED_TEST==='1'&&/^iso_acceptance_[a-f0-9]{12}$/.test(process.env.ISO_ISOLATED_DBNAME||'')&&!!process.env.ISO_ISOLATED_CANDIDATE_PATH;
test.use({baseURL:process.env.UI_BASE_URL,channel:'msedge',headless:true,actionTimeout:15000});
const candidateEngine=process.env.ISO_ISOLATED_CANDIDATE_ENGINE||'rules';
test.setTimeout(candidateEngine==='llm'?750000:240000);

test('real isolated orchestration: Ollama batch stop/resume and sealed candidate worker',async({page})=>{
 test.skip(!enabled,'Requires --extended on the disposable database runner');
 await page.goto('/');await page.getByLabel('Tên đăng nhập').fill('release_admin');
 await page.getByLabel('Mật khẩu').fill(process.env.INITIAL_ADMIN_PASSWORD);
 await page.getByRole('button',{name:'ĐĂNG NHẬP HỆ THỐNG'}).click();
 await expect(page.getByRole('heading',{name:'Tổng quan đánh giá tuân thủ',exact:true})).toBeVisible();
 const {token,aid}=await page.evaluate(()=>({token:sessionStorage.getItem('iso_team_token'),aid:sessionStorage.getItem('iso_team_assessment')}));
 const headers={Authorization:`Bearer ${token}`},base=`/api/assessments/${aid}`,batchBase=base+'/enterprise/shared-work/batches';
 const json=async(method,url,data)=>{const r=await page.request.fetch(url,{method,headers,...(data===undefined?{}:{data})});expect(r.ok(),`${method} ${url}: ${await r.text()}`).toBeTruthy();return r.json();};
 try{
  // Genuine requests/storage/model, but deliberately artificial source contents.
  const scope=await json('GET',base+'/enterprise/scope56');
  for(const cid of ['A.6.1','A.6.2']){
   const c=scope.controls.find(c=>c.control_id===cid);
   const uploaded=await page.request.post(`${base}/enterprise/scope56/controls/${cid}/sources/upload`,{headers,multipart:{
    evidence_type:c.expected_evidence_types[0],origin:'SYNTHETIC orchestration regression only, not human evidence',
    file:{name:`synthetic-orchestration-${cid}.txt`,mimeType:'text/plain',buffer:Buffer.from(
     `SYNTHETIC TEST ONLY ${cid}. This isolated test record lists LAB-EMP-TEST-001 and LAB-EMP-TEST-002. `+
     'The personnel register identifies two simulated positions. Screening checks and signed employment terms have not been supplied. '+
     'This is a transport/workflow regression fixture; it does not certify completion, authorization or compliance. '+
     'The reviewer needs original records for each criterion, including dates, signatures and scope. No real employee assessment is asserted.')}}});
   expect(uploaded.status()).toBe(201);
  }
  await page.getByRole('button',{name:'Hồ sơ ISO',exact:true}).click();
  await page.getByLabel('Giới hạn control mỗi lượt').selectOption('4');
  await page.getByLabel('Đánh giá lại cả nguồn hiện hành').check();
  const started=page.waitForResponse(r=>new URL(r.url()).pathname===batchBase&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Bắt đầu lượt',exact:true}).click();
  const batch=await (await started).json();expect(batch.action).toBe('started');
  const duplicate=await json('POST',batchBase,{limit:4,force:true});
  expect(duplicate.action).toBe('following');expect(duplicate.batch_id).toBe(batch.batch_id);
  await page.getByRole('button',{name:'Dừng sau việc hiện tại',exact:true}).click();
  await page.reload();await expect(page.getByRole('heading',{name:'Agent đánh giá theo lô trên server',exact:true})).toBeVisible();
  const findBatch=async id=>(await json('GET',batchBase)).items.find(b=>b.batch_id===id);
  let stopped;
  await expect.poll(async()=>{stopped=await findBatch(batch.batch_id);return stopped.status;},{timeout:100000}).toBe('STOPPED');
  expect(stopped.results.length).toBeLessThan(stopped.plan.length);
  expect(stopped.results.every(r=>r.status==='SUCCEEDED')).toBe(true);
  await expect(page.getByRole('button',{name:'Bắt đầu lượt',exact:true})).toBeEnabled({timeout:10000});
  // Resume by starting a NEW bounded pass. The stopped pass remains immutable.
  const resumedResponse=page.waitForResponse(r=>new URL(r.url()).pathname===batchBase&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Bắt đầu lượt',exact:true}).click();
  const resumed=await (await resumedResponse).json();expect(resumed.batch_id).not.toBe(batch.batch_id);
  let completed;
  await expect.poll(async()=>{completed=await findBatch(resumed.batch_id);return completed.status;},{timeout:140000}).toBe('COMPLETED');
  expect(completed.results.length).toBe(completed.plan.length);
  expect(completed.results.every(r=>r.status==='SUCCEEDED')).toBe(true);
  expect(await findBatch(batch.batch_id)).toMatchObject({status:'STOPPED',results:stopped.results});
  const after=await json('GET',base+'/enterprise/scope56');
  for(const cid of new Set([...stopped.results,...completed.results].map(r=>r.control_id))){
   const c=after.controls.find(c=>c.control_id===cid);
   expect(c.history.some(h=>h.audit_trail.some(v=>v.startsWith('MODEL_INPUT_BYTES'))&&h.audit_trail.includes('EVALUATE'))).toBe(true);
  }
  expect(after.soa.approval).toBe('DRAFT_NOT_APPROVED');
  const plan=JSON.parse(readFileSync(process.env.ISO_ISOLATED_CANDIDATE_PATH,'utf8'));
  await page.getByRole('button',{name:'Thực nghiệm A.8',exact:true}).click();
  await page.getByRole('combobox',{name:'Engine',exact:true}).selectOption(candidateEngine);
  await page.getByText('Tổng hợp nghiên cứu & nhập gói nguồn kiểm định',{exact:true}).click();
  await page.getByText('Nhập gói nguồn ứng viên đã chốt · admin',{exact:true}).click();
  await page.getByLabel('Gói ứng viên JSON đã chốt').setInputFiles(process.env.ISO_ISOLATED_CANDIDATE_PATH);
  const beforeRuns=await json('GET',base+'/a8/runs');
  await page.getByRole('button',{name:'Kiểm tra gói, chưa chạy model',exact:true}).click();
  await expect(page.getByRole('region',{name:'Phiếu kiểm tra gói ứng viên'})).toContainText(plan.sha256);
  expect((await json('GET',base+'/a8/runs')).length).toBe(beforeRuns.length);
  const createdResponse=page.waitForResponse(r=>new URL(r.url()).pathname===base+'/a8/candidate-runs'&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Nhập và chạy gói ứng viên',exact:true}).click();
  const created=await (await createdResponse).json();expect(created.candidate_source).toBe(true);
  await expect(page.getByLabel('Mở lượt đánh giá đã lưu')).toHaveValue(created.run_id);
  let result;
  await expect.poll(async()=>{result=await json('GET',base+'/a8/runs/'+created.run_id);return result.state;},{timeout:candidateEngine==='llm'?600000:30000}).toBe('finished');
  expect(result.report.capture_sha256).toBe(plan.snapshot.sha256);
  expect(result.report.records).toHaveLength(18);expect(result.report.mode).toBe(candidateEngine);
  if(candidateEngine==='rules')expect(result.report.records.every(r=>!r.error)).toBe(true);
  else{
   expect(result.report.records.some(r=>r.execution_source==='ollama-a8-evidence-judgment')).toBe(true);
   expect(result.report.records.every(r=>r.attempts.length>=1&&r.attempts.length<=2)).toBe(true);
   expect(result.report.records.every(r=>r.execution_source!=='a8-lab-rules')).toBe(true);
  }
  expect(result.independent_validation).toBe(false);expect(result.designer_reference||[]).toEqual([]);
  await page.reload();await expect(page.getByLabel('Mở lượt đánh giá đã lưu')).toHaveValue(created.run_id);
  // Separate test identities read the same frozen pack; no human labels invented.
  const raters=[];
  for(const username of ['release_rater1','release_rater2']){
   const login=await page.request.post('/api/auth/login',{data:{username,password:process.env.ISO_ASSESSOR_PASSWORD}});
   expect(login.ok()).toBe(true);const memberHeaders={Authorization:`Bearer ${(await login.json()).access_token}`};
   try{
    const response=await page.request.get(base+'/a8/runs/'+created.run_id,{headers:memberHeaders});expect(response.ok()).toBe(true);
    const blind=await response.json();expect(blind.blind).toBe(true);expect(blind.evidence_pack).toHaveLength(18);
    expect(blind).not.toHaveProperty('protocol');expect(blind).not.toHaveProperty('report');
    expect(blind.evidence_pack.every(e=>!Object.hasOwn(e.evidence,'facts'))).toBe(true);
    const denied=await page.request.post(batchBase,{headers:memberHeaders,data:{limit:4,force:false}});expect(denied.status()).toBe(403);
    raters.push({username,report_sha256:blind.report_sha256,submitted:blind.submitted_controls.length});
   }finally{await page.request.post('/api/auth/logout',{headers:memberHeaders});}
  }
  expect(raters[0].report_sha256).toBe(raters[1].report_sha256);expect(raters.every(r=>r.submitted===0)).toBe(true);
  writeFileSync(process.env.ISO_ISOLATED_ORCHESTRATION_RECEIPT,JSON.stringify({
   test_data_only:true,human_assessment:false,independent_validation:false,
   stopped_batch:{batch_id:stopped.batch_id,status:stopped.status,planned:stopped.plan.length,results:stopped.results},
   completed_batch:{batch_id:completed.batch_id,status:completed.status,planned:completed.plan.length,results:completed.results},
   candidate:{run_id:created.run_id,engine:candidateEngine,state:result.state,records:result.report.records.length,capture_sha256:result.report.capture_sha256,plan_sha256:plan.sha256,
    report_sha256:result.report.sha256,model:result.report.model,
    results:result.report.records.map(r=>({control_id:r.control_id,status:r.status,error:r.error,execution_source:r.execution_source,attempts:r.attempts,repaired:r.repaired}))},
   synthetic_raters:raters
  },null,2),'utf8');
 }finally{await page.request.post('/api/auth/logout',{headers});}
});
