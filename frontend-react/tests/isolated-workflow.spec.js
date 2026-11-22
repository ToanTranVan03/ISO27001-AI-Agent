import {test,expect} from '@playwright/test';
import {fileURLToPath} from 'node:url';
import {readFileSync} from 'node:fs';

process.loadEnvFile(fileURLToPath(new URL('../../.env',import.meta.url)));
test.use({baseURL:process.env.UI_BASE_URL||'http://127.0.0.1:5173',channel:'msedge',headless:true});
test.setTimeout(60000);

test('isolated UI: valid upload, original download, stale review, criteria and decision draft',async({page})=>{
 const password=process.env.INITIAL_ADMIN_PASSWORD;
 test.skip(!password,'Local admin credential required');
 let token;
 try{
  await page.goto('/');
  await page.getByLabel('Tên đăng nhập').fill(process.env.INITIAL_ADMIN_USERNAME||'admin');
  await page.getByLabel('Mật khẩu').fill(password);
  await page.getByRole('button',{name:'ĐĂNG NHẬP HỆ THỐNG'}).click();
  await expect(page.getByRole('heading',{name:'Tổng quan đánh giá tuân thủ',exact:true})).toBeVisible();
  token=await page.evaluate(()=>sessionStorage.getItem('iso_team_token'));
  const aid=await page.evaluate(()=>sessionStorage.getItem('iso_team_assessment'));
  const path=`/api/assessments/${aid}/enterprise/scope56`;
  const response=await page.request.get(path,{headers:{Authorization:`Bearer ${token}`}});
  expect(response.ok()).toBeTruthy();
  const scope=await response.json();
  const before=JSON.stringify(scope);
  const fixture=structuredClone(scope),control=fixture.controls.find(c=>c.control_id==='A.6.2');
  const originalToken=control.review_token;
  let uploads=0,reviews=0,decisions=0;
  // Every write below is intercepted. Nothing is evidence or a human label.
  await page.route(`**${path}/**`,async route=>{
   const req=route.request(),url=new URL(req.url()).pathname;
   if(req.method()==='POST'&&url.endsWith('/A.6.2/sources/validate')){
    return route.fulfill({json:{preflight_only:true,original_preserved:false,evidence_saved:false,
     original_sha256:'c'.repeat(64),quality:{alphanumeric_characters:60},warnings:['UI MOCK: chưa xác nhận đủ tiêu chí.']}});
   }
   if(req.method()==='POST'&&url.endsWith('/A.6.2/sources/upload')){
    uploads++;
    expect(req.headers()['content-type']).toContain('multipart/form-data');
    expect(req.postDataBuffer().toString()).toContain('ui-isolated-source.txt');
    control.evidence=[{evidence_id:'UI-MOCK-SOURCE',source:'upload-source://A.6.2/ui-isolated-source.txt',sha256_hash:'a'.repeat(64),is_synthetic:true}];
    control.review_token='b'.repeat(64);control.usable_source_count=1;control.explicit_source_count=1;control.source_quality_issues=[];
    return route.fulfill({status:201,json:{inserted:['UI-MOCK-SOURCE'],evidence_id:'UI-MOCK-SOURCE',original_sha256:'a'.repeat(64)}});
   }
   if(req.method()==='GET'&&url.endsWith('/UI-MOCK-SOURCE/original')){
    return route.fulfill({status:200,contentType:'application/octet-stream',body:'UI MOCK ORIGINAL - NOT REAL EVIDENCE'});
   }
   if(req.method()==='POST'&&url.endsWith('/reviews')){
    const body=req.postDataJSON();reviews++;
    expect(body.control_id).toBe('A.6.2');
    expect(body.review_token).toBe(control.review_token);
    expect(body.criteria_reviews).toHaveLength(control.pass_criteria.length);
    expect(body.criteria_reviews.every(c=>c.verdict==='unknown'&&c.rationale.includes('UI mock'))).toBeTruthy();
    expect(body.conclusion).toBe('Insufficient Evidence');
    control.human_review_current=true;control.human_review=body;
    return route.fulfill({status:200,json:{mock:true}});
   }
   if(req.method()==='POST'&&url.endsWith('/decisions')){
    decisions++;const body=req.postDataJSON();
    expect(body.applicable).toBe(true);expect(body.treatment_owner).toBe('UI test owner');
    expect(body.verification_plan.length).toBeGreaterThanOrEqual(10);
    control.applicability=body;
    return route.fulfill({status:200,json:{mock:true}});
   }
   if(req.method()!=='GET')return route.abort('blockedbyclient');
   return route.fallback();
  });
  await page.route(`**${path}`,route=>route.fulfill({json:fixture}));
  // Refresh through normal navigation to load the isolated snapshot.
  await page.getByRole('button',{name:'Doanh nghiệp',exact:true}).click();
  await page.getByRole('button',{name:'Tổng quan 56 control',exact:true}).click();
  const openControl=async()=>page.getByRole('row').filter({has:page.getByText('A.6.2',{exact:true})}).getByRole('button',{name:'Bổ sung',exact:true}).click();
  await openControl();
  await page.getByLabel('Xuất xứ / đơn vị cung cấp').fill('Isolated UI mock fixture - not genuine evidence');
  await page.getByLabel('Chọn bản gốc bằng chứng').setInputFiles({name:'ui-isolated-source.txt',mimeType:'text/plain',buffer:Buffer.from('UI fixture only. This content must never be stored as real compliance evidence.')});
  await page.getByRole('button',{name:'Kiểm tra trước — chưa lưu',exact:true}).click();
  await expect(page.getByText('Đã qua kiểm tra kỹ thuật — chưa lưu bằng chứng',{exact:true})).toBeVisible();
  expect(uploads).toBe(0);expect(control.review_token).toBe(originalToken);
  await page.getByLabel('Xuất xứ / đơn vị cung cấp').fill('Updated UI mock origin, still not real evidence');
  await expect(page.getByText('Đã qua kiểm tra kỹ thuật — chưa lưu bằng chứng',{exact:true})).toHaveCount(0);
  await page.getByRole('button',{name:'Lưu nguồn và bản gốc',exact:true}).click();
  await expect(page.getByText('Đã lưu nguồn mới',{exact:true})).toBeVisible();
  expect(originalToken).not.toBe(control.review_token);
  await page.getByText('02 · Thẩm định kết luận trên nguồn hiện hành',{exact:true}).click();
  await expect(page.getByRole('button',{name:'Người đánh giá xác nhận',exact:true})).toBeDisabled();
  await expect(page.getByText('Dữ liệu đã đổi; chọn lại control và đọc lại nguồn trước khi thẩm định.',{exact:true})).toBeVisible();
  const downloading=page.waitForEvent('download');
  await page.getByRole('button',{name:/ui-isolated-source\.txt.*Bản gốc/}).click();
  const stream=await (await downloading).createReadStream();let text='';for await(const chunk of stream)text+=chunk.toString();
  expect(text).toBe('UI MOCK ORIGINAL - NOT REAL EVIDENCE');
  await openControl();
  for(let i=1;i<=control.pass_criteria.length;i++){
   await page.getByLabel(`Căn cứ tiêu chí ${i}`,{exact:true}).fill('UI mock: unknown criterion pending independent evidence verification.');
   await page.getByLabel(`Nguồn tiêu chí ${i}`,{exact:true}).selectOption(['UI-MOCK-SOURCE']);
  }
  await page.getByLabel('Căn cứ thẩm định',{exact:true}).fill('UI mock: insufficient evidence conclusion for isolated interaction testing only.');
  await page.getByRole('button',{name:'Người đánh giá xác nhận',exact:true}).click();
  await expect(page.getByText('Đã lưu thẩm định có danh tính và phiên bản bằng chứng.',{exact:true})).toBeVisible();
  await page.getByText('03 · Tính áp dụng & kế hoạch xử lý',{exact:true}).click();
  await page.getByLabel('Tính áp dụng',{exact:true}).selectOption('true');
  await page.getByLabel('Lý do áp dụng',{exact:true}).fill('UI mock applicability rationale only.');
  await page.getByLabel('Kế hoạch xử lý',{exact:true}).fill('UI mock treatment plan; not an actual decision.');
  await page.getByLabel('Người chịu trách nhiệm xử lý',{exact:true}).fill('UI test owner');
  await page.getByLabel('Hạn xử lý',{exact:true}).fill('2026-12-01');
  await page.getByLabel('Cách kiểm tra lại',{exact:true}).fill('UI mock: recollect and verify the actual evidence.');
  await page.getByRole('button',{name:'Admin lưu quyết định / kế hoạch nháp',exact:true}).click();
  await expect(page.getByText('Đã ghi quyết định tính áp dụng; SoA toàn bộ vẫn là dự thảo chờ thẩm định.',{exact:true})).toBeVisible();
  expect([uploads,reviews,decisions]).toEqual([1,1,1]);
  expect(fixture.soa.approval).toBe('DRAFT_NOT_APPROVED');
  // APIRequestContext bypasses page routes: verify the real scope is unchanged.
  const after=await page.request.get(path,{headers:{Authorization:`Bearer ${token}`}});
  const real=await after.json();
  expect(real.controls.find(c=>c.control_id==='A.6.2').review_token).toBe(JSON.parse(before).controls.find(c=>c.control_id==='A.6.2').review_token);
  expect(real.acceptance).toEqual(JSON.parse(before).acceptance);
 }finally{
  if(token)await page.request.post('/api/auth/logout',{headers:{Authorization:`Bearer ${token}`}});
 }
});

