import {test,expect} from '@playwright/test';
import {fileURLToPath} from 'node:url';
process.loadEnvFile(fileURLToPath(new URL('../../.env',import.meta.url)));
test.use({baseURL:process.env.UI_BASE_URL||'http://127.0.0.1:5173',channel:'msedge',headless:true,actionTimeout:15000});
test.setTimeout(60000);

test('F5 keeps selection without scrolling to a control or starting work',async({page})=>{
 test.skip(!process.env.INITIAL_ADMIN_PASSWORD,'Admin credential required');let token;
 const mutations=[];
 try{
  await page.goto('/');await page.getByLabel('Tên đăng nhập').fill(process.env.INITIAL_ADMIN_USERNAME||'admin');
  await page.getByLabel('Mật khẩu').fill(process.env.INITIAL_ADMIN_PASSWORD);
  await page.getByRole('button',{name:'ĐĂNG NHẬP HỆ THỐNG'}).click();
  await expect(page.getByRole('heading',{name:'Tổng quan đánh giá tuân thủ',exact:true})).toBeVisible();
  const session=await page.evaluate(()=>({token:sessionStorage.getItem('iso_team_token'),aid:sessionStorage.getItem('iso_team_assessment')}));token=session.token;
  page.on('request',r=>{if(r.method()==='POST')mutations.push(new URL(r.url()).pathname);});
  await page.goto('/#'+new URLSearchParams({view:'scope56',control:'A.6.3',assessment:session.aid}));
  await expect(page.getByRole('heading',{name:'A.6.3 · Information security awareness, education and training',exact:true})).toBeAttached();
  await expect.poll(()=>page.evaluate(()=>window.scrollY)).toBe(0);
  // Opening the control deliberately still moves to its detail.
  await page.getByRole('button',{name:/^A\.6\.3: /}).click();
  await expect.poll(()=>page.evaluate(()=>window.scrollY)).toBeGreaterThan(100);
  await page.reload();
  await expect(page.getByRole('heading',{name:'A.6.3 · Information security awareness, education and training',exact:true})).toBeAttached();
  await expect.poll(()=>page.evaluate(()=>window.scrollY)).toBe(0);
  expect(new URLSearchParams(new URL(page.url()).hash.slice(1)).get('control')).toBe('A.6.3');
  for(const [view,context,heading] of [
   ['dossier',{control:'A.6.3'},'A.6.3 · Information security awareness, education and training'],
   ['company',{employee:'EMP-001'},/^EMP-001 ·/]
  ]){
   await page.goto('/#'+new URLSearchParams({view,assessment:session.aid,...context}));
   await expect(page.getByRole('heading',{name:heading,exact:true})).toBeAttached();
   await page.evaluate(()=>window.scrollTo(0,document.body.scrollHeight));
   await page.reload();
   await expect(page.getByRole('heading',{name:heading,exact:true})).toBeAttached();
   await expect.poll(()=>page.evaluate(()=>window.scrollY)).toBe(0);
  }
  expect(mutations).toEqual([]);
 }finally{if(token)await page.request.post('/api/auth/logout',{headers:{Authorization:`Bearer ${token}`}});}
});

