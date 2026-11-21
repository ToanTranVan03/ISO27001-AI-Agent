import {test,expect} from '@playwright/test';
import {fileURLToPath} from 'node:url';
process.loadEnvFile(fileURLToPath(new URL('../../.env',import.meta.url)));
test.use({baseURL:process.env.UI_BASE_URL||'http://127.0.0.1:5173',channel:'msedge',headless:true,actionTimeout:15000});
test.setTimeout(60000);

async function login(page){
 await page.goto('/');await page.getByLabel('Tên đăng nhập').fill(process.env.INITIAL_ADMIN_USERNAME||'admin');
 await page.getByLabel('Mật khẩu').fill(process.env.INITIAL_ADMIN_PASSWORD);
 await page.getByRole('button',{name:'ĐĂNG NHẬP HỆ THỐNG'}).click();
 await expect(page.getByRole('heading',{name:'Tổng quan đánh giá tuân thủ',exact:true})).toBeVisible();
 return page.evaluate(()=>({token:sessionStorage.getItem('iso_team_token'),aid:sessionStorage.getItem('iso_team_assessment')}));
}

test('batch UI: rejects stale start, follows running batch across reload and stops without losing results',async({page})=>{
 test.skip(!process.env.INITIAL_ADMIN_PASSWORD,'Local admin required');let session;
 try{
  session=await login(page);const {aid,token}=session;
  const scopePath=`/api/assessments/${aid}/enterprise/scope56`,base=`/api/assessments/${aid}/enterprise/shared-work/batches`;
  const before=await (await page.request.get(scopePath,{headers:{Authorization:`Bearer ${token}`}})).json();
  const bid='00000000-0000-0000-0000-000000000096';let batch=null,starts=0,stops=0;
  await page.route(`**${base}**`,async route=>{
   const req=route.request(),path=new URL(req.url()).pathname;
   if(req.method()==='GET')return route.fulfill({json:{items:batch?[batch]:[]}});
   if(req.method()==='POST'&&path===base){
    starts++;expect(req.postDataJSON()).toEqual({limit:4,force:true});
    if(starts===1)return route.fulfill({status:409,json:{detail:'UI MOCK: nguồn đã đổi; kiểm tra lại trước khi chạy.'}});
    batch={batch_id:bid,status:'RUNNING',created_at:'2026-11-21T10:00:00Z',plan:[{control_id:'A.8.13'},{control_id:'A.8.15'}],results:[{control_id:'A.8.13',status:'SUCCEEDED'}]};
    return route.fulfill({status:202,json:{action:'started',batch_id:bid}});
   }
   if(req.method()==='POST'&&path===`${base}/${bid}/stop`){stops++;batch.status='STOP_REQUESTED';return route.fulfill({json:batch});}
   return route.abort('blockedbyclient');
  });
  await page.getByRole('button',{name:'Hồ sơ ISO',exact:true}).click();
  const start=page.getByRole('button',{name:'Bắt đầu lượt',exact:true});
  await page.getByLabel('Giới hạn control mỗi lượt').selectOption('4');
  await page.getByLabel('Đánh giá lại cả nguồn hiện hành').check();
  await start.click();await expect(page.getByRole('alert')).toContainText('UI MOCK: nguồn đã đổi');
  await expect(start).toBeEnabled();await start.click();
  await expect(start).toBeDisabled();await expect(page.getByRole('progressbar')).toHaveAttribute('aria-valuenow','1');
  await page.reload();await expect(page.getByRole('heading',{name:'Agent đánh giá theo lô trên server',exact:true})).toBeVisible();
  await expect(start).toBeDisabled();await page.getByRole('button',{name:'Dừng sau việc hiện tại',exact:true}).click();
  await expect(page.getByRole('button',{name:'Dừng sau việc hiện tại',exact:true})).toBeDisabled();
  await expect(page.getByRole('status').filter({hasText:'Đang chờ dừng sau việc hiện tại'})).toBeVisible();
  batch.status='STOPPED';
  await expect(start).toBeEnabled({timeout:10000});
  await expect(page.getByRole('progressbar')).toHaveAttribute('aria-valuenow','1');
  const downloading=page.waitForEvent('download');await page.getByRole('button',{name:'Xuất lượt',exact:true}).click();
  const stream=await (await downloading).createReadStream();let content='';for await(const chunk of stream)content+=chunk.toString();
  const exported=JSON.parse(content);expect(exported.status).toBe('STOPPED');expect(exported.results).toHaveLength(1);
  expect(starts).toBe(2);expect(stops).toBe(1);
  const after=await (await page.request.get(scopePath,{headers:{Authorization:`Bearer ${token}`}})).json();
  expect(after.soa.fingerprint).toBe(before.soa.fingerprint);expect(after.acceptance).toEqual(before.acceptance);
 }finally{if(session)await page.request.post('/api/auth/logout',{headers:{Authorization:`Bearer ${session.token}`}});}
});

