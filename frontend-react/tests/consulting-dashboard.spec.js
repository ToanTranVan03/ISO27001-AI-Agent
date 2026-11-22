import {test,expect} from '@playwright/test';
import {fileURLToPath} from 'node:url';
process.loadEnvFile(fileURLToPath(new URL('../../.env',import.meta.url)));
test.use({baseURL:process.env.UI_BASE_URL||'http://127.0.0.1:5173',channel:'msedge',headless:true});
test('dashboard UI: role perspectives, unknown cost and actionable control filters without real writes',async({page})=>{
 const data={portfolio:{registered_clients:2,visible_campaigns:3},findings:1,actions:2,by_state:{IN_PROGRESS:1,AWAITING_VERIFICATION:1},due_soon:1,overdue:1,completed:0,completion_percent:0,risk_proposals:{high:1},decisions_pending:56,estimated_cost:null,scope_note:'MOCK workflow counts only, not compliance.',urgent:[{control_id:'A.8.13',finding_id:'f',description:'MOCK backup gap'}],worklist:[{control_id:'A.8.13',name:'Backup',conclusion:'Insufficient Evidence',flags:['missing_sources','awaiting_verification'],findings:1,actions:2,usable_sources:0}]};
 await page.route('**/remediation/dashboard',r=>r.fulfill({json:data}));
 await page.goto('/');await page.getByLabel('Tên đăng nhập',{exact:true}).fill('admin');await page.getByLabel('Mật khẩu',{exact:true}).fill(process.env.INITIAL_ADMIN_PASSWORD);await page.getByRole('button',{name:'ĐĂNG NHẬP HỆ THỐNG'}).click();
 await page.getByText('Tư vấn & khắc phục · từ phát hiện đến xác minh',{exact:true}).click();
 await expect(page.getByRole('heading',{name:'Dashboard tư vấn và khắc phục'})).toBeVisible();
 await expect(page.getByText('Góc nhìn chuyên viên · phân loại rủi ro & vấn đề cần xử lý khẩn cấp')).toBeVisible();
 await page.getByRole('combobox',{name:'Góc nhìn báo cáo',exact:true}).selectOption('business');
 await expect(page.getByText(/Góc nhìn doanh nghiệp · công việc và tiêu chí còn chưa đáp ứng/)).toBeVisible();
 await page.getByRole('combobox',{name:'Góc nhìn báo cáo',exact:true}).selectOption('leadership');await expect(page.getByText('Chi phí dự kiến: Chưa có dữ liệu số tiền; xem nguồn lực trong kế hoạch.',{exact:true})).toBeVisible();
 await page.getByRole('combobox',{name:'Danh sách công việc theo control',exact:true}).selectOption('missing_sources');
 await page.getByRole('button',{name:'A.8.13 · Backup',exact:true}).click();await expect(page).toHaveURL(/control=A.8.13/);
 const token=await page.evaluate(()=>sessionStorage.getItem('iso_team_token'));await page.request.post('/api/auth/logout',{headers:{Authorization:`Bearer ${token}`}});
});
