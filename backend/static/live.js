/* Reading the dashboard never requests an audit: the server consumes business events. */
let liveRevision = -1, liveState = null, submittingEvent = false;
function businessActionOptions(actions) {
  const groups = new Map();
  for (const action of actions) {
    const name = action.id.startsWith('training_') ? 'Đào tạo và nguồn bằng chứng' : action.id.startsWith('retention_') ? 'Ngoại lệ bàn giao' : action.id.startsWith('remote_') ? 'Làm việc từ xa' : action.id === 'advance_day' ? 'Thời gian mô phỏng' : 'Nhân sự, hồ sơ và quyền truy cập';
    if (!groups.has(name)) {const group = el('optgroup'); group.label = name; groups.set(name, group);}
    const option = el('option', action.name); option.value = action.id; groups.get(name).append(option);
  }
  return [...groups.values()];
}
const repairActions = {'A.6.1': 'screening_complete', 'A.6.2': 'nda_signed', 'A.6.3': 'training_complete', 'A.6.4': 'discipline_complete', 'A.6.5': 'recover_access', 'A.6.6': 'nda_signed', 'A.6.7': 'remote_protected', 'A.6.8': 'report_complete'};
const evidenceLabels = {status: 'Trạng thái lao động', active: 'Tài khoản đang mở', returned: 'Đã bàn giao laptop', encrypted: 'Laptop đã mã hóa', mfa: 'MFA', remote: 'Làm việc từ xa', employment_status_known: 'Biết trạng thái lao động', remote_status_known: 'Biết trạng thái từ xa', active_accounts: 'Tài khoản còn mở', unreturned_devices: 'Thiết bị chưa trả', asset_inventory_complete: 'Có danh mục tài sản', disciplinary_process: 'Có quy trình xử lý vi phạm', reporting_channel: 'Có kênh báo cáo'};
function evidenceValue(value) {
  if (value === null || value === undefined) return 'Chưa xác minh';
  if (value === true) return 'Có / Đạt';
  if (value === false) return 'Không / Chưa đạt';
  if (Array.isArray(value)) return value.length ? value.map(evidenceValue).join(' / ') : 'Không còn';
  if (typeof value === 'object') return Object.entries(value).map(([key, item]) => `${evidenceLabels[key] || key}: ${evidenceValue(item)}`).join('; ');
  return ({active: 'Đang làm việc', terminated: 'Đã nghỉ việc'})[value] || String(value);
}

