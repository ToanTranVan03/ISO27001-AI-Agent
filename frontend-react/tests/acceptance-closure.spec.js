import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
process.loadEnvFile(fileURLToPath(new URL('../../.env',import.meta.url)));
test.use({baseURL:process.env.UI_BASE_URL||'http://127.0.0.1:5173',channel:'msedge',headless:true,actionTimeout:15000});
test.setTimeout(60000);

async function login(page,username,password){
 await page.goto('/');await page.getByLabel('Tên đăng nhập').fill(username);await page.getByLabel('Mật khẩu').fill(password);
 await page.getByRole('button',{name:'ĐĂNG NHẬP HỆ THỐNG'}).click();
 await expect(page.getByRole('heading',{name:'Tổng quan đánh giá tuân thủ',exact:true})).toBeVisible();
 return page.evaluate(()=>({token:sessionStorage.getItem('iso_team_token'),aid:sessionStorage.getItem('iso_team_assessment')}));
}
async function download(page,name){const waiting=page.waitForEvent('download');await page.getByRole('button',{name,exact:true}).click();const stream=await (await waiting).createReadStream();let text='';for await(const chunk of stream)text+=chunk.toString();return text;}

test('acceptance: exported A8 JSON, CSV and Markdown bind to the selected report',async({page})=>{
 test.skip(!process.env.INITIAL_ADMIN_PASSWORD,'Local admin required');let session;
 try{
  session=await login(page,process.env.INITIAL_ADMIN_USERNAME||'admin',process.env.INITIAL_ADMIN_PASSWORD);
  const base=`/api/assessments/${session.aid}/a8`,headers={Authorization:`Bearer ${session.token}`};
  const runs=await (await page.request.get(base+'/runs',{headers})).json(),run=runs.find(r=>r.mine&&r.state==='finished');expect(run).toBeTruthy();
  const doc=await (await page.request.get(base+'/runs/'+run.run_id,{headers})).json();
  await page.getByRole('button',{name:'Thực nghiệm A.8',exact:true}).click();await page.getByLabel('Mở lượt đánh giá đã lưu').selectOption(run.run_id);
  await expect(page.getByRole('heading',{name:'Kết quả kiểm tra A.8',exact:true})).toBeVisible();
  const exported=JSON.parse(await download(page,'Xuất hồ sơ và đối chiếu JSON'));
  expect(exported.run_id).toBe(run.run_id);expect(exported.report.sha256).toBe(doc.report.sha256);expect(exported).not.toHaveProperty('designer_reference');
  const csv=await download(page,'Xuất bảng đối chiếu CSV');
  const rows=csv.replace(/^\uFEFF/,'').split('\r\n');expect(rows).toHaveLength(doc.report.records.length+1);
  expect(rows[0]).toContain('"Khớp người đánh giá"');
  for(const record of doc.report.records){
   const row=rows.slice(1).map(line=>line.slice(1,-1).split('","')).find(c=>c[0]===record.control_id);
   expect(row).toBeTruthy();expect(row[1]).toBe(record.status||'');
   const human=doc.human_comparison.cases.find(c=>c.case_id===record.case_id);
   expect(row[4]).toBe(human?.expected||'');expect(row[5]).toBe(String(human?.correct??''));
  }
  const md=await download(page,'Xuất báo cáo SoA Markdown');expect(md).toContain(doc.report.sha256);
  expect(md).toContain(`Trạng thái: ${doc.soa.approval}`);
  for(const entry of doc.soa.entries)expect(md).toContain(`| ${entry.control_id} |`);
 }finally{if(session)await page.request.post('/api/auth/logout',{headers:{Authorization:`Bearer ${session.token}`}});}
});

