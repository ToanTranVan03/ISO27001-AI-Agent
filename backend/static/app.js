const $ = (id) => document.getElementById(id);
const statusLabels = {Compliant: 'Đạt theo quy tắc', 'Partially Compliant': 'Còn thiếu sót', 'Non-Compliant': 'Chưa đạt', 'Insufficient Evidence': 'Thiếu bằng chứng'};
let scenarios = [], enterprise = null, affected = new Set(), busy = false, currentResult = null;
let storyStep = 0;
const goals = {
  baseline: 'Mục tiêu: hiểu doanh nghiệp mẫu và các hồ sơ cần có.',
  training: 'Mục tiêu: biết agent phát hiện ai chưa hoàn tất đào tạo (A.6.3).',
  'new-hire': 'Mục tiêu: kiểm tra NDA trước khi cấp quyền truy cập (A.6.2, A.6.6).',
  offboarding: 'Mục tiêu: liên kết người nghỉ việc với tài khoản và laptop chưa thu hồi (A.6.5).',
  phishing: 'Mục tiêu: kiểm tra nhân viên có biết và thực hiện báo cáo sự kiện (A.6.8).',
  remote: 'Mục tiêu: kiểm tra thiết bị và tài khoản khi làm việc từ xa (A.6.7).'
};
const checkNames = {screened: 'Thẩm tra', terms_signed: 'Cam kết lao động', training_complete: 'Hoàn tất khóa học', training_passed: 'Đạt kiểm tra', disciplinary_informed: 'Biết quy trình xử lý vi phạm', post_employment_ack: 'Cam kết bảo mật sau nghỉ việc', nda_signed: 'Ký NDA', remote_policy_ack: 'Biết chính sách từ xa', reporting_trained: 'Biết cách báo cáo', event_reported: 'Đã báo cáo sự kiện', access_revoked: 'Đã thu hồi quyền', assets_returned: 'Đã trả thiết bị', device_encryption: 'Mã hóa laptop', vpn_mfa: 'MFA cho VPN'};

function problemControls() {
  return currentResult?.controls.filter(c => c.status !== 'Compliant') || [];
}

function fact(title, description) {
  const card = el('div', undefined, 'story-fact'); card.append(el('strong', title), el('p', description)); return card;
}

function setStoryStep(step) {
  if (!currentResult) return;
  storyStep = step;
  const problems = problemControls();
  $('story-steps').hidden = false;
  for (const button of document.querySelectorAll('[data-step]')) {
    if (Number(button.dataset.step) === step) button.setAttribute('aria-current', 'step'); else button.removeAttribute('aria-current');
  }
  $('story-kicker').textContent = `BƯỚC ${step + 1} / 3 · ${currentResult.scenario.name}`;
  $('story-title').textContent = ['Chuyện gì đang xảy ra?', 'Agent kiểm tra bằng chứng nào?', 'Ai cần làm gì tiếp theo?'][step];
  $('story-description').textContent = step === 0 ? currentResult.scenario.description : step === 1 ? 'Agent đối chiếu hồ sơ với quy tắc. Đây là các điểm thiếu sót tìm thấy từ bằng chứng:' : 'Đây là đề xuất cho HR/IT xem xét. Chưa có hành động khắc phục nào được thực hiện trên hệ thống thật.';
  $('story-facts').replaceChildren();
  if (step === 0) {
    $('story-facts').append(fact(`${affected.size} nhân sự cần xem`, affected.size ? 'Áo cam: có phát hiện. Vòng xanh: nhân vật bạn đang điều khiển.' : 'Doanh nghiệp mẫu chưa có phát hiện theo quy tắc diễn tập.'));
  } else if (step === 1) {
    for (const control of problems) {
      const sample = control.findings[0];
      $('story-facts').append(fact(`${control.control_id} · ${control.name}`, sample ? `${control.findings.length} hồ sơ có vấn đề. Ví dụ ${sample.person_id}: ${sample.failed_checks.map(k => checkNames[k] || k).join(', ')} chưa đáp ứng.` : 'Chưa đủ bằng chứng để kết luận.'));
    }
    if (!problems.length) $('story-facts').append(fact('8 kiểm soát đã được đối chiếu', 'Hồ sơ mẫu đáp ứng các quy tắc đơn giản hóa của đồ án.'));
  } else {
    for (const control of problems) $('story-facts').append(fact(control.owner, control.recommended_action));
    if (!problems.length) $('story-facts').append(fact('HR / IT', 'Duy trì kiểm tra định kỳ và lưu hồ sơ.'));
  }
  $('story-back').hidden = step === 0;
  $('story-next').hidden = false;
  $('story-next').textContent = ['Agent kiểm tra gì? →', 'Xem cách xử lý →', 'Xem bằng chứng ↓'][step];
  $('outcome-section').hidden = step !== 2;
  window.dispatchEvent(new CustomEvent('hivefive:guide-step', {detail: {step}}));
}

