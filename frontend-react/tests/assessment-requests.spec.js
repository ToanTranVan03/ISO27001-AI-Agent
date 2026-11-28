import {test,expect} from '@playwright/test';
import {fileURLToPath} from 'node:url';
process.loadEnvFile(fileURLToPath(new URL('../../.env',import.meta.url)));
test.use({baseURL:'http://127.0.0.1:5173',channel:'msedge',headless:true});
test('assessment request UI preserves requested scope and cancellation history without running Agent',async({page})=>{
 const rows=[];
 await page.route('**/enterprise/assessment-requests**',async route=>{
  const req=route.request();
  if(req.method()==='POST'){
   const body=req.postDataJSON();
   if(req.url().endsWith('/cancel')){rows[0].version++;rows[0].document.status='CANCELLED';rows[0].document.history.push({event:'cancelled',note:body.note});return route.fulfill({json:rows[0]});}
   expect(body.control_ids).toEqual(['A.6.1']);rows.push({request_id:'ui-test',version:1,document:{...body,status:'REQUESTED',baseline:[],history:[{event:'requested'}]},created_at:'UI MOCK ONLY'});return route.fulfill({status:201,json:rows[0]});
  }
  return route.fulfill({json:{requests:rows,can_create:true,note:'UI MOCK ONLY'}});
 });
 await page.goto('/');await page.getByLabel('Tên đăng nhập',{exact:true}).fill('admin');await page.getByLabel('Mật khẩu',{exact:true}).fill(process.env.INITIAL_ADMIN_PASSWORD);await page.getByRole('button',{name:'ĐĂNG NHẬP HỆ THỐNG'}).click();
 await page.getByText('Yêu cầu đánh giá · lưu mục đích và phạm vi',{exact:true}).click();
 await page.getByLabel('Tên yêu cầu đánh giá',{exact:true}).fill('UI TEST yêu cầu đánh giá');await page.getByLabel('Mục đích và phạm vi yêu cầu',{exact:true}).fill('UI MOCK xem hồ sơ gốc cho kiểm tra nhân sự');await page.getByRole('listbox',{name:/^Control trong yêu cầu/}).selectOption(['A.6.1']);await page.getByLabel('Căn cứ lập yêu cầu',{exact:true}).fill('UI MOCK ONLY, không ghi doanh nghiệp chính');await page.getByRole('button',{name:'Lưu yêu cầu đánh giá',exact:true}).click();
 await expect(page.getByRole('heading',{name:'UI TEST yêu cầu đánh giá',exact:true})).toBeVisible();
 await page.getByLabel('Lý do hủy UI TEST yêu cầu đánh giá',{exact:true}).fill('UI MOCK yêu cầu giữ nguyên lịch sử');await page.getByRole('button',{name:'Hủy yêu cầu, giữ lịch sử',exact:true}).click();await expect(page.getByText(/Đã hủy — giữ lịch sử/)).toBeVisible();
 const token=await page.evaluate(()=>sessionStorage.getItem('iso_team_token'));await page.request.post('/api/auth/logout',{headers:{Authorization:`Bearer ${token}`}});
});