function renderTriad(person, accounts, devices, state) {
  const container = $('case-triad');
  if (!container) return;
  const triadData = state.triad;
  const personRisks = (triadData?.cross_entity_risks || []).filter(r => r.person_id === person.id);
  
  const wrap = el('div', undefined, 'triad-wrapper');
  const header = el('div', undefined, 'triad-header');
  header.append(
    el('strong', 'Mô hình Tam giác ATTT · Con người (Trọng tâm) ↔ Phần mềm ↔ Phần cứng'),
    el('span', personRisks.length ? `⚠️ ${personRisks.length} rủi ro lan truyền đa thực thể` : '✅ Liên kết thực thể đạt chuẩn', personRisks.length ? 'risk-badge-warn' : 'risk-badge-ok')
  );
  
  const grid = el('div', undefined, 'triad-grid');
  
  const colPeople = el('div', undefined, 'triad-col people-col');
  colPeople.append(
    el('h4', '👤 1. Con người (Trọng tâm A.6)'),
    el('p', `Phòng ban: ${person.department} · Vai trò: ${person.role || 'Nhân viên'}`),
    el('p', `Trạng thái: ${evidenceValue(person.status)}`),
    el('p', `Đào tạo ATTT: ${evidenceValue(person.training_passed)}`),
    el('p', `Cam kết NDA: ${evidenceValue(person.nda_signed)}`)
  );
  
  const activeAccs = accounts.filter(a => a.active);
  const colSoftware = el('div', undefined, 'triad-col software-col');
  colSoftware.append(
    el('h4', '💻 2. Phần mềm & IAM (A.8)'),
    el('p', `Tài khoản mở: ${activeAccs.length}/${accounts.length}`),
    el('p', `Danh mục: ${accounts.map(a => `${a.system}${a.active ? '' : ' (đóng)'}`).join(', ')}`),
    el('p', `MFA VPN: ${evidenceValue(accounts.find(a => a.system === 'VPN')?.mfa)}`),
    el('p', `Rà soát quyền: ${person.access_review_required ? (accounts.every(a => a.role_reviewed) ? 'Đã rà soát' : 'Chưa hoàn tất') : 'Không yêu cầu'}`)
  );
  
  const unreturned = devices.filter(d => !d.returned);
  const unencrypted = devices.filter(d => !d.encrypted);
  const colHardware = el('div', undefined, 'triad-col hardware-col');
  colHardware.append(
    el('h4', '🛡️ 3. Phần cứng & Thiết bị (A.7/A.8.1)'),
    el('p', `Thiết bị: ${devices.map(d => d.id).join(', ') || 'Không có'}`),
    el('p', `Bàn giao laptop: ${unreturned.length ? 'Đang giữ laptop' : 'Đã thu hồi đủ'}`),
    el('p', `Mã hóa BitLocker: ${unencrypted.length ? 'Chưa mã hóa' : 'Đã mã hóa'}`),
    el('p', `Làm từ xa: ${person.remote ? 'Có mang máy ra ngoài' : 'Làm tại văn phòng'}`)
  );
  
  grid.append(colPeople, colSoftware, colHardware);
  wrap.append(header, grid);
  
  if (personRisks.length) {
    const riskBox = el('div', undefined, 'triad-risk-box');
    riskBox.append(el('strong', 'Chuỗi rủi ro lan truyền liên thực thể:'));
    for (const r of personRisks) {
      const item = el('div', undefined, 'triad-risk-item');
      item.append(
        el('span', `[${r.risk.risk_level}] ${r.title} (Điểm rủi ro CIA: ${r.risk.risk_score}/25)`, 'risk-title'),
        el('p', `${r.detail} (Kiểm soát liên đới: ${r.controls.join(', ')})`, 'risk-detail')
      );
      if (r.iso_guidance) {
        item.append(
          el('p', `📖 Tiêu chuẩn ISO: ${r.iso_guidance.regulatory_rationale}`, 'iso-citation'),
          el('p', `🛠️ Khuyến nghị xử lý: ${(r.iso_guidance.actionable_steps || []).join(' ')}`, 'context-advice')
        );
      }
      riskBox.append(item);
    }
    wrap.append(riskBox);
  }
  container.replaceChildren(wrap);
}