window.addEventListener('hivefive:person-selected', event => {
  const {person} = event.detail;
  $('story-person').hidden = false; $('story-person').replaceChildren();
  const card = el('div', undefined, 'story-person-card');
  card.append(el('strong', `Đang điều khiển: ${person.id}`), el('p', `${person.name} · ${person.status === 'terminated' ? 'Đã nghỉ việc trong tình huống' : 'Đang làm việc'}`));
  const button = el('button', 'Xem hồ sơ nhân sự');
  button.addEventListener('click', () => {$('people-section').open = true; $('person-detail').scrollIntoView({behavior: 'smooth', block: 'center'});});
  card.append(button); $('story-person').append(card);
});

function updateScene() {
  if (enterprise) window.dispatchEvent(new CustomEvent('hivefive:data', {detail: {
    enterprise, affected: [...affected], scenario: currentResult?.scenario || null,
    controls: currentResult?.controls || []
  }}));
}
window.addEventListener('hivefive:scene-ready', updateScene);

function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

async function request(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === 'string' ? body.detail : `Yêu cầu thất bại (${response.status}).`);
  }
  return response.json();
}

function showError(error) {
  $('error').textContent = error.message || 'Không kết nối được backend. Hãy kiểm tra server và thử lại.';
  $('error').hidden = false;
  $('retry').hidden = false;
}

function renderPeople() {
  if (!enterprise) return;
  const filter = $('department').value;
  $('people').replaceChildren();
  for (const person of enterprise.people.filter(p => !filter || p.department === filter)) {
    const row = el('tr');
    if (affected.has(person.id)) row.className = 'row-affected';
    const name = el('td', person.name); name.append(el('small', person.id)); row.append(name);
    row.append(el('td', person.department));
    row.append(el('td', person.training_complete && person.training_passed ? 'Hoàn tất · đạt' : 'Chưa hoàn tất'));
    row.append(el('td', person.nda_signed ? 'Đã ký' : 'Chưa ký'));
    const accounts = enterprise.accounts.filter(a => a.person_id === person.id);
    const software = el('td', `${accounts.filter(a => a.active).length}/${accounts.length} tài khoản mở`);
    software.append(el('small', accounts.map(a => `${a.system}${a.mfa ? '' : ' (thiếu MFA)'}`).join(' · ')));
    row.append(software);
    const hardware = el('td');
    for (const device of enterprise.devices.filter(d => d.person_id === person.id)) {
      hardware.append(el('div', device.id), el('small', `${device.encrypted ? 'Đã mã hóa' : 'Chưa mã hóa'} · ${device.returned ? 'Đã trả' : 'Đang giữ'}`));
    }
    row.append(hardware);
    const state = el('td', person.status === 'terminated' ? 'Đã nghỉ việc' : 'Đang làm việc');
    if (person.remote) state.append(el('small', 'Làm việc từ xa'));
    if (affected.has(person.id)) state.append(el('small', 'Có phát hiện cần xử lý'));
    row.append(state); $('people').append(row);
  }
}

