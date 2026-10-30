// Run with NODE_PATH pointing to an installed Playwright package directory.
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');

let browser;
(async () => {
  browser = await chromium.launch({headless: true, channel: 'msedge'});
  const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('http://127.0.0.1:8000/simulation');
  await page.waitForFunction(() => document.getElementById('people-count').textContent === '50');
  await page.waitForFunction(() => document.getElementById('scene-status').dataset.ready === 'true', {timeout: 30000});
  assert.equal(await page.locator('#campus-canvas canvas').count(), 1);
  assert.equal(await page.locator('#people tr').count(), 50);
  await page.locator('.simulation-notes > summary').click();
  await page.locator('#manual-simulation > summary').click();
  await page.selectOption('#scenario', 'training');
  assert.equal(await page.locator('#outcome-section').isVisible(), false);
  assert.equal(await page.locator('#people-section').getAttribute('open'), null);
  await page.getByRole('button', {name: 'Bắt đầu diễn tập'}).click();
  await page.getByText('Đã hoàn tất mô phỏng.', {exact: true}).waitFor();
  assert.equal(await page.locator('#affected-count').textContent(), '8');
  assert.equal(await page.locator('.control').count(), 8);
  assert.equal(await page.locator('.row-affected').count(), 8);
  assert.equal(await page.locator('#scene-status').getAttribute('data-affected'), '8');
  assert.equal(await page.locator('#outcome-section').isVisible(), false);
  assert.match(await page.locator('#story-title').innerText(), /Chuyện gì/);
  await page.getByRole('button', {name: 'Agent kiểm tra gì?'}).click();
  assert.match(await page.locator('#story-facts').innerText(), /A.6.3/);
  await page.getByRole('button', {name: 'Xem cách xử lý'}).click();
  assert.equal(await page.locator('#outcome-section').isVisible(), true);
  assert.equal(await page.locator('#results > .control').count(), 1);
  assert.equal(await page.locator('#other-controls').getAttribute('open'), null);
  await page.locator('#people-section > summary').click();
  await page.selectOption('#person-select', 'HF-050');
  assert.match(await page.locator('#person-detail').innerText(), /Chưa hoàn tất/);
  assert.match(await page.locator('#person-detail').innerText(), /LT-050/);
  await page.locator('.camera-options > summary').click();
  await page.getByRole('button', {name: 'Nội thất: tắt', exact: true}).click();
  await page.getByRole('button', {name: 'Nội thất: bật', exact: true}).click();
  await page.locator('.camera-options > summary').click();
  // Keyboard movement changes the selected avatar, without changing audit data.
  await page.locator('#campus-canvas').focus();
  const before = await page.locator('#campus-canvas').evaluate(el => ({x: +el.dataset.personX, z: +el.dataset.personZ}));
  await page.keyboard.down('KeyS');
  await page.waitForFunction(before => {
    const el = document.getElementById('campus-canvas');
    return Math.hypot(+el.dataset.personX - before.x, +el.dataset.personZ - before.z) > .08;
  }, before);
  await page.keyboard.up('KeyS');
  assert.equal(await page.locator('#affected-count').textContent(), '8');
  await page.waitForFunction(() => document.getElementById('campus-canvas').dataset.cameraMoving === 'false');
  // Use visible open-floor positions to exercise picking and click-to-walk.
  const bounds = await page.locator('#campus-canvas').boundingBox();
  let clickedFloor = false;
  for (const [x, y] of [[.62, .70], [.55, .75], [.70, .55], [.48, .85]]) {
    await page.mouse.click(bounds.x + bounds.width * x, bounds.y + bounds.height * y);
    if ((await page.locator('#movement-status').innerText()).includes('đang đi tới')) {clickedFloor = true; break;}
  }
  assert.equal(clickedFloor, true, 'Clicking open floor starts a route');
  await page.waitForFunction(() => document.getElementById('campus-canvas').dataset.moving === 'true');
  await page.getByRole('button', {name: 'Xem tòa nhà', exact: true}).click();
  await page.getByRole('button', {name: 'Về phòng diễn tập', exact: true}).click();
  await page.selectOption('#department', 'Sales');
  assert.equal(await page.locator('#people tr').count(), 15);
  await page.locator('#results .control > details > summary').click();
  assert.equal(await page.locator('#results .evidence-table tr').count(), 8);

  for (const width of [320, 768, 1024, 1440]) {
    await page.setViewportSize({width, height: 1000});
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), `Horizontal page overflow at ${width}px`);
  }
  await page.setViewportSize({width: 1440, height: 1000});
  await page.waitForFunction(() => document.getElementById('campus-canvas').dataset.cameraMoving === 'false');
  await page.locator('.campus-section').screenshot({path: path.join(__dirname, '..', 'docs', 'charts', 'hivefive-office-guided.png')});

  // Validate error recovery.
  await page.route('**/api/simulation/run', route => route.fulfill({status: 503, contentType: 'application/json', body: JSON.stringify({detail: 'Ollama chưa sẵn sàng. Chọn Quy tắc để chạy lại.'})}));
  await page.locator('.mode-options > summary').click();
  await page.selectOption('#mode', 'ai');
  await page.getByRole('button', {name: 'Bắt đầu diễn tập'}).click();
  await page.locator('#error').waitFor({state: 'visible'});
  assert.match(await page.locator('#error').innerText(), /Ollama/);
  await page.unroute('**/api/simulation/run');
  await page.selectOption('#mode', 'rules');
  await page.getByRole('button', {name: 'Thử lại', exact: true}).click();
  await page.getByText('Đã hoàn tất mô phỏng.', {exact: true}).waitFor();
  assert.equal(await page.locator('#error').isVisible(), false);
  assert.deepEqual(errors, []);
  console.log('Browser passed: guided 3-step scenario, one room, collapsed details, WASD movement, floor click-to-walk, building overview, 8 highlights/evidence rows, responsive widths, error recovery; no page errors.');
  await browser.close();
})().catch(async error => {console.error(error); await browser?.close(); process.exitCode = 1;});