function renderDossier() {
  if (!liveState) return;
  const state = liveState, pid = $('business-person').value;
  const person = state.enterprise.people.find(p => p.id === pid);
  if (!person) return;
  const events = state.events.filter(e => e.person_id === pid), event = events[0];
  const issues = state.controls.filter(c => c.findings.some(f => f.person_id === pid) || c.missing_evidence.includes(pid));
  const verified = state.status === 'complete' && state.report?.trigger_revision === state.revision;
  const accounts = state.enterprise.accounts.filter(a => a.person_id === pid);
  const devices = state.enterprise.devices.filter(d => d.person_id === pid);
  $('case-title').textContent = `${pid} · ${person.department}`;
  $('scene-case-title').textContent = `${pid} · ${evidenceValue(person.status)}`;
  $('scene-case-detail').textContent = `${accounts.filter(a => a.active).length} tài khoản mở · ${devices.filter(d => !d.returned).length} laptop đang giữ`;
  const retained = state.controls.find(c => c.control_id === 'A.6.5')?.evidences.find(e => e.person_id === pid)?.content.approved_retained_accounts || [];
  $('scene-case-issue').textContent = issues.length ? issues.map(c => `${c.control_id}${c.missing_evidence.includes(pid) ? ' · Thiếu bằng chứng' : ' · Cần xử lý'}`).join(' / ') : retained.length ? `${retained.length} tài khoản giữ theo ngoại lệ còn hạn` : '8 kiểm soát · Chưa có phát hiện';
  $('case-summary').textContent = `Ngày mô phỏng ${state.enterprise.assessment_date || '2026-10-30'} · ${evidenceValue(person.status)} · ${accounts.filter(a => a.active).length}/${accounts.length} tài khoản mở · ${devices.filter(d => !d.returned).length} laptop đang giữ · ${issues.length} kiểm soát cần xem xét.`;
  const stages = [
    ['01 · Sự việc', event ? `Đã nhận phiên bản ${event.revision}` : 'Chưa có sự kiện trong nhật ký gần nhất'],
    ['02 · Đối chiếu', issues.length ? `${issues.length} kiểm soát có phát hiện / thiếu dữ liệu` : 'Chưa có phát hiện theo quy tắc'],
    ['03 · AI xác minh', verified ? 'Đã xác minh snapshot hiện tại' : state.status === 'failed' ? 'Chưa hoàn tất · xem lỗi bên dưới' : state.status === 'watching' ? 'Đang chờ sự kiện' : 'Đang chờ / xử lý snapshot mới'],
    ['04 · Khắc phục', issues.length ? 'Cần cập nhật bằng chứng và tái kiểm tra' : verified && event ? 'Đã tái kiểm tra · hết phát hiện' : 'Chưa cần khắc phục theo quy tắc']
  ];
  $('case-lifecycle').replaceChildren(...stages.map(([title, description]) => {
    const item = el('li'); item.append(el('strong', title), el('span', description)); return item;
  }));
  renderTriad(person, accounts, devices, state);
  $('case-event').textContent = event ? `${new Date(event.created_at).toLocaleString('vi-VN')} · ${state.actions.find(a => a.id === event.action)?.name}` : 'Chọn thao tác nghiệp vụ để tạo sự việc.';
  const table = el('table'), head = el('thead'), tr = el('tr'), body = el('tbody');
  for (const label of ['Bản ghi / bằng chứng', 'Trước', 'Sau']) tr.append(el('th', label));
  head.append(tr); table.append(head, body);
  for (const change of event?.changes || []) {
    const row = el('tr'); row.append(el('th', `${change.record_id} · ${checkNames[change.field] || evidenceLabels[change.field] || change.field}`), el('td', evidenceValue(change.before)), el('td', evidenceValue(change.after))); body.append(row);
  }
  $('case-changes').replaceChildren(event?.changes?.length ? table : el('p', 'Chưa có dữ liệu thay đổi trước/sau.'));
  $('case-controls').replaceChildren(...state.controls.map(control => {
    const record = control.evidences.find(e => e.person_id === pid);
    const failed = control.findings.some(f => f.person_id === pid), missing = control.missing_evidence.includes(pid);
    const detail = el('details', undefined, `case-control${failed || missing ? ' needs-action' : ''}`);
    detail.open = failed || missing;
    detail.append(el('summary', `${control.control_id} · ${missing ? (failed ? 'Có vấn đề và thiếu bằng chứng' : 'Thiếu bằng chứng') : failed ? 'Chưa đáp ứng quy tắc' : 'Đạt theo bằng chứng'}`));
    detail.append(el('p', control.name));
    const list = el('ul');
    for (const [key, value] of Object.entries(record?.content || {})) if (key !== 'context_recommendation') list.append(el('li', `${checkNames[key] || evidenceLabels[key] || key}: ${evidenceValue(value)}`));
    detail.append(list, el('small', `${record?.evidence_id || 'Chưa có bằng chứng'} · SHA-256 ${record?.sha256.slice(0, 12) || '—'}`));
    const citation = (state.triad?.iso_citations || {})[control.control_id];
    if (citation) detail.append(el('p', `Tiêu chuẩn: ${citation.clause} — ${citation.guidance}`, 'iso-citation'));
    if (!failed && !missing && record?.content.context_recommendation) detail.append(el('p', record.content.context_recommendation, 'context-advice'));
    if (record?.content.approved_retained_accounts?.length) {detail.append(el('p', 'Ngoại lệ có điều kiện đang áp dụng; tiếp tục theo dõi thời hạn.')); detail.open = true;}
    if (failed || missing) {
      detail.append(el('p', `${control.owner} · ${missing ? 'Cần bổ sung nguồn xác minh. ' : ''}${record?.content.context_recommendation || control.recommended_action}`));
      if (control.control_id !== 'A.6.5' || person.status === 'terminated' || person.access_review_required) {
        const action = control.control_id === 'A.6.5' && person.status === 'active' ? 'role_review' : repairActions[control.control_id];
        const button = el('button', action === 'role_review' ? 'Ghi nhận đã rà soát quyền theo vai trò mới' : 'Ghi nhận khắc phục trong mô phỏng', 'secondary');
        button.type = 'button'; button.disabled = submittingEvent;
        button.addEventListener('click', () => submitBusinessChange(pid, action)); detail.append(button);
      }
    }
    return detail;
  }));
  $('scene-scenario').textContent = `${pid} · ${issues.length ? `${issues.length} kiểm soát cần xử lý` : 'Chưa có phát hiện'}`;
  $('scene-help').textContent = event ? `${state.actions.find(a => a.id === event.action)?.name} · Xem hồ sơ sự việc bên dưới` : 'Chọn nhân vật · Bấm sàn để đi · WASD / phím mũi tên';
}
const liveToolNames = {read_people: 'Đọc hồ sơ nhân sự', read_assets: 'Liên kết tài khoản và laptop', assess_people: 'Đối chiếu kiểm soát A.6', inspect_offboarding: 'Kiểm tra sâu bàn giao khi nghỉ việc', inspect_remote: 'Kiểm tra sâu làm việc từ xa', check_scope: 'Kiểm tra phạm vi', create_tasks: 'Cập nhật công việc cần xử lý', verify_report: 'Xác minh báo cáo và bằng chứng'};
Object.assign(liveToolNames, {inspect_context: 'Kiểm tra thời hạn, nguồn mâu thuẫn và ngoại lệ'});
Object.assign(evidenceLabels, {training_valid_until:'Đào tạo có hiệu lực đến', training_current:'Đào tạo còn hiệu lực', assessment_date:'Ngày đối chiếu', lms_training_passed:'Kết quả từ LMS', training_source_agreement:'HR/LMS thống nhất', training_source_comparison:'Đối chiếu hai nguồn', source_resolution:'Yêu cầu đối soát', role_access_reviewed:'Đã rà soát quyền theo vai trò', role_reviewed:'Đã rà soát quyền tài khoản', access_review_required:'Cần rà soát quyền khi đổi vai trò', current_role:'Vai trò hiện tại', role:'Vai trò', retention_exception:'Ngoại lệ giữ tài khoản', retention_exception_records:'Căn cứ ngoại lệ', approved_retained_accounts:'Tài khoản được giữ có điều kiện', approved:'Đã phê duyệt', approver:'Người duyệt', reason:'Lý do', expires_on:'Hết hạn ngày', account_id:'Tài khoản áp dụng', scope:'Phạm vi', valid:'Hồ sơ ngoại lệ hợp lệ', applied:'Đang áp dụng', context_recommendation:'Cách xử lý theo ngữ cảnh'});