function renderResult(data) {
  currentResult = data;
  enterprise = data.enterprise;
  affected = new Set(data.controls.flatMap(c => [...c.findings.map(f => f.person_id), ...c.missing_evidence]));
  $('affected-count').textContent = data.summary.affected_people;
  $('affected-note').textContent = `${data.summary.controls_with_findings}/8 kiểm soát có phát hiện`;
  $('result-mode').textContent = data.mode_label;
  $('result-context').textContent = `${data.scenario.name} · ${new Date(data.generated_at).toLocaleString('vi-VN')} · Kết quả theo chính sách mô phỏng.`;
  $('results').replaceChildren();
  $('other-results').replaceChildren();
  const problems = data.controls.filter(c => c.status !== 'Compliant');
  $('other-controls-label').textContent = `${data.controls.length - problems.length} kiểm soát còn lại (thu gọn)`;
  $('other-controls').open = false;
  $('results-title').textContent = problems.length ? `${problems.length} kiểm soát cần xử lý` : 'Chưa có phát hiện theo quy tắc mô phỏng';
  for (const control of data.controls) {
    const section = el('article', undefined, 'control');
    const top = el('div', undefined, 'control-head');
    const title = el('h3'); title.append(el('span', control.control_id, 'control-id'), document.createTextNode(control.name));
    top.append(title, el('span', statusLabels[control.status] || control.status, `badge${control.status === 'Compliant' ? '' : ' warn'}`));
    section.append(top, el('p', control.rationale, 'muted'));
    if (control.findings.length || control.missing_evidence.length) {
      const action = el('div', undefined, 'action');
      action.append(el('p', `Ưu tiên ${control.priority.toLowerCase()} · Phụ trách: ${control.owner}`), el('p', control.recommended_action));
      const people = [...new Set([...control.findings.map(f => f.person_id), ...control.missing_evidence])];
      action.append(el('p', `Hồ sơ cần xem: ${people.join(', ')}`)); section.append(action);
    }
    const details = el('details');
    const problemIds = new Set([...control.findings.map(f => f.person_id), ...control.missing_evidence]);
    const records = problemIds.size ? control.evidences.filter(e => problemIds.has(e.person_id)) : control.evidences.slice(0, 5);
    details.append(el('summary', `Bằng chứng: ${records.length} hồ sơ${problemIds.size ? ' liên quan' : ` mẫu / ${control.evidences.length}`}`));
    const table = el('table', undefined, 'evidence-table');
    for (const record of records) {
      const row = el('tr'), checks = control.findings.find(f => f.person_id === record.person_id)?.failed_checks || [];
      row.append(el('th', record.person_id), el('td', checks.length ? checks.map(k => `${checkNames[k] || k}: chưa đáp ứng`).join('; ') : 'Hồ sơ đã đối chiếu'));
      table.append(row);
    }
    details.append(table);
    const technical = el('details'); technical.append(el('summary', 'Dữ liệu kỹ thuật (JSON)'));
    // Text rendering keeps evidence/model content inert in the browser.
    const pre = el('pre');
    technical.addEventListener('toggle', () => {
      if (technical.open && !pre.textContent) pre.textContent = JSON.stringify(control.evidences, null, 2);
    });
    technical.append(pre); details.append(technical); section.append(details);
    (control.status === 'Compliant' ? $('other-results') : $('results')).append(section);
  }
  $('ai-section').hidden = !data.ai_explanation;
  $('ai-text').textContent = data.ai_explanation || '';
  $('trace-section').hidden = false;
  $('trace').replaceChildren(...data.audit_trail.map(step => el('li', step)));
  $('people-context').textContent = `Hồ sơ trong tình huống: ${data.scenario.name}. Hàng có nền vàng là nhân sự có phát hiện.`;
  renderPeople(); updateScene();
  $('pending-scenario').hidden = true;
  setStoryStep(0);
}

async function loadCatalog() {
  $('error').hidden = true; $('retry').hidden = true;
  try {
    const data = await request('/api/simulation');
    if (!currentResult) enterprise = data.enterprise;
    scenarios = data.scenarios;
    $('scenario').replaceChildren(...scenarios.map(s => {
      const option = el('option', s.name); option.value = s.id; return option;
    }));
    $('scenario').value = 'training';
    $('people-count').textContent = enterprise.people.length;
    $('account-count').textContent = enterprise.accounts.length;
    $('device-count').textContent = enterprise.devices.length;
    $('scenario').disabled = false; $('run').disabled = false;
    updateDescription(); renderPeople(); updateScene();
  } catch (error) { showError(error); }
}

function updateDescription() {
  $('scenario-description').textContent = scenarios.find(s => s.id === $('scenario').value)?.description || '';
  $('scenario-goal').textContent = goals[$('scenario').value] || '';
  $('pending-scenario').hidden = !currentResult || currentResult.scenario.id === $('scenario').value;
}

async function run() {
  if (busy) return;
  busy = true; $('error').hidden = true; $('retry').hidden = true;
  $('run').disabled = true; $('scenario').disabled = true; $('mode').disabled = true;
  $('results').setAttribute('aria-busy', 'true');
  $('progress').textContent = $('mode').value === 'ai' ? 'Đang kiểm tra bằng chứng và chờ Ollama giải thích (tối đa khoảng 60 giây)…' : 'Đang thu thập và đối chiếu bằng chứng…';
  try {
    const data = await request('/api/simulation/run', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({scenario_id: $('scenario').value, mode: $('mode').value})});
    renderResult(data); $('progress').textContent = 'Đã hoàn tất mô phỏng.';
  } catch (error) {
    showError(error); $('progress').textContent = 'Lần chạy chưa hoàn tất. Kết quả đang hiển thị (nếu có) thuộc lần chạy trước.';
  } finally {
    busy = false; $('run').disabled = false; $('scenario').disabled = false; $('mode').disabled = false;
    $('results').setAttribute('aria-busy', 'false');
  }
}

$('scenario').addEventListener('change', updateDescription);
$('department').addEventListener('change', renderPeople);
$('run').addEventListener('click', run);
$('retry').addEventListener('click', () => scenarios.length ? run() : loadCatalog());
for (const button of document.querySelectorAll('[data-step]')) button.addEventListener('click', () => setStoryStep(Number(button.dataset.step)));
$('story-back').addEventListener('click', () => setStoryStep(Math.max(0, storyStep - 1)));
$('story-next').addEventListener('click', () => {
  if (storyStep < 2) setStoryStep(storyStep + 1);
  else $('outcome-section').scrollIntoView({behavior: 'smooth', block: 'start'});
});
loadCatalog();