test('isolated UI: blind submission hides answers and removes locked controls after reload',async({page})=>{
 const password=process.env.ACCEPTANCE_KHOA_PASSWORD;
 test.skip(!password,'Local assessor credential required');
 const sample=JSON.parse(readFileSync(fileURLToPath(new URL('../../docs/a8-results/live-v2-ollama-pilot.json',import.meta.url)),'utf8')).report;
 const rid='00000000-0000-0000-0000-000000000092';
 const submitted=[];let token;
 try{
  await page.goto('/');await page.getByLabel('Tên đăng nhập').fill('ledangkhoa');await page.getByLabel('Mật khẩu').fill(password);
  await page.getByRole('button',{name:'ĐĂNG NHẬP HỆ THỐNG'}).click();
  await expect(page.getByRole('heading',{name:'Tổng quan đánh giá tuân thủ',exact:true})).toBeVisible();
  token=await page.evaluate(()=>sessionStorage.getItem('iso_team_token'));
  const aid=await page.evaluate(()=>sessionStorage.getItem('iso_team_assessment'));
  const base=`/api/assessments/${aid}/a8`;
  const blind=()=>({run_id:rid,state:'finished',mode:'blind',profile:'UI MOCK ONLY',blind:true,can_review:true,
   report_sha256:sample.sha256,submitted_controls:[...submitted],protocol_note:'Isolated UI test; no real labels are submitted.',
   evidence_pack:sample.records.map(r=>({control_id:r.control_id,name:r.name,criteria_checks:r.criteria_checks,criteria_details:r.criteria_details,
    evidence:Object.fromEntries(Object.entries(r.evidence).filter(([key])=>key!=='facts'))}))});
  await page.route(`**${base}/runs`,route=>route.request().method()==='GET'?route.fulfill({json:[{run_id:rid,mine:false,state:'finished',can_review:true,profile:'UI MOCK ONLY',mode:'blind',created_at:'2026-11-21T00:00:00Z'}]}):route.abort());
  await page.route(`**${base}/runs/${rid}**`,async route=>{
   const req=route.request(),url=new URL(req.url()).pathname;
   if(req.method()==='GET'&&url.endsWith(rid))return route.fulfill({json:blind()});
   if(req.method()==='POST'&&url.endsWith('/reviews')){
    const body=req.postDataJSON();
    expect(body.report_sha256).toBe(sample.sha256);
    expect(body.assistance).toBe('ai_assisted');
    expect(body.prior_exposure).toBe('yes');
    expect(body.rationale).toContain('UI MOCK');
    if(submitted.includes(body.control_id))return route.fulfill({status:409,json:{detail:'Mock locked label'}});
    submitted.push(body.control_id);return route.fulfill({json:{saved:true,mock:true}});
   }
   return route.abort('blockedbyclient');
  });
  const open=async()=>{
   await page.getByRole('button',{name:'Thực nghiệm A.8',exact:true}).click();
   await page.getByLabel('Mở lượt đánh giá đã lưu').selectOption(rid);
   await expect(page.getByRole('heading',{name:'Gói đánh giá mù · chưa hiển thị Agent hoặc đáp án nhóm',exact:true})).toBeVisible();
  };
  await open();
  await expect(page.getByRole('heading',{name:'Kết quả kiểm tra A.8',exact:true})).toHaveCount(0);
  const cid=sample.records[0].control_id;
  await page.getByLabel('Control chấm mù',{exact:true}).selectOption(cid);
  await page.getByLabel('Nguồn hỗ trợ đánh giá').selectOption('ai_assisted');
  await page.getByLabel('Đã xem kết quả trước khi chấm').selectOption('yes');
  await page.getByLabel('Kết luận chấm mù',{exact:true}).selectOption('Insufficient Evidence');
  await page.getByLabel('Lý do đánh giá mù').fill('UI MOCK ONLY - browser interaction fixture, never a real human assessment.');
  await page.getByRole('button',{name:'Nộp và khóa kết luận',exact:true}).click();
  await expect(page.getByText(/Đã nộp 1\/18/)).toBeVisible();
  expect(submitted).toEqual([cid]);
  expect(await page.getByLabel('Control chấm mù',{exact:true}).locator('option').evaluateAll(options=>options.map(o=>o.value))).not.toContain(cid);
  await page.reload();await expect(page.getByRole('heading',{name:'Đánh giá chuyên sâu A.8',exact:true})).toBeVisible();
  await expect(page.getByText(/Đã nộp 1\/18/)).toBeVisible();
  expect(await page.getByLabel('Control chấm mù',{exact:true}).locator('option').evaluateAll(options=>options.map(o=>o.value))).not.toContain(cid);
  await expect(page.getByRole('heading',{name:'Kết quả kiểm tra A.8',exact:true})).toHaveCount(0);
 }finally{if(token)await page.request.post('/api/auth/logout',{headers:{Authorization:`Bearer ${token}`}});}
});