function displayLive(state) {
  if (liveState && liveState.revision === state.revision && liveState.status === state.status && liveState.progress.length === state.progress.length && liveState.error === state.error) return;
  liveState = state;
  const changed = liveRevision !== state.revision;
  if (changed) {
    liveRevision = state.revision;
    const selected = $('business-person').value;
    const selectedAction = $('business-action').value;
    $('business-person').replaceChildren(...state.enterprise.people.map(p => {
      const option = el('option', `${p.id} · ${p.name}`); option.value = p.id; return option;
    }));
    if (selected) $('business-person').value = selected;
    $('business-action').replaceChildren(...businessActionOptions(state.actions));
    if (selectedAction) $('business-action').value = selectedAction;
    const controls = state.controls;
    const affectedIds = new Set(controls.flatMap(c => [...c.findings.map(f => f.person_id), ...c.missing_evidence]));
    const last = state.events[0];
    renderResult({enterprise: state.enterprise, controls,
      summary: {affected_people: affectedIds.size, controls_with_findings: controls.filter(c => c.findings.length).length},
      scenario: {id: 'live', name: 'Doanh nghiệp đang vận hành', description: last ? `${last.person_id}: ${state.actions.find(a => a.id === last.action)?.name}` : 'Chưa có sự kiện. Cập nhật một hồ sơ để Agent tự phát hiện thay đổi.'},
      generated_at: last?.created_at || new Date().toISOString(), mode_label: 'Phát hiện tự động theo bằng chứng', audit_trail: []});
    $('story-steps').hidden = true; $('story-back').hidden = true; $('story-next').hidden = true;
    $('story-kicker').textContent = 'DOANH NGHIỆP / ĐANG VẬN HÀNH';
    $('story-title').textContent = last ? 'Sự việc đã được ghi nhận' : 'Bạn điều hành. Agent theo dõi.';
    $('story-description').textContent = currentResult.scenario.description;
    $('story-facts').replaceChildren(fact(`${affectedIds.size} nhân sự cần xử lý`, 'Áo cam đánh dấu hồ sơ có phát hiện. Chọn nhân vật để cập nhật nghiệp vụ; kết quả tự xuất hiện tại Trạm giám sát.'));
    for (const [id, value] of [['people-count', state.enterprise.people.length], ['account-count', state.enterprise.accounts.length], ['device-count', state.enterprise.devices.length]]) $(id).textContent = value;
    $('business-events').replaceChildren(...state.events.map(event => el('li', `${new Date(event.created_at).toLocaleTimeString('vi-VN')} · ${event.person_id} · ${state.actions.find(a => a.id === event.action)?.name}`)));
    if (!last) $('business-events').append(el('li', 'Chưa có thay đổi nghiệp vụ.'));
    $('live-evidence').textContent = `Nguồn HIVEFIVE-LIVE · Phiên bản ${state.revision} · SHA-256 ${state.snapshot_hash.slice(0, 12)} · A.6.1–A.6.8`;
    if (last) window.dispatchEvent(new CustomEvent('hivefive:focus-person', {detail: {id: last.person_id}}));
  }
  const statuses = {watching: 'Đang quan sát', pending: 'Đã nhận thay đổi', processing: 'AI đang kiểm tra sâu', complete: 'Đã xác minh', failed: 'AI chưa hoàn tất'};
  $('live-state-badge').textContent = statuses[state.status] || state.status;
  const currentReport = state.report?.trigger_revision === state.revision ? state.report : null;
  const problems = state.controls.filter(c => c.status !== 'Compliant');
  $('live-findings').replaceChildren();
  if (!problems.length) {
    $('live-findings').append(fact(state.revision ? 'Không còn phát hiện theo quy tắc' : 'Hồ sơ ban đầu đầy đủ theo quy tắc', state.revision ? 'Bằng chứng hiện tại đã được đối chiếu lại tự động. Xem trạng thái xác minh AI bên trên.' : 'Thử ghi nhận nghỉ việc khi tài khoản còn mở. Agent sẽ tự nhận sự kiện.'));
  }
  for (const control of problems) {
    const card = el('article', undefined, 'live-finding');
    card.append(el('span', control.control_id, 'control-id'), el('h3', control.name), el('p', statusLabels[control.status] || control.status, 'live-verdict'));
    const evidence = [...control.findings.map(f => `${f.person_id}: ${f.failed_checks.map(k => `${checkNames[k] || k}: chưa đáp ứng`).join(', ')}`), ...control.missing_evidence.map(id => `${id}: thiếu bằng chứng`)];
    if (control.control_id === 'A.6.5') {
      const ids = new Set(control.findings.map(f => f.person_id));
      evidence.push(`${state.enterprise.accounts.filter(a => ids.has(a.person_id) && a.active).length} tài khoản còn mở; ${state.enterprise.devices.filter(d => ids.has(d.person_id) && !d.returned).length} laptop chưa bàn giao.`);
    }
    card.append(el('p', evidence.join('; ')), fact(`Cách xử lý · ${control.owner}`, control.recommended_action));
    $('live-findings').append(card);
  }
  $('live-status').textContent = state.status === 'watching' ? 'Đang chờ sự kiện nghiệp vụ. Không cần khởi chạy kiểm tra.' : state.status === 'complete' ? `Agent đã tự kiểm tra phiên bản ${state.processed_revision}. ${currentReport?.verified_clear_tasks.length || 0} công việc đã hết phát hiện trong mô phỏng.` : state.status === 'failed' ? `Đối chiếu quy tắc đã hiển thị. AI chưa hoàn tất: ${state.error}` : state.active_revision && state.active_revision < state.revision ? `AI đang xác minh phiên bản ${state.active_revision}; phiên bản ${state.revision} đã xếp hàng. Phát hiện theo bằng chứng bên dưới thuộc phiên bản mới nhất.` : `Đã phát hiện thay đổi phiên bản ${state.revision}. Kết quả theo bằng chứng hiển thị ngay; AI đang tự chọn công cụ để xác minh. Bạn có thể tiếp tục thao tác.`;
  
  // Render Agent Proposed Tasks
  const taskList = state.report?.tasks || [];
  if (taskList.length) {
    const tasksWrap = el('div', undefined, 'agent-tasks-box');
    tasksWrap.append(el('h3', `📋 Đề xuất xử lý từ Agent (${taskList.length} công việc đã lưu SQLite):`));
    const ul = el('ul', undefined, 'agent-tasks-list');
    for (const t of taskList.slice(0, 6)) {
      const li = el('li');
      li.append(
        el('strong', `[${t.priority || 'Trung bình'}] ${t.task_id} (${t.owner}): `),
        el('span', t.title)
      );
      ul.append(li);
    }
    if (taskList.length > 6) {
      ul.append(el('li', `... và ${taskList.length - 6} nhiệm vụ khác cho toàn doanh nghiệp.`));
    }
    $('live-tasks-section').replaceChildren(tasksWrap);
  } else {
    $('live-tasks-section').replaceChildren();
  }

  const progressActions = state.progress.filter(e => e.type === 'action');
  const reportActions = (state.report?.events || []).filter(e => e.type === 'action');
  const actions = progressActions.length ? progressActions : reportActions;
  $('live-tools').replaceChildren(...actions.map(event => {
    const item = el('li', `${event.tool === 'inspect_evidence' ? 'Xác minh nguồn bằng chứng thiếu' : liveToolNames[event.tool]} · ${event.reason}`);
    const finished = state.progress.some(e => e.type === 'tool_result' && e.step === event.step);
    item.append(el('small', `${finished ? 'Đã nhận kết quả công cụ' : 'Đang thực hiện'}${event.available_tools ? ` · Đã chọn trong ${event.available_tools.length} công cụ khả dụng · ${event.decision_ms} ms` : ''}`));
    const result = state.progress.find(e => e.type === 'tool_result' && e.step === event.step);
    if (result) {const detail = el('details'); detail.append(el('summary', 'Quan sát thực tế từ công cụ'), el('pre', JSON.stringify(result.observation, null, 2), 'tool-observation')); item.append(detail);}
    return item;
  }));
  if (!actions.length) $('live-tools').append(el('li', 'Chưa có công cụ được gọi cho phiên bản này.'));
  $('business-person').disabled = submittingEvent; $('business-action').disabled = submittingEvent;
  $('business-submit').disabled = submittingEvent;
  renderDossier();
}

