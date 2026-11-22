import {test,expect} from '@playwright/test';
import {fileURLToPath} from 'node:url';
process.loadEnvFile(fileURLToPath(new URL('../../.env',import.meta.url)));
test.use({baseURL:process.env.UI_BASE_URL||'http://127.0.0.1:5173',channel:'msedge',headless:true,actionTimeout:15000});
test.setTimeout(90000);
test('register UI: source-backed requirements, separate review and source revision invalidates approval',async({page})=>{
 test.skip(!process.env.INITIAL_ADMIN_PASSWORD,'Local admin required');let token,aid;
 const author='11111111-1111-4111-8111-111111111111',reviewer='22222222-2222-4222-8222-222222222222';
 const board={records:[],role:'business_admin',user_id:author,note:'UI MOCK register only, no real requirement'};
 await page.route('**/governance**',async route=>{
  const req=route.request();if(req.method()==='GET')return route.fulfill({json:board});
  const body=req.postDataJSON(),id=new URL(req.url()).pathname.split('/').at(-1);
  if(req.method()==='PUT'){
   const old=board.records.find(r=>r.record_id===id);expect(body.expected_version).toBe(old?.version||0);
   const doc={...body.data,status:'DRAFT',last_editor:author,history:[...(old?.document.history||[]),{event:'edit',note:body.note}]};
   if(old){old.version++;old.document=doc;}else board.records.push({record_id:id,kind:body.kind,version:1,document:doc});
  }else{
   const row=board.records[0];expect(body.expected_version).toBe(row.version);row.version++;row.document.status='ACKNOWLEDGED';row.document.history.push({event:'acknowledge',note:body.note});
  }
  return route.fulfill({json:{mock:true}});
 });
 try{
  await page.goto('/');await page.getByLabel('Tên đăng nhập').fill(process.env.INITIAL_ADMIN_USERNAME||'admin');await page.getByLabel('Mật khẩu').fill(process.env.INITIAL_ADMIN_PASSWORD);await page.getByRole('button',{name:'ĐĂNG NHẬP HỆ THỐNG'}).click();
  await expect(page.getByRole('heading',{name:'Tổng quan đánh giá tuân thủ',exact:true})).toBeVisible();
  ({token,aid}=await page.evaluate(()=>({token:sessionStorage.getItem('iso_team_token'),aid:sessionStorage.getItem('iso_team_assessment')})));
  const path=`/api/assessments/${aid}/enterprise/scope56`,headers={Authorization:`Bearer ${token}`};
  const before=await (await page.request.get(path,{headers})).json();
  await page.getByText('Tư vấn & khắc phục · từ phát hiện đến xác minh',{exact:true}).click();
  await page.getByText('Sổ rủi ro & danh mục yêu cầu có nguồn',{exact:true}).click();
  await page.getByText('Tạo hồ sơ rủi ro hoặc yêu cầu',{exact:true}).click();
  await page.getByRole('combobox',{name:'Loại hồ sơ sổ',exact:true}).selectOption('requirement');
  for(const [name,value] of [['Mã tham chiếu yêu cầu','TEST-REQ-01'],['Tên yêu cầu','UI MOCK internal requirement'],['Nội dung yêu cầu do nhóm cung cấp','Synthetic requirement used for software testing only.'],['Nguồn tài liệu / tham chiếu hợp pháp','SYNTHETIC document reference for test only'],['Phiên bản nguồn','test-v1'],['Căn cứ quyền sử dụng tài liệu','Synthetic content created for this UI test only.'],['Phạm vi liên quan của yêu cầu','UI test only, no real applicability claim'],['Căn cứ tạo/sửa hồ sơ sổ','Synthetic register creation, no professional confirmation']])await page.getByRole('textbox',{name,exact:true}).fill(value);
  await page.getByRole('listbox',{name:'Control liên quan trong phạm vi hiện có',exact:true}).selectOption('A.6.1');
  await page.getByRole('button',{name:'Lưu hồ sơ sổ ở trạng thái nháp',exact:true}).click();
  await expect(page.getByRole('heading',{name:'UI MOCK internal requirement',exact:true})).toBeVisible();
  board.role='consultant';board.user_id=reviewer;await page.getByRole('button',{name:'Làm mới sổ rủi ro/yêu cầu',exact:true}).click();
  const row=page.locator('article').filter({has:page.getByRole('heading',{name:'UI MOCK internal requirement',exact:true})}).last();
  await row.getByRole('textbox',{name:/Căn cứ rà sổ/}).fill('Synthetic separate review of the source and version, not a real legal verification.');
  await row.getByRole('button',{name:'Ghi nhận đã rà sổ',exact:true}).click();
  await expect(row.getByText(/ACKNOWLEDGED/)).toBeVisible();
  await row.getByRole('button',{name:'Sửa sổ, giữ lịch sử',exact:true}).click();
  await page.getByRole('textbox',{name:'Phiên bản nguồn',exact:true}).fill('test-v2');
  await page.getByRole('textbox',{name:'Căn cứ tạo/sửa hồ sơ sổ',exact:true}).fill('Synthetic source version change must reset approval.');
  await page.getByRole('button',{name:'Lưu phiên bản sổ mới',exact:true}).click();
  await expect(row.getByText(/DRAFT/)).toBeVisible();expect(board.records[0].document.history.length).toBe(3);
  const after=await (await page.request.get(path,{headers})).json();expect(after.handoff_packet.sha256).toBe(before.handoff_packet.sha256);
 }finally{if(token)await page.request.post('/api/auth/logout',{headers:{Authorization:`Bearer ${token}`},timeout:10000}).catch(()=>{});}
});
