/* Stream actual agent events; model/evidence text is always rendered as inert text. */
const toolNames = {
  read_people: 'Đọc hồ sơ nhân sự', read_assets: 'Đọc tài khoản và laptop',
  assess_people: 'Đối chiếu 8 kiểm soát con người', inspect_offboarding: 'Kiểm tra sâu người nghỉ việc',
  inspect_remote: 'Kiểm tra sâu làm việc từ xa', check_scope: 'Rà soát danh mục 56 kiểm soát',
  create_tasks: 'Lập và đối chiếu công việc', verify_report: 'Xác minh báo cáo'
};
function observationText(tool, o) {
  switch (tool) {
    case 'read_people': return `Đã đọc ${o.people_records} hồ sơ từ ${o.source}.`;
    case 'read_assets': return `Đã liên kết ${o.accounts} tài khoản và ${o.devices} laptop.`;
    case 'assess_people': return `Đã đánh giá ${o.evaluated_controls} kiểm soát. Phát hiện: ${Object.entries(o.findings_by_control).map(([id, n]) => `${id}: ${n} hồ sơ`).join(' · ') || 'không có'}.`;
    case 'inspect_offboarding': return `${o.person_ids.join(', ')}: còn ${o.active_account_ids.length} tài khoản mở, ${o.unreturned_device_ids.length} thiết bị chưa trả.`;
    case 'inspect_remote': return `${o.unencrypted_device_ids.length} laptop chưa mã hóa, ${o.vpn_without_mfa_ids.length} VPN thiếu MFA.`;
    case 'check_scope': return `${o.implemented_evaluators}/56 kiểm soát có bộ đánh giá; ${o.not_evaluated_controls} chưa đánh giá.`;
    case 'create_tasks': return `${o.proposed_tasks} việc đề xuất; ${o.reused_tasks} việc đã tồn tại; ${o.verified_clear_in_simulation} việc đã hết phát hiện khi kiểm tra lại. Chỉ lưu nội bộ.`;
    case 'verify_report': return `Đã xác minh bằng chứng, phạm vi và ${o.task_count} công việc.`;
    default: return '';
  }
}
function showAgentReport(report) {
  $('agent-log').replaceChildren();
  for (const event of report.events.filter(e => e.type === 'action')) {
    const item = el('li', `${toolNames[event.tool]} — ${event.reason}`);
    const result = report.events.find(e => e.type === 'tool_result' && e.step === event.step);
    if (result) item.append(el('p', observationText(event.tool, result.observation), 'hint'));
    $('agent-log').append(item);
  }
  $('agent-report').hidden = false;
  const scope = report.scope;
  $('agent-summary').replaceChildren(
    fact(`${scope.evaluated_controls}/${scope.catalog_controls} đã đánh giá`, `${scope.not_evaluated_controls} kiểm soát chưa được đánh giá`),
    fact(`${report.summary.affected_people} nhân sự có phát hiện`, `${report.summary.controls_with_findings} kiểm soát con người cần xử lý`),
    fact(`${report.tasks.length} việc đề xuất`, `${report.tasks.filter(t => t.reused).length} việc được nhận diện lại, không tạo trùng`)
  );
  $('agent-source').textContent = `${new Date(report.created_at).toLocaleString('vi-VN')} · ${report.mode === 'ai' ? 'AI chọn công cụ' : 'Workflow quy tắc'} · Nguồn: ${report.source} · Mã bằng chứng: ${report.snapshot_hash.slice(0, 12)}`;
  $('agent-tasks-label').textContent = `${report.tasks.length} công việc đề xuất cho HR / IT`;
  $('agent-tasks').replaceChildren(...report.tasks.map(task => fact(
    `${task.task_id} · ${task.owner} · ${task.reused ? 'Đã tồn tại' : 'Mới'}`,
    `${task.title} ${task.person_ids.length ? 'Hồ sơ: ' + task.person_ids.join(', ') + '.' : ''} Trạng thái: đề xuất, chưa thực hiện.`
  )));
  $('agent-cleared').replaceChildren(...report.verified_clear_tasks.map(t => fact(t.task_id, 'Nguồn bằng chứng mới không còn phát hiện theo quy tắc mô phỏng.')));
  $('agent-coverage').replaceChildren(
    fact('A.6 · Con người: 8/8 đã đánh giá', 'Quy tắc đơn giản hóa với hồ sơ và bằng chứng liên kết.'),
    fact('A.7 · Vật lý: 0/14 đã đánh giá', 'Chưa có bộ đánh giá và nguồn bằng chứng.'),
    fact('A.8 · Công nghệ: 0/34 đã đánh giá', 'Chưa có bộ đánh giá và nguồn bằng chứng. Dữ liệu tài khoản/laptop hiện hỗ trợ kiểm tra A.6.'),
    el('p', report.limitations, 'hint')
  );
  renderResult({enterprise: report.enterprise, controls: report.people_controls, summary: report.summary,
    scenario: {id: 'autonomous', name: 'Agent kiểm tra HiveFive', description: report.goal},
    generated_at: report.created_at, mode_label: report.mode === 'ai' ? 'AI điều phối công cụ' : 'Workflow quy tắc',
    audit_trail: report.events.filter(e => e.type === 'action').map(e => `${toolNames[e.tool]}: ${e.reason}`)});
  $('people-count').textContent = report.enterprise.people.length;
  $('account-count').textContent = report.enterprise.accounts.length;
  $('device-count').textContent = report.enterprise.devices.length;
}
async function loadAgentHistory() {
  try {
    const history = await request('/api/agent/history');
    $('agent-history').replaceChildren(...history.map(r => el('li', `${new Date(r.created_at).toLocaleString('vi-VN')} · ${r.mode === 'ai' ? 'AI' : 'Workflow'} · ${r.status === 'complete' ? 'Hoàn tất' : 'Thất bại'} · ${r.goal}`)));
    if (!history.length) $('agent-history').append(el('li', 'Chưa có lần kiểm tra.'));
  } catch { $('agent-history').replaceChildren(el('li', 'Không tải được lịch sử.')); }
}
async function runMission() {
  if (busy) return;
  if (!$('agent-goal').value.trim()) { $('agent-goal').focus(); return; }
  busy = true;
  for (const id of ['agent-run', 'agent-restore', 'run', 'agent-goal', 'agent-mode']) $(id).disabled = true;
  $('agent-error').hidden = true; $('agent-log').replaceChildren(); $('agent-log-panel').open = true;
  $('agent-status').textContent = 'Đang nhận mục tiêu…';
  $('agent-report').hidden = true;
  let completed = false;
  function handle(event) {
    if (event.type === 'error') throw new Error(event.message);
    if (event.type === 'start') $('agent-status').textContent = `${event.message} Đang chờ bộ điều phối chọn công cụ…`;
    if (event.type === 'action') {
      $('agent-log').append(el('li', `${toolNames[event.tool]} — ${event.reason}`));
      $('agent-status').textContent = `Đang thực hiện: ${toolNames[event.tool]}…`;
    }
    if (event.type === 'tool_result') {
      const item = $('agent-log').lastElementChild;
      item?.append(el('p', observationText(event.tool, event.observation), 'hint'));
      $('agent-status').textContent = 'Đã nhận kết quả. Đang chọn công cụ tiếp theo…';
    }
    if (event.type === 'complete') {
      showAgentReport(event.report); completed = true;
      $('agent-status').textContent = 'Đã hoàn tất kiểm tra và lưu báo cáo. Xem công việc đề xuất và nhân sự được đánh dấu trong mô hình.';
    }
  }
  try {
    const response = await fetch('/api/agent/run', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({goal: $('agent-goal').value.trim(), mode: $('agent-mode').value})});
    if (!response.ok) throw new Error(`Không khởi chạy được Agent (${response.status}).`);
    const reader = response.body.getReader(), decoder = new TextDecoder();
    let buffer = '';
    try {
      while (true) {
        const {value, done} = await reader.read();
        buffer += decoder.decode(value, {stream: !done});
        const lines = buffer.split('\n'); buffer = lines.pop();
        for (const line of lines) if (line.trim()) handle(JSON.parse(line));
        if (done) break;
      }
      if (buffer.trim()) handle(JSON.parse(buffer));
      if (!completed) throw new Error('Kết nối kết thúc trước khi Agent hoàn tất. Hãy chạy lại.');
    } finally { await reader.cancel().catch(() => {}); }
  } catch (error) {
    $('agent-error').textContent = error.message || 'Không kết nối được máy chủ.'; $('agent-error').hidden = false;
    $('agent-status').textContent = 'Lần kiểm tra chưa hoàn tất. Có thể chạy lại; nhật ký trên là các bước thực tế đã nhận. Kết quả 3D cũ (nếu có) thuộc lần chạy trước.';
  } finally {
    busy = false;
    for (const id of ['agent-run', 'agent-restore', 'run', 'agent-goal', 'agent-mode']) $(id).disabled = false;
    loadAgentHistory();
  }
}
$('agent-run').addEventListener('click', runMission);
$('agent-restore').addEventListener('click', async () => {
  if (busy) return;
  try {
    const report = await request('/api/agent/latest');
    if (report) { showAgentReport(report); $('agent-status').textContent = 'Đang xem báo cáo hoàn tất gần nhất được lưu trên máy.'; }
    else $('agent-status').textContent = 'Chưa có báo cáo hoàn tất.';
  } catch { $('agent-status').textContent = 'Không tải được báo cáo gần nhất.'; }
});
$('agent-history-panel').addEventListener('toggle', () => { if ($('agent-history-panel').open) loadAgentHistory(); });