async function pollLive() {
  try {
    const state = await request('/api/live');
    displayLive(state);
    $('live-error').hidden = true;
  } catch (error) {
    liveState = null;
    $('live-error').textContent = `Mất kết nối nguồn doanh nghiệp: ${error.message}. Đang tự kết nối lại…`;
    $('live-error').hidden = false;
    $('live-state-badge').textContent = 'Mất kết nối';
  } finally { setTimeout(pollLive, 2000); }
}
async function submitBusinessChange(person_id, action) {
  if (submittingEvent) return;
  submittingEvent = true; $('business-submit').disabled = true;
  try {
    const result = await request('/api/live/events', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({person_id, action})});
    $('business-feedback').textContent = result.changed ? `Đã ghi nhận ${person_id}, phiên bản ${result.revision}. Agent tự nhận thay đổi.` : 'Hồ sơ đã có trạng thái này; không phát sinh sự kiện mới.';
    const state = await request('/api/live');
    displayLive(state);
    if (result.changed) window.dispatchEvent(new CustomEvent('hivefive:focus-person', {detail: {id: person_id}}));
  } catch (error) { $('business-feedback').textContent = error.message; }
  finally { submittingEvent = false; $('business-submit').disabled = false; $('business-person').disabled = false; $('business-action').disabled = false; renderDossier(); }
}
$('business-form').addEventListener('submit', event => {
  event.preventDefault();
  submitBusinessChange($('business-person').value, $('business-action').value);
});
window.addEventListener('hivefive:person-selected', event => {
  if (liveState && $('business-person').querySelector(`option[value="${event.detail.person.id}"]`)) $('business-person').value = event.detail.person.id;
  renderDossier();
});
$('business-person').addEventListener('change', () => {renderDossier(); window.dispatchEvent(new CustomEvent('hivefive:focus-person', {detail: {id: $('business-person').value}}));});
async function loadResearch() {
  try {
    const result = await request('/api/research');
    const table = el('table'), head = el('tr');
    for (const text of ['Chế độ', 'Hoàn tất', 'Khớp nhãn toàn ca', 'TB thời gian', 'Độ lệch chuẩn', 'Kế hoạch đủ bước yêu cầu', 'Lần gọi model']) head.append(el('th', text));
    table.append(head);
    for (const [mode, summary] of Object.entries(result.summary)) {
      const row = el('tr');
      for (const text of [({rules:'Luật', workflow:'Workflow cố định', ai:'AI chọn công cụ'})[mode], `${summary.completed}/${summary.trials}`, `${summary.exact_matches}/${summary.trials}`, summary.mean_ms === null ? 'Chưa đo' : `${summary.mean_ms} ms`, summary.stdev_ms == null ? 'Chưa đo' : `${summary.stdev_ms} ms`, mode === 'rules' ? 'Không điều phối công cụ' : `${summary.required_plan_complete ?? '—'}/${summary.trials}`, summary.model_calls]) row.append(el('td', text));
      table.append(row);
    }
    $('research-results').replaceChildren(el('p', `${result.case_count} ca tổng hợp · ${result.repeats || 1} lần lặp · ${result.paired ? 'Ba chế độ cùng tập ca và snapshot' : 'Các chế độ có thể khác số ca'} · ${new Date(result.generated_at).toLocaleString('vi-VN')}`), table, ...result.limitations.map(text => el('p', text, 'hint')));
  } catch (error) { $('research-results').textContent = `Chưa tải được kết quả: ${error.message}`; }
}
loadResearch();
document.querySelector('.research-panel').addEventListener('toggle', event => {if (event.target.open) loadResearch();});
pollLive();