test('acceptance: old run is read-only, rationale errors and warning acknowledgments stay separate',async({page})=>{
 test.skip(!process.env.ACCEPTANCE_KHOA_PASSWORD,'Local assessor required');let session;
 try{
  session=await login(page,'ledangkhoa',process.env.ACCEPTANCE_KHOA_PASSWORD);
  const base=`/api/assessments/${session.aid}/a8`,old='00000000-0000-0000-0000-000000000097',current='00000000-0000-0000-0000-000000000098';
  const report=JSON.parse(readFileSync(fileURLToPath(new URL('../../docs/a8-results/live-v2-ollama-pilot.json',import.meta.url)),'utf8')).report;
  const pack=report.records.map(r=>({control_id:r.control_id,name:r.name,criteria_checks:r.criteria_checks,criteria_details:r.criteria_details,evidence:Object.fromEntries(Object.entries(r.evidence).filter(([key])=>key!=='facts'))}));
  const blind=id=>({run_id:id,state:'finished',mode:'blind',profile:'MOCK UI ONLY',blind:true,can_review:id===current,report_sha256:report.sha256,submitted_controls:[],evidence_pack:pack});
  let submits=0;
  await page.route(`**${base}/runs**`,async route=>{
   const req=route.request(),path=new URL(req.url()).pathname;
   if(req.method()==='GET'&&path===base+'/runs')return route.fulfill({json:[old,current].map(run_id=>({run_id,state:'finished',mine:false,mode:'blind',profile:'UI MOCK',can_review:run_id===current,has_artifacts:true,created_at:'2026-11-21T00:00:00Z'}))});
   if(req.method()==='GET'&&[base+'/runs/'+old,base+'/runs/'+current].includes(path))return route.fulfill({json:blind(path.endsWith(old)?old:current)});
   if(req.method()==='POST'&&path.endsWith('/review-check')){
    const filler=req.postDataJSON().rationale.startsWith('ssss');return route.fulfill({json:{blocked:filler,issues:[{code:filler?'filler':'duplicate',message:filler?'UI MOCK: ký tự thử bị chặn':'UI MOCK: kiểm tra dán nhầm control khác'}],note:'UI MOCK ONLY'}});
   }
   if(req.method()==='POST'&&path.endsWith('/reviews')){submits++;return route.fulfill({status:422,json:{detail:'UI MOCK: căn cứ ký tự thử, chưa lưu nhãn'}});}
   return route.abort('blockedbyclient');
  });
  await page.getByRole('button',{name:'Thực nghiệm A.8',exact:true}).click();await page.getByLabel('Mở lượt đánh giá đã lưu').selectOption(old);
  await expect(page.getByRole('heading',{name:'Lượt lịch sử · Chỉ đọc, không thể nộp chấm mới',exact:true})).toBeVisible();
  await expect(page.getByRole('button',{name:'Nộp và khóa kết luận',exact:true})).toHaveCount(0);
  await page.getByRole('button',{name:`Mở lượt có thể chấm · ${current.slice(0,8)}`,exact:true}).click();await page.getByLabel('Control chấm mù',{exact:true}).selectOption(pack[0].control_id);
  await expect(page.getByRole('heading',{name:'Chấm giả định để luyện tập · Gói mẫu riêng',exact:true})).toHaveCount(0);
  await page.getByLabel('Kết luận chấm mù',{exact:true}).selectOption('Insufficient Evidence');
  await page.getByLabel('Lý do đánh giá mù').fill('s'.repeat(50));await page.getByRole('button',{name:'Kiểm tra căn cứ trước khi nộp',exact:true}).click();
  await expect(page.getByText('UI MOCK: ký tự thử bị chặn',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Nộp và khóa kết luận',exact:true}).click();await expect(page.getByRole('alert')).toContainText('chưa lưu nhãn');
  await page.getByLabel('Lý do đánh giá mù').fill('UI MOCK: potentially duplicated observation, not a real human conclusion.');
  await page.getByRole('button',{name:'Kiểm tra căn cứ trước khi nộp',exact:true}).click();
  const ack=page.getByRole('checkbox',{name:'Tôi đã đọc lại nguồn và xác nhận căn cứ này có chủ đích, không dán nhầm.',exact:true});
  await ack.check();await expect(ack).toBeChecked();
  await page.getByLabel('Lý do đánh giá mù').fill('UI MOCK: changed rationale must remove the prior warning acknowledgment.');await expect(ack).toHaveCount(0);
  await page.getByRole('button',{name:'Kiểm tra căn cứ trước khi nộp',exact:true}).click();await expect(ack).not.toBeChecked();
  expect(submits).toBe(1);
 }finally{if(session)await page.request.post('/api/auth/logout',{headers:{Authorization:`Bearer ${session.token}`}});}
});

test('acceptance: source requests distinguish missing, unusable and corrupt originals without writing evidence',async({page})=>{
 test.skip(!process.env.INITIAL_ADMIN_PASSWORD,'Local admin required');let session;
 try{
  session=await login(page,process.env.INITIAL_ADMIN_USERNAME||'admin',process.env.INITIAL_ADMIN_PASSWORD);
  const path=`/api/assessments/${session.aid}/enterprise/scope56`,headers={Authorization:`Bearer ${session.token}`};
  const before=await (await page.request.get(path,{headers})).json();
  const mocked=structuredClone(before),controls=mocked.controls.slice(0,3);let writes=0;
  mocked.source_requests.requests=controls.map((c,i)=>({control_id:c.control_id,name:`UI MOCK SOURCE ${i+1}`,
   owner_role:'UI MOCK — no assignment',reason:['supply_missing_source','replace_unusable_source','restore_source_integrity'][i],
   source_issues:i===2?[{evidence_id:'UI-MOCK-LOST-ORIGINAL',issues:['original_missing'],integrity_state:'failed'}]:[]}));
  await page.route(`**${path}**`,async route=>{
   const request=route.request();
   if(request.method()!=='GET'){writes++;return route.abort('blockedbyclient');}
   if(new URL(request.url()).pathname===path)return route.fulfill({json:mocked});
   return route.continue();
  });
  await page.reload();
  await page.getByText('Quản lý nguồn, tiêu chí và hồ sơ bàn giao',{exact:true}).click();
  await page.getByText('Hồ sơ bàn giao và công cụ quản lý',{exact:true}).click();
  await page.getByText('Nguồn cần bổ sung hoặc đối chiếu · 3 control',{exact:true}).click();
  await expect(page.getByText('Chưa có nguồn ngoài preset — cần cung cấp hồ sơ gốc.',{exact:true})).toBeVisible();
  await expect(page.getByText('Nội dung chưa dùng được — kiểm tra bản gốc/OCR và nộp lại.',{exact:true})).toBeVisible();
  await expect(page.getByText('Bản lưu thiếu hoặc lệch kiểm tra toàn vẹn — đối chiếu bản gốc, không sửa hash để bỏ qua lỗi.',{exact:true})).toBeVisible();
  await expect(page.getByText('UI-MOCK-LOST-ORIGINAL: original_missing',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:`${controls[2].control_id} · UI MOCK SOURCE 3`,exact:true}).click();
  await expect(page).toHaveURL(new RegExp(`control=${controls[2].control_id.replaceAll('.','\\.')}`));
  await expect(page.getByRole('heading',{name:`${controls[2].control_id} · ${controls[2].name}`,exact:true})).toBeVisible();
  expect(writes).toBe(0);
  const after=await (await page.request.get(path,{headers})).json();
  expect(after.handoff_packet.sha256).toBe(before.handoff_packet.sha256);
  expect(after.soa.fingerprint).toBe(before.soa.fingerprint);
 }finally{if(session)await page.request.post('/api/auth/logout',{headers:{Authorization:`Bearer ${session.token}`}});}
});