test('employee, dossier, control and source-run context survive navigation, reload and back',async({page})=>{
 const password=process.env.INITIAL_ADMIN_PASSWORD;test.skip(!password,'Admin credential required');
 const errors=[];page.on('pageerror',e=>errors.push(e.message));let token;
 try{
  await page.goto('/');await page.getByLabel('Tên đăng nhập').fill(process.env.INITIAL_ADMIN_USERNAME||'admin');
  await page.getByLabel('Mật khẩu').fill(password);await page.getByRole('button',{name:'ĐĂNG NHẬP HỆ THỐNG'}).click();
  await expect(page.getByRole('heading',{name:'Tổng quan đánh giá tuân thủ',exact:true})).toBeVisible();
  token=await page.evaluate(()=>sessionStorage.getItem('iso_team_token'));
  const aid=await page.evaluate(()=>sessionStorage.getItem('iso_team_assessment'));
  const headers={Authorization:`Bearer ${token}`};
  const before=await (await page.request.get(`/api/assessments/${aid}/enterprise/scope56`,{headers})).json();
  await page.getByRole('button',{name:'Doanh nghiệp',exact:true}).click();
  await page.getByRole('button',{name:/^EMP-001 ·/}).click();
  await page.getByRole('button',{name:'Xem hồ sơ liên quan · EMP-001',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Hồ sơ liên quan nhân viên EMP-001',exact:true})).toBeVisible();
  const dossier=await (await page.request.get(`/api/assessments/${aid}/enterprise/shared-work`,{headers})).json();
  const related=dossier.controls.filter(c=>c.evidence.some(e=>e.entity_refs?.employees?.includes('EMP-001')));
  await expect(page.locator('.work-card')).toHaveCount(Math.min(12,related.length));
  if(!related.length)await page.getByLabel('Chỉ control có bằng chứng liên quan nhân viên').uncheck();
  const control=related[0]||dossier.controls[0];
  await page.locator('.work-card').filter({has:page.getByText(control.control_id,{exact:true})}).click();
  await page.getByRole('button',{name:`Tổng quan · ${control.control_id}`,exact:true}).click();
  await expect(page.getByRole('heading',{name:`${control.control_id} · ${control.name}`,exact:true})).toBeVisible();
  expect(new URLSearchParams(new URL(page.url()).hash.slice(1)).get('employee')).toBe('EMP-001');
  expect(new URLSearchParams(new URL(page.url()).hash.slice(1)).get('control')).toBe(control.control_id);
  await page.reload();
  expect(new URLSearchParams(new URL(page.url()).hash.slice(1)).get('control')).toBe(control.control_id);
  await expect(page.getByRole('heading',{name:`${control.control_id} · ${control.name}`,exact:true})).toBeVisible();
  await page.getByRole('button',{name:`Doanh nghiệp · EMP-001`,exact:true}).click();
  await expect(page.getByRole('heading',{name:/^EMP-001 ·/})).toBeVisible();
  await page.goBack();
  await expect(page.getByRole('heading',{name:`${control.control_id} · ${control.name}`,exact:true})).toBeVisible();
  // Use an actual imported capture to verify the scope -> source run -> scope round trip.
  const captured=before.controls.find(c=>c.evidence.some(e=>e.source?.startsWith('a8-capture://')));
  expect(captured,'An imported live capture is needed to test source navigation').toBeTruthy();
  const source=captured.evidence.find(e=>e.source.startsWith('a8-capture://'));
  const rid=source.source.split('://')[1].split('/')[0];
  const hash=new URLSearchParams({view:'scope56',control:captured.control_id,assessment:aid});
  await page.goto('/#'+hash.toString());
  await expect(page.getByRole('heading',{name:`${captured.control_id} · ${captured.name}`,exact:true})).toBeVisible();
  await page.getByRole('button',{name:`Mở lượt A.8 ${rid.slice(0,8)} · ${captured.control_id}`,exact:true}).click();
  await expect(page.getByLabel('Mở lượt đánh giá đã lưu')).toHaveValue(rid);
  await expect(page.getByRole('heading',{name:`Bằng chứng và kết quả · ${captured.control_id}`,exact:true})).toBeVisible();
  await page.reload();
  await expect(page.getByLabel('Mở lượt đánh giá đã lưu')).toHaveValue(rid);
  // Intercept the import write: verify its navigation without importing test data.
  await page.route(`**/a8/runs/${rid}/import-sources`,route=>route.fulfill({json:{inserted:[],reused:['UI-MOCK-NAVIGATION'],skipped_controls:[]}}));
  await page.getByRole('button',{name:'Nhập nguồn live vào hồ sơ 56 (admin)',exact:true}).click();
  await expect(page.getByRole('heading',{name:`${captured.control_id} · ${captured.name}`,exact:true})).toBeVisible();
  await page.getByRole('button',{name:`Mở lượt A.8 ${rid.slice(0,8)} · ${captured.control_id}`,exact:true}).click();
  await expect(page.getByLabel('Mở lượt đánh giá đã lưu')).toHaveValue(rid);
  await page.getByRole('button',{name:`Mở hồ sơ ${captured.control_id}`,exact:true}).click();
  await expect(page.getByRole('heading',{name:`${captured.control_id} · ${captured.name}`,exact:true})).toBeVisible();
  const after=await (await page.request.get(`/api/assessments/${aid}/enterprise/scope56`,{headers})).json();
  expect(after.soa.fingerprint).toBe(before.soa.fingerprint);expect(after.acceptance).toEqual(before.acceptance);
  expect(errors).toEqual([]);
  await page.getByRole('button',{name:'Đăng xuất',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Đăng nhập hệ thống đánh giá',exact:true})).toBeVisible();
  expect(new URL(page.url()).hash).toBe('');
 }finally{if(token)await page.request.post('/api/auth/logout',{headers:{Authorization:`Bearer ${token}`}});}
});
