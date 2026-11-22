import {test,expect} from '@playwright/test';
import {fileURLToPath} from 'node:url';
process.loadEnvFile(fileURLToPath(new URL('../../.env',import.meta.url)));
test.use({baseURL:process.env.UI_BASE_URL||'http://127.0.0.1:5173',channel:'msedge',headless:true});
test('client forms UI: create and edit versioned profile without main campaign mutations',async({page})=>{
 let client=null,posts=0;
 await page.route('**/api/clients**',async route=>{
  const req=route.request();
  if(req.method()==='POST'){
   const body=req.postDataJSON();expect(body.expected_version).toBe(0);expect(body.campaign.isms_scope).toContain('MOCK');posts++;
   client={client_id:'mock-client',name:body.name,profile:{name:body.name,sector:body.sector,contact:body.contact,locations:body.locations},version:1,campaigns:[{assessment_id:'mock-assessment',name:body.campaign.name}]};return route.fulfill({status:201,json:{client_id:client.client_id,version:1,campaign:client.campaigns[0]}});
  }
  if(req.method()==='PUT'){const body=req.postDataJSON();expect(body.expected_version).toBe(1);client={...client,name:body.name,profile:body,version:2};return route.fulfill({json:{version:2}});}
  return route.fulfill({json:{clients:client?[client]:[],can_manage:true}});
 });
 await page.goto('/');await page.getByLabel('Tên đăng nhập',{exact:true}).fill('admin');await page.getByLabel('Mật khẩu',{exact:true}).fill(process.env.INITIAL_ADMIN_PASSWORD);await page.getByRole('button',{name:'ĐĂNG NHẬP HỆ THỐNG'}).click();await page.getByRole('button',{name:'Doanh nghiệp',exact:true}).click();
 await page.getByText('Khách hàng tư vấn · doanh nghiệp và các đợt riêng',{exact:true}).click();
 for(const [name,value] of [['Tên khách hàng','MOCK client'],['Lĩnh vực khách hàng','MOCK sector'],['Người liên hệ khách hàng','MOCK contact'],['Tên đợt đầu tiên','MOCK assessment'],['Phạm vi ISMS của đợt','MOCK one isolated service and authorized users']])await page.getByRole('textbox',{name,exact:true}).fill(value);
 await page.getByRole('button',{name:'Lưu khách hàng',exact:true}).click();await expect(page.getByRole('heading',{name:'MOCK client · v1',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Sửa khách hàng MOCK client',exact:true}).click();await page.getByRole('textbox',{name:'Tên khách hàng',exact:true}).fill('MOCK client revised');await page.getByRole('button',{name:'Lưu khách hàng',exact:true}).click();await expect(page.getByRole('heading',{name:'MOCK client revised · v2',exact:true})).toBeVisible();expect(posts).toBe(1);
 const token=await page.evaluate(()=>sessionStorage.getItem('iso_team_token'));await page.request.post('/api/auth/logout',{headers:{Authorization:`Bearer ${token}`}});
});
