import {test,expect} from '@playwright/test';
import {fileURLToPath} from 'node:url';

process.loadEnvFile(fileURLToPath(new URL('../../.env',import.meta.url)));
test.use({baseURL:process.env.UI_BASE_URL||'http://127.0.0.1:5173',channel:'msedge',headless:true});
test.setTimeout(60000);
test.afterEach(async({page})=>{
 const token=await page.evaluate(()=>sessionStorage.getItem('iso_team_token')).catch(()=>null);
 if(token)await page.request.post('/api/auth/logout',{headers:{Authorization:`Bearer ${token}`}});
});

// Read-only acceptance against the running application. Never submit labels,
// upload evidence, start inference or approve a real assessment.
for(const [username,key] of [['admin','INITIAL_ADMIN_PASSWORD'],['ledangkhoa','ACCEPTANCE_KHOA_PASSWORD'],['ledoanvantu','ACCEPTANCE_TU_PASSWORD']]){
 test(`${username}: navigation, scope and safe exports`,async({page})=>{
  const password=process.env[key];
  test.skip(!password,`Missing local credential ${key}`);
  const failures=[];
  page.on('pageerror',error=>failures.push(error.message));
  await page.goto('/');
  await page.getByLabel('Tên đăng nhập').fill(username);
  await page.getByLabel('Mật khẩu').fill(password);
  await page.getByRole('button',{name:'ĐĂNG NHẬP HỆ THỐNG'}).click();
  await expect(page.getByRole('heading',{name:'Tổng quan đánh giá tuân thủ',exact:true})).toBeVisible();
  await page.getByText('Quản lý nguồn, tiêu chí và hồ sơ bàn giao',{exact:true}).click();
  await page.getByText('Hồ sơ bàn giao và công cụ quản lý',{exact:true}).click();
  await expect(page.getByRole('heading',{name:'Việc còn thiếu để bàn giao',exact:true})).toBeVisible();
  await page.getByText('Phiếu yêu cầu nguồn theo nhóm phụ trách',{exact:true}).scrollIntoViewIfNeeded();
  await page.getByText(/Rà mức bao phủ nguồn đã có/).click();
  await expect(page.getByRole('button',{name:'Xuất danh sách rà phạm vi'})).toBeVisible();
  await page.getByRole('heading',{name:'Phê duyệt SoA đủ 56 control'}).scrollIntoViewIfNeeded();
  await expect(page.getByRole('button',{name:'Admin phê duyệt SoA toàn phạm vi',exact:true})).toBeDisabled();
  const downloaded=page.waitForEvent('download');
  await page.getByRole('button',{name:'Xuất SoA JSON',exact:true}).click();
  const download=await downloaded;
  const stream=await download.createReadStream();let text='';
  for await(const chunk of stream)text+=chunk.toString();
  const soa=JSON.parse(text);
  expect(soa.entries).toHaveLength(56);
  expect(soa.approval).toBe('DRAFT_NOT_APPROVED');
  if(username==='admin'){
   await page.getByRole('row').filter({has:page.getByText('A.6.2',{exact:true})}).getByRole('button',{name:'Bổ sung',exact:true}).click();
   await expect(page.getByRole('heading',{name:/A\.6\.2 ·/})).toBeVisible();
   await page.getByLabel('Xuất xứ / đơn vị cung cấp').fill('UI rejection test - invalid content, never evidence');
   await page.getByLabel('Chọn bản gốc bằng chứng').setInputFiles({name:'ui-invalid-source.txt',mimeType:'text/plain',buffer:Buffer.from('x')});
   const rejected=page.waitForResponse(r=>r.url().endsWith('/A.6.2/sources/upload')&&r.request().method()==='POST');
   await page.getByRole('button',{name:'Lưu nguồn và bản gốc',exact:true}).click();
   expect((await rejected).status()).toBe(422);
   await expect(page.getByRole('alert').filter({hasText:/./}).first()).toBeVisible();
   await page.getByText('03 · Tính áp dụng & kế hoạch xử lý',{exact:true}).click();
   await page.getByLabel('Tính áp dụng',{exact:true}).selectOption('true');
   await expect(page.getByText(/Kế hoạch còn thiếu:/)).toBeVisible();
   // No decision submitted; a local selection is not an approval.
  }
  await page.getByRole('button',{name:'Doanh nghiệp',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Doanh nghiệp dùng chung',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Hồ sơ ISO',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Hồ sơ & công việc chung',exact:true})).toBeVisible();
  if(username!=='admin')await expect(page.getByRole('button',{name:'Bắt đầu lượt',exact:true})).toHaveCount(0);
  await page.getByRole('button',{name:'Thực nghiệm A.8',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Đánh giá chuyên sâu A.8',exact:true})).toBeVisible();
  if(username==='admin'){
   const token=await page.evaluate(()=>sessionStorage.getItem('iso_team_token'));
   const aid=await page.evaluate(()=>sessionStorage.getItem('iso_team_assessment'));
   const runs=await (await page.request.get(`/api/assessments/${aid}/a8/runs`,{headers:{Authorization:`Bearer ${token}`}})).json();
   const run=runs.find(r=>r.mine&&r.state==='finished');
   expect(run,'A finished coordinator-owned run is needed for read-only UI testing').toBeTruthy();
   await page.getByLabel('Mở lượt đánh giá đã lưu').selectOption(run.run_id);
   await expect(page.getByRole('heading',{name:'Sổ xử lý bất đồng & căn cứ cần rà'})).toBeVisible();
   // Mock this write only: verify the form without adding test notes to real history.
   let submitted;
   await page.route(`**/runs/${run.run_id}/review-followups`,async route=>{
    submitted=route.request().postDataJSON();
    await route.fulfill({status:201,contentType:'application/json',body:JSON.stringify({meaning:'UI_MOCK_ONLY'})});
   });
   await page.getByLabel('Control cần xử lý bất đồng').selectOption({index:1});
   await page.getByLabel('Nội dung đối soát bất đồng').fill('UI mock only: test a coordination note without writing any real review history.');
   await page.getByRole('button',{name:'Lưu biên bản xử lý riêng'}).click();
   await expect(page.getByText('Đã lưu biên bản riêng; nhãn khóa, số liệu đối chiếu và phê duyệt không thay đổi.',{exact:true})).toBeVisible();
   expect(submitted.report_sha256).toMatch(/^[a-f0-9]{64}$/);
   expect(submitted.state).toBe('needs_new_review');
   expect(submitted).not.toHaveProperty('expected');
  }
  expect(failures).toEqual([]);
  await page.getByRole('button',{name:'Đăng xuất',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Đăng nhập hệ thống đánh giá'})).toBeVisible();
 });
}
