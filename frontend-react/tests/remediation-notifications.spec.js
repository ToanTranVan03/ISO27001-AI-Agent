import {test,expect} from '@playwright/test';
import {fileURLToPath} from 'node:url';
process.loadEnvFile(fileURLToPath(new URL('../../.env',import.meta.url)));
test.use({baseURL:process.env.UI_BASE_URL||'http://127.0.0.1:5173',channel:'msedge',headless:true,actionTimeout:15000});
test.setTimeout(60000);

test('notifications: unread filter and persisted-read UI do not mutate remediation or assessment',async({page})=>{
 test.skip(!process.env.INITIAL_ADMIN_PASSWORD,'Local admin required');let token,reads=0;
 const item={notification_id:'40000000-0000-4000-8000-000000000001',event_type:'overdue',created_at:'2026-11-22T01:00:00+00:00',read_at:null,
  body:{title:'UI MOCK overdue reminder',action_title:'UI MOCK assigned work',control_id:'A.6.1',finding_id:'50000000-0000-4000-8000-000000000001',action_id:'60000000-0000-4000-8000-000000000001',due_date:'2026-11-21',note:'UI MOCK reminder only, not a compliance finding.'}};
 await page.route('**/remediation/notifications**',async route=>{
  const req=route.request(),url=new URL(req.url());
  if(req.method()==='GET')return route.fulfill({json:{items:url.searchParams.get('unread_only')==='true'&&item.read_at?[]:[item],unread_count:item.read_at?0:1,note:'UI MOCK inbox, no main data writes'}});
  expect(req.method()).toBe('POST');expect(url.pathname.endsWith('/'+item.notification_id+'/read')).toBe(true);
  reads++;item.read_at='2026-11-22T02:00:00+00:00';return route.fulfill({json:{notification_id:item.notification_id,read_at:item.read_at}});
 });
 try{
  await page.goto('/');await page.getByLabel('Tên đăng nhập').fill(process.env.INITIAL_ADMIN_USERNAME||'admin');await page.getByLabel('Mật khẩu').fill(process.env.INITIAL_ADMIN_PASSWORD);await page.getByRole('button',{name:'ĐĂNG NHẬP HỆ THỐNG'}).click();
  await expect(page.getByRole('heading',{name:'Tổng quan đánh giá tuân thủ',exact:true})).toBeVisible();
  const session=await page.evaluate(()=>({token:sessionStorage.getItem('iso_team_token'),aid:sessionStorage.getItem('iso_team_assessment')}));token=session.token;
  const path=`/api/assessments/${session.aid}/enterprise/scope56`,headers={Authorization:`Bearer ${token}`};
  const before=await (await page.request.get(path,{headers})).json();
  await page.getByText('Tư vấn & khắc phục · từ phát hiện đến xác minh',{exact:true}).click();
  await page.getByText('Thông báo khắc phục · 1 chưa đọc',{exact:true}).click();
  await expect(page.getByText('UI MOCK overdue reminder',{exact:true})).toBeVisible();
  await page.getByRole('checkbox',{name:'Chỉ thông báo chưa đọc',exact:true}).check();
  await page.getByRole('button',{name:'Đánh dấu đã đọc',exact:true}).click();
  await expect(page.getByText('Thông báo khắc phục · 0 chưa đọc',{exact:true})).toBeVisible();
  await expect(page.getByText('Chưa có thông báo thuộc bộ lọc này.',{exact:true})).toBeVisible();expect(reads).toBe(1);
  const after=await (await page.request.get(path,{headers})).json();
  expect(after.handoff_packet.sha256).toBe(before.handoff_packet.sha256);expect(after.soa.fingerprint).toBe(before.soa.fingerprint);
 }finally{if(token)await page.request.post('/api/auth/logout',{headers:{Authorization:`Bearer ${token}`},timeout:10000}).catch(()=>{});}
});