test('candidate UI: invalid JSON, server refusal, receipt, changed engine and concurrent run',async({page})=>{
 test.skip(!process.env.INITIAL_ADMIN_PASSWORD,'Local admin required');let session;
 try{
  session=await login(page);const {aid,token}=session,base=`/api/assessments/${aid}/a8`;
  const before=await (await page.request.get(base+'/runs',{headers:{Authorization:`Bearer ${token}`}})).json();
  let checks=0,starts=0;
  const plan={sha256:'a'.repeat(64),dataset_usage:'UI-MOCK-NOT-VALIDATION-DATA'};
  await page.route(`**${base}/candidate-runs**`,async route=>{
   const req=route.request();expect(req.method()).toBe('POST');expect(req.postDataJSON().plan).toEqual(plan);
   if(new URL(req.url()).pathname.endsWith('/validate')){
    checks++;if(checks===1)return route.fulfill({status:422,json:{detail:'UI MOCK: Source matches known fixture'}});
    return route.fulfill({json:{valid:true,plan_sha256:plan.sha256,independent_validation:false,model_called:false,run_created:false,
     controls:[{control_id:'A.8.1',artifact_count:3,unknown_checks:['disk_encrypted']}],note:'UI MOCK ONLY'}});
   }
   starts++;return route.fulfill({status:409,json:{detail:'UI MOCK: Đợt này đang có lượt chạy.'}});
  });
  await page.getByRole('button',{name:'Thực nghiệm A.8',exact:true}).click();
  await page.getByText('Tổng hợp nghiên cứu & nhập gói nguồn kiểm định',{exact:true}).click();
  await page.getByText('Nhập gói nguồn ứng viên đã chốt · admin',{exact:true}).click();
  const file=page.getByLabel('Gói ứng viên JSON đã chốt'),check=page.getByRole('button',{name:'Kiểm tra gói, chưa chạy model',exact:true}),start=page.getByRole('button',{name:'Nhập và chạy gói ứng viên',exact:true});
  await expect(start).toBeDisabled();
  await file.setInputFiles({name:'invalid.json',mimeType:'application/json',buffer:Buffer.from('{')});await check.click();
  await expect(page.getByRole('alert')).toBeVisible();expect(checks).toBe(0);await expect(start).toBeDisabled();
  await file.setInputFiles({name:'mock-plan.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(plan))});await check.click();
  await expect(page.getByRole('alert')).toContainText('known fixture');await expect(start).toBeDisabled();
  await check.click();const receipt=page.getByRole('region',{name:'Phiếu kiểm tra gói ứng viên'});
  await expect(receipt).toContainText('disk_encrypted');await expect(receipt).toContainText(plan.sha256);
  const downloading=page.waitForEvent('download');await page.getByRole('button',{name:'Xuất phiếu kiểm tra gói',exact:true}).click();
  const stream=await (await downloading).createReadStream();let text='';for await(const chunk of stream)text+=chunk.toString();
  expect(JSON.parse(text)).toMatchObject({model_called:false,run_created:false,independent_validation:false,plan_sha256:plan.sha256});
  await page.getByRole('combobox',{name:'Engine',exact:true}).selectOption('rules');await expect(start).toBeDisabled();
  await expect(page.getByText('Engine hoặc đợt đã đổi; kiểm tra lại gói trước khi chạy.',{exact:true})).toBeVisible();
  await check.click();await expect(start).toBeEnabled();await start.click();
  await expect(page.getByRole('alert')).toContainText('Đợt này đang có lượt chạy');expect(starts).toBe(1);
  const after=await (await page.request.get(base+'/runs',{headers:{Authorization:`Bearer ${token}`}})).json();
  expect(after.map(r=>r.run_id)).toEqual(before.map(r=>r.run_id));
 }finally{if(session)await page.request.post('/api/auth/logout',{headers:{Authorization:`Bearer ${session.token}`}});}
});
