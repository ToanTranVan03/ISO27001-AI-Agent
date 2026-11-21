import {test,expect} from '@playwright/test';
import {fileURLToPath} from 'node:url';

process.loadEnvFile(fileURLToPath(new URL('../../.env',import.meta.url)));
const enabled=process.env.ISO_ISOLATED_TEST==='1'&&/^iso_acceptance_[a-f0-9]{12}$/.test(process.env.ISO_ISOLATED_DBNAME||'');
test.use({baseURL:process.env.UI_BASE_URL,channel:'msedge',headless:true,actionTimeout:15000});
test.setTimeout(180000);

test('real isolated writes: source, review, SoA lifecycle and two synthetic raters',async({page})=>{
 test.skip(!enabled,'Only run through run_isolated_acceptance.py against a disposable database');
 const adminName=process.env.INITIAL_ADMIN_USERNAME;
 expect(adminName).toBe('release_admin');
 const login=async(name,password)=>{
  await page.goto('/');await page.getByLabel('Tên đăng nhập').fill(name);await page.getByLabel('Mật khẩu').fill(password);
  await page.getByRole('button',{name:'ĐĂNG NHẬP HỆ THỐNG'}).click();
  await expect(page.getByRole('heading',{name:'Tổng quan đánh giá tuân thủ',exact:true})).toBeVisible();
  return page.evaluate(()=>sessionStorage.getItem('iso_team_token'));
 };
 const adminToken=await login(adminName,process.env.INITIAL_ADMIN_PASSWORD);
 const aid=await page.evaluate(()=>sessionStorage.getItem('iso_team_assessment'));
 const base=`/api/assessments/${aid}`,path=`${base}/enterprise/scope56`;
 const request=async(method,url,body,token=adminToken)=>{
  const r=await page.request.fetch(url,{method,headers:{Authorization:`Bearer ${token}`},...(body===undefined?{}:{data:body})});
  expect(r.ok(),`${method} ${url}: ${await r.text()}`).toBeTruthy();return r.json();
 };
 const initial=await request('GET',path);
 for(const name of ['release_rater1','release_rater2'])await request('POST','/api/team/users',{
  username:name,display_name:`SYNTHETIC TEST ONLY ${name}`,password:process.env.ISO_ASSESSOR_PASSWORD});
 // Deliberately artificial test-only scope to exercise an approval transition.
 for(const c of initial.controls.filter(c=>c.control_id!=='A.6.1'))await request('POST',path+'/decisions',{
  control_id:c.control_id,applicable:false,reason:'Synthetic integration test exclusion; never a real scope decision.',
  treatment:'Synthetic test fixture only; no operational remediation asserted.'});
 await request('POST',path+'/rubric/approval',{rubric_sha256:initial.rubric_sha256,note:'SYNTHETIC integration test acknowledgment only, not a professional approval.'});
 await page.getByRole('button',{name:'Doanh nghiệp',exact:true}).click();await page.getByRole('button',{name:'Tổng quan 56 control',exact:true}).click();
 const open=async()=>page.getByRole('row').filter({has:page.getByText('A.6.1',{exact:true})}).getByRole('button',{name:'Bổ sung',exact:true}).click();
 await open();
 await page.getByLabel('Xuất xứ / đơn vị cung cấp').fill('SYNTHETIC isolated browser integration fixture only');
 await page.getByLabel('Chọn bản gốc bằng chứng').setInputFiles({name:'synthetic-record.txt',mimeType:'text/plain',buffer:Buffer.from('Synthetic integration test HR record. Verification remains unknown. This file is not genuine employee screening evidence.')});
 await page.getByRole('button',{name:'Lưu nguồn và bản gốc',exact:true}).click();
 await expect(page.getByText('Đã lưu nguồn mới',{exact:true})).toBeVisible();
 await expect(page.getByText('Đã tiếp nhận nguồn. Chạy đánh giá lại và thẩm định trên nguồn hiện hành.',{exact:true})).toBeVisible();
 await expect(page.getByText('Dữ liệu đã đổi; chọn lại control và đọc lại nguồn trước khi thẩm định.',{exact:true})).toBeVisible();
 await page.getByText('02 · Thẩm định kết luận trên nguồn hiện hành',{exact:true}).click();
 await expect(page.getByRole('button',{name:'Người đánh giá xác nhận',exact:true})).toBeDisabled();
 await open();
 await expect(page.getByText('Dữ liệu đã đổi; chọn lại control và đọc lại nguồn trước khi thẩm định.',{exact:true})).toHaveCount(0);
 const current=await request('GET',path),control=current.controls.find(c=>c.control_id==='A.6.1');
 const eid=control.evidence.find(e=>e.source?.includes('synthetic-record.txt')).evidence_id;
 const original=await page.request.get(`${path}/controls/A.6.1/sources/${eid}/original`,{headers:{Authorization:`Bearer ${adminToken}`}});
 expect(original.status()).toBe(200);expect(await original.text()).toContain('Synthetic integration test');
 for(let i=1;i<=control.pass_criteria.length;i++){
  await page.getByLabel(`Căn cứ tiêu chí ${i}`,{exact:true}).fill(`Synthetic test criterion ${i}: source does not establish the actual requirement.`);
  await page.getByLabel(`Nguồn tiêu chí ${i}`,{exact:true}).selectOption([eid]);
 }
 await page.getByLabel('Căn cứ thẩm định',{exact:true}).fill('SYNTHETIC integration test: unknown criteria yield insufficient evidence. No expert judgment asserted.');
 await page.getByRole('button',{name:'Người đánh giá xác nhận',exact:true}).click();
 await expect(page.getByText('Đã lưu thẩm định có danh tính và phiên bản bằng chứng.',{exact:true})).toBeVisible();
 await page.getByText('03 · Tính áp dụng & kế hoạch xử lý',{exact:true}).click();
 await page.getByLabel('Tính áp dụng',{exact:true}).selectOption('true');
 await page.getByLabel('Lý do áp dụng',{exact:true}).fill('Synthetic test scope; applies only to this disposable dataset.');
 await page.getByLabel('Kế hoạch xử lý',{exact:true}).fill('Synthetic test plan: collect suitable HR evidence and review again.');
 await page.getByLabel('Người chịu trách nhiệm xử lý',{exact:true}).fill('SYNTHETIC TEST OWNER');
 await page.getByLabel('Hạn xử lý',{exact:true}).fill('2026-12-31');
 await page.getByLabel('Cách kiểm tra lại',{exact:true}).fill('Synthetic test: recollect source and check the same criteria.');
 await page.getByRole('button',{name:'Admin lưu quyết định / kế hoạch nháp',exact:true}).click();
 await expect(page.getByText('Đã ghi quyết định tính áp dụng; SoA toàn bộ vẫn là dự thảo chờ thẩm định.',{exact:true})).toBeVisible();
 const ready=await request('GET',path);expect(ready.soa.approval_ready).toBe(true);
 await page.getByLabel('Căn cứ phê duyệt SoA 56').fill('SYNTHETIC integration test approval in disposable database only. Not a real professional signoff.');
 await page.getByRole('button',{name:'Admin phê duyệt SoA toàn phạm vi',exact:true}).click();
 await expect(page.getByText('Đã ghi phê duyệt của người phụ trách trong phạm vi đồ án.',{exact:true})).toBeVisible();
 const approved=await request('GET',path);expect(approved.soa.approval).toBe('HUMAN_APPROVED_PROJECT_SCOPE');
 const changed=await page.request.post(`${path}/controls/A.6.1/sources/upload`,{headers:{Authorization:`Bearer ${adminToken}`},multipart:{
  evidence_type:control.expected_evidence_types[0],origin:'SYNTHETIC changed source for invalidation test',
  file:{name:'changed-record.txt',mimeType:'text/plain',buffer:Buffer.from('Synthetic changed HR record for snapshot invalidation; this is not actual employee evidence.')}}});
 expect(changed.status()).toBe(201);
 const stale=await request('GET',path);expect(stale.soa.approval).toBe('DRAFT_NOT_APPROVED');
 expect(stale.controls.find(c=>c.control_id==='A.6.1').human_review_current).toBe(false);
 const rejected=await page.request.post(path+'/approval',{headers:{Authorization:`Bearer ${adminToken}`},data:{fingerprint:approved.soa.fingerprint,note:'Synthetic stale fingerprint must never approve again.'}});
 expect(rejected.status()).toBe(409);
 const run=await request('POST',base+'/a8/runs',{profile:'mixed',mode:'rules',transport:'files'});
 let finished;
 await expect.poll(async()=>{finished=await request('GET',base+'/a8/runs/'+run.run_id);return finished.state;},{timeout:30000}).toBe('finished');
 await page.getByRole('button',{name:'Đăng xuất',exact:true}).click();
 for(const username of ['release_rater1','release_rater2']){
  const token=await login(username,process.env.ISO_ASSESSOR_PASSWORD);
  const blind=await request('GET',base+'/a8/runs/'+run.run_id,undefined,token);
  expect(blind.blind).toBe(true);expect(blind).not.toHaveProperty('report');
  await page.getByRole('button',{name:'Thực nghiệm A.8',exact:true}).click();
  await page.getByLabel('Mở lượt đánh giá đã lưu').selectOption(run.run_id);
  const cid=blind.evidence_pack[0].control_id;
  await page.getByLabel('Control chấm mù',{exact:true}).selectOption(cid);
  await page.getByLabel('Nguồn hỗ trợ đánh giá').selectOption('ai_assisted');
  await page.getByLabel('Đã xem kết quả trước khi chấm').selectOption('yes');
  await page.getByLabel('Kết luận chấm mù',{exact:true}).selectOption('Insufficient Evidence');
  await page.getByLabel('Lý do đánh giá mù').fill(`SYNTHETIC TEST ONLY: ${cid} browser submission, not a genuine human conclusion.`);
  await page.getByRole('button',{name:'Nộp và khóa kết luận',exact:true}).click();
  await expect(page.getByText(/Đã nộp 1\/18/)).toBeVisible();
  const payload=c=>({control_id:c,expected:'Insufficient Evidence',rationale:`SYNTHETIC TEST ONLY ${c}: artificial label to verify persistence, not independent expert judgment.`,
   assistance:'ai_assisted',prior_exposure:'yes',report_sha256:blind.report_sha256,quality_warning_acknowledged:true});
  const duplicate=await page.request.post(base+'/a8/runs/'+run.run_id+'/reviews',{headers:{Authorization:`Bearer ${token}`},data:payload(cid)});
  expect(duplicate.status()).toBe(409);
  for(const record of blind.evidence_pack.slice(1))await request('POST',base+'/a8/runs/'+run.run_id+'/reviews',payload(record.control_id),token);
  await page.reload();await expect(page.getByRole('heading',{name:'Tổng quan đánh giá tuân thủ',exact:true})).toBeVisible();
  const full=await request('GET',base+'/a8/runs/'+run.run_id,undefined,token);
  expect(full.blind).not.toBe(true);expect(full.review_analysis.submitted_label_count).toBe(18);
  expect(full.review_analysis.complete_independent_reviewers).toHaveLength(0);
  await page.getByRole('button',{name:'Đăng xuất',exact:true}).click();
 }
 const refreshedAdmin=await login(adminName,process.env.INITIAL_ADMIN_PASSWORD);
 const final=await request('GET',base+'/a8/runs/'+run.run_id,undefined,refreshedAdmin);
 expect(final.review_analysis.submitted_label_count).toBe(36);
 expect(final.review_analysis.complete_reviewers).toHaveLength(2);
 expect(final.human_reference_reviewer_id).toBeNull();
 await page.getByRole('button',{name:'Đăng xuất',exact:true}).click();
});
