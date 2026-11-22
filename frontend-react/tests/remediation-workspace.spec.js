import {test,expect} from '@playwright/test';
import {fileURLToPath} from 'node:url';
process.loadEnvFile(fileURLToPath(new URL('../../.env',import.meta.url)));
test.use({baseURL:process.env.UI_BASE_URL||'http://127.0.0.1:5173',channel:'msedge',headless:true,actionTimeout:15000});
test.setTimeout(90000);

test('corrective action UI: baseline, consultant approval, assigned work and separate verification without main writes',async({page})=>{
 test.skip(!process.env.INITIAL_ADMIN_PASSWORD,'Local admin required');let token;
 const consultant='10000000-0000-4000-8000-000000000001',operator='10000000-0000-4000-8000-000000000002',verifier='10000000-0000-4000-8000-000000000003';
 const members=[{user_id:consultant,name:'UI TEST CONSULTANT',role:'consultant'},{user_id:operator,name:'UI TEST OPERATOR',role:'operator'},{user_id:verifier,name:'UI TEST VERIFIER',role:'verifier'}];
 const board={records:[],members,role:'consultant',user_id:consultant,can_manage_roles:true,note:'UI MOCK ONLY — no real finding or approval'};
 let mutations=0,fixture,aid,scopeBefore;
 await page.route('**/remediation**',async route=>{
  const req=route.request(),path=new URL(req.url()).pathname;
  if(path.includes('/notifications'))return route.fulfill({json:{items:[],unread_count:0,note:'UI MOCK inbox'}});
  if(path.endsWith('/report.csv'))return route.fulfill({contentType:'text/csv',body:'Control,State\nA.6.1,REWORK'});
  if(path.endsWith('/report.html'))return route.fulfill({contentType:'text/html',body:'<!doctype html><html>UI MOCK print report</html>'});
  if(req.method()==='GET')return route.fulfill({json:board});
  const body=req.postDataJSON();mutations++;
  if(path.endsWith('/context'))board.records.push({record_id:'context',kind:'context',version:1,document:body});
  else if(path.endsWith('/findings')){
   const control=fixture.controls.find(c=>c.control_id===body.control_id);
   board.records.push({record_id:'20000000-0000-4000-8000-000000000001',kind:'finding',version:1,document:{...body,baseline:{review_token:control.review_token,conclusion:'Insufficient Evidence',criteria:control.pass_criteria,evidence:scopeBefore.controls.find(c=>c.control_id===body.control_id).evidence},actions:[],history:[]}});
  }else if(path.endsWith('/actions')){
   const finding=board.records.find(r=>r.kind==='finding');expect(body.expected_version).toBe(finding.version);
   finding.document.actions.push({...body,action_id:'30000000-0000-4000-8000-000000000001',state:'PENDING_APPROVAL',proposal_origin:'UI_MOCK_CONSULTANT_DRAFT',tasks:body.tasks.map((title,i)=>({task_id:`task-${i}`,title,done:false})),evidence:[],verifications:[]});finding.version++;
  }else if(path.endsWith('/events')){
   const finding=board.records.find(r=>r.kind==='finding'),action=finding.document.actions[0];expect(body.expected_version).toBe(finding.version);
   if(body.command==='approve')Object.assign(action,{state:'NOT_STARTED',assignee:body.assignee,due_date:body.due_date});
   else if(body.command==='start')action.state='IN_PROGRESS';
   else if(body.command==='task')action.tasks.find(t=>t.task_id===body.task_id).done=body.done;
   else if(body.command==='attach')action.evidence.push({evidence_id:body.evidence_id,sha256_hash:'c'.repeat(64)});
   else if(body.command==='submit')action.state='AWAITING_VERIFICATION';
   else if(body.command==='verify'){action.state='REWORK';action.verifications.push({at:'UI MOCK TIME',outcome:body.outcome,note:body.note,reviewer_id:verifier,review_token:fixture.controls[0].review_token});}
   else throw new Error('Unexpected mock command '+body.command);
   finding.version++;
  }else throw new Error('Unexpected remediation mutation '+path);
  return route.fulfill({json:{mock:true}});
 });
 try{
  await page.goto('/');await page.getByLabel('Tên đăng nhập').fill(process.env.INITIAL_ADMIN_USERNAME||'admin');await page.getByLabel('Mật khẩu').fill(process.env.INITIAL_ADMIN_PASSWORD);await page.getByRole('button',{name:'ĐĂNG NHẬP HỆ THỐNG'}).click();
  await expect(page.getByRole('heading',{name:'Tổng quan đánh giá tuân thủ',exact:true})).toBeVisible();
  ({token,aid}=await page.evaluate(()=>({token:sessionStorage.getItem('iso_team_token'),aid:sessionStorage.getItem('iso_team_assessment')})));
  const path=`/api/assessments/${aid}/enterprise/scope56`,headers={Authorization:`Bearer ${token}`};
  scopeBefore=await (await page.request.get(path,{headers})).json();fixture=structuredClone(scopeBefore);
  fixture.controls[0].evidence.push({evidence_id:'UI-MOCK-AFTER',sha256_hash:'c'.repeat(64),source:'upload-source://A.6.1/ui-mock.txt',is_synthetic:false,source_quality:{usable:true}});
  await page.route(`**${path}`,route=>route.fulfill({json:fixture}));await page.reload();
  await page.getByText('Tư vấn & khắc phục · từ phát hiện đến xác minh',{exact:true}).click();
  await page.getByText(/Hồ sơ doanh nghiệp & phạm vi ISMS/).click();
  await page.getByLabel('Tên doanh nghiệp',{exact:true}).fill('UI MOCK COMPANY');await page.getByLabel('Lĩnh vực hoạt động',{exact:true}).fill('UI mock technology');await page.getByLabel('Phạm vi ISMS',{exact:true}).fill('UI MOCK isolated business scope, not a real assessment.');await page.getByRole('button',{name:'Lưu hồ sơ và lịch sử phạm vi',exact:true}).click();
  await expect(page.getByRole('status').filter({hasText:'Đã lưu thao tác'})).toBeVisible();
  await page.getByText('Ghi nhận phát hiện trên snapshot hiện tại',{exact:true}).click();await page.getByRole('combobox',{name:'Control',exact:true}).selectOption(fixture.controls[0].control_id);
  await page.getByLabel('Phát hiện / khoảng cách',{exact:true}).fill('UI MOCK missing access review evidence');await page.getByLabel('Địa điểm, tài sản hoặc quy trình',{exact:true}).fill('UI MOCK location');await page.getByLabel('Giả thuyết nguyên nhân — cần xác nhận',{exact:true}).fill('UI MOCK cause pending investigation');await page.getByRole('button',{name:'Lưu phát hiện và baseline',exact:true}).click();
  await expect(page.getByRole('heading',{name:'UI MOCK missing access review evidence',exact:true})).toBeVisible();
  await page.getByText('Đề xuất kế hoạch cho phát hiện này',{exact:true}).click();
  for(const [label,value] of [['Tên hành động','UI MOCK review accounts'],['Hướng dẫn thực hiện','UI MOCK identify accounts, review and record actual observations.'],['Điều kiện nghiệm thu/bằng chứng cần nộp','UI MOCK submit review evidence and require separate verification.'],['Bộ phận thực hiện','UI MOCK IT'],['Nguồn lực cần thiết','UI MOCK accountable personnel'],['Công việc con — mỗi dòng một việc','UI MOCK list accounts\nUI MOCK record review']])await page.getByLabel(label,{exact:true}).fill(value);
  await page.getByRole('button',{name:'Lưu đề xuất chờ duyệt',exact:true}).click();
  const card=page.locator('article').filter({has:page.getByRole('heading',{name:'UI MOCK review accounts',exact:true})}).last();
  await card.getByRole('textbox',{name:'Ghi chú thao tác / căn cứ xác minh (ít nhất 10 ký tự)',exact:true}).fill('UI MOCK approve test plan only');await card.getByRole('combobox',{name:'Người thực hiện',exact:true}).selectOption(operator);await card.getByLabel('Hạn hoàn thành',{exact:true}).fill('2026-12-20');await card.getByRole('button',{name:'Duyệt và giao thực hiện',exact:true}).click();
  board.role='operator';board.user_id=operator;board.can_manage_roles=false;await page.getByRole('button',{name:'Làm mới khắc phục',exact:true}).click();
  await card.getByRole('textbox',{name:'Ghi chú thao tác / căn cứ xác minh (ít nhất 10 ký tự)',exact:true}).fill('UI MOCK progress, no genuine record');
  await expect(card.getByRole('checkbox').nth(1)).toBeDisabled();await card.getByRole('checkbox').nth(0).click();await expect(card.getByRole('checkbox').nth(0)).toBeChecked();await card.getByRole('checkbox').nth(1).click();await expect(card.getByRole('checkbox').nth(1)).toBeChecked();
  await card.getByRole('combobox',{name:'Bằng chứng sau thực hiện đã lưu vào control',exact:true}).selectOption('UI-MOCK-AFTER');await card.getByRole('button',{name:'Gắn nguồn vào hành động',exact:true}).click();await card.getByRole('button',{name:'Gửi xác minh — chưa kết luận đạt',exact:true}).click();
  await expect(card.getByText('Chờ xác minh',{exact:true})).toBeVisible();await expect(card.getByRole('button',{name:'Xác minh đạt',exact:true})).toHaveCount(0);
  board.role='verifier';board.user_id=verifier;await page.getByRole('button',{name:'Làm mới khắc phục',exact:true}).click();await card.getByRole('textbox',{name:'Ghi chú thao tác / căn cứ xác minh (ít nhất 10 ký tự)',exact:true}).fill('UI MOCK verifier requests more work, not a professional judgment');await card.getByRole('button',{name:'Chưa đạt — làm lại',exact:true}).click();
  await expect(card.getByText('Cần thực hiện lại',{exact:true})).toBeVisible();expect(mutations).toBeGreaterThan(5);
  for(const [name,filename] of [['Xuất CSV mở bằng Excel','khac-phuc-truoc-sau.csv'],['Tải bản in HTML · mở để lưu PDF','bao-cao-khac-phuc.html']]){
   const waiting=page.waitForEvent('download');await page.getByRole('button',{name,exact:true}).click();expect((await waiting).suggestedFilename()).toBe(filename);
  }
  const after=await (await page.request.get(path,{headers})).json();expect(after.handoff_packet.sha256).toBe(scopeBefore.handoff_packet.sha256);expect(after.soa.fingerprint).toBe(scopeBefore.soa.fingerprint);
 }finally{if(token)await page.request.post('/api/auth/logout',{headers:{Authorization:`Bearer ${token}`},timeout:10000}).catch(()=>{});}
});
