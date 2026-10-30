"""Isolated, synthetic HiveFive scenarios; rules never use benchmark answer labels."""

import hashlib
import json
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from agent_core.evidence_context import assessment_date, context_observations, valid_retention


SCENARIOS = [
    {'id': 'baseline', 'name': 'Doanh nghiệp mẫu', 'description': '50 nhân sự có hồ sơ đầy đủ theo chính sách mô phỏng.'},
    {'id': 'new-hire', 'name': 'Nhân viên mới thiếu NDA', 'description': 'Một nhân viên Sales đã có tài khoản nhưng chưa ký NDA và cam kết lao động.'},
    {'id': 'training', 'name': 'Đào tạo còn bỏ sót', 'description': '8 nhân viên Sales chưa hoàn tất khóa nhận thức an toàn thông tin.'},
    {'id': 'phishing', 'name': 'Email đáng ngờ chưa được báo cáo', 'description': 'Diễn tập giả lập: nhân viên nhận email đáng ngờ nhưng chưa biết cách báo cáo. Không gửi email thật.'},
    {'id': 'offboarding', 'name': 'Nghỉ việc còn quyền truy cập', 'description': 'Một nhân viên đã nghỉ việc nhưng tài khoản vẫn mở và laptop chưa được bàn giao.'},
    {'id': 'remote', 'name': 'Làm việc từ xa thiếu bảo vệ', 'description': 'Laptop của nhân viên làm từ xa chưa mã hóa; tài khoản VPN chưa bật MFA.'},
]

# These criteria operationalize the project's rubric, not certification requirements.
CONTROLS = [
    ('A.6.1', 'Thẩm tra trước tuyển dụng', ['screened'], 'HR', 'Hoàn tất và lưu hồ sơ thẩm tra phù hợp vai trò trước khi tuyển dụng.'),
    ('A.6.2', 'Điều khoản lao động', ['terms_signed'], 'HR', 'Bổ sung cam kết trách nhiệm bảo mật trong hồ sơ lao động.'),
    ('A.6.3', 'Nhận thức và đào tạo', ['training_complete', 'training_passed'], 'HR / Quản lý', 'Tổ chức đào tạo bổ sung, kiểm tra hiệu quả và lưu kết quả.'),
    ('A.6.4', 'Quy trình xử lý vi phạm', ['disciplinary_informed'], 'HR', 'Truyền đạt quy trình xử lý vi phạm minh bạch; lưu bằng chứng đã phổ biến.'),
    ('A.6.5', 'Trách nhiệm khi nghỉ hoặc đổi việc', ['post_employment_ack'], 'HR / IT', 'Rà soát thu hồi quyền, nhận lại thiết bị và nhắc nghĩa vụ bảo mật sau nghỉ việc.'),
    ('A.6.6', 'Thỏa thuận bảo mật', ['nda_signed'], 'HR / Pháp chế', 'Hoàn tất NDA hợp lệ trước khi cấp quyền truy cập thông tin.'),
    ('A.6.7', 'Làm việc từ xa', ['remote_policy_ack'], 'IT / Quản lý', 'Mã hóa thiết bị, bật MFA cho VPN và truyền đạt chính sách làm việc từ xa.'),
    ('A.6.8', 'Báo cáo sự kiện an toàn thông tin', ['reporting_trained', 'event_reported'], 'SecOps / Quản lý', 'Hướng dẫn kênh báo cáo, ghi nhận và xử lý sự kiện diễn tập.'),
]


def build_enterprise():
    people, accounts, devices = [], [], []
    departments = ['IT'] * 15 + ['Ops'] * 10 + ['Finance'] * 10 + ['Sales'] * 15
    fields = {field for _, _, checks, _, _ in CONTROLS for field in checks}
    for index, department in enumerate(departments, 1):
        person_id = f'HF-{index:03}'
        people.append({
            'id': person_id, 'name': f'Nhân sự {department} {index:02}',
            'department': department, 'role': 'Nhân viên', 'status': 'active',
            'remote': index % 5 == 0,
            **{field: True for field in sorted(fields)},
        })
        for system in ['HR', 'Email', 'VPN', 'Nghiệp vụ']:
            accounts.append({'id': f'{person_id}-{system}', 'person_id': person_id,
                             'system': system, 'active': True, 'mfa': True,
                             'access': 'Theo vai trò'})
        devices.append({'id': f'LT-{index:03}', 'person_id': person_id,
                        'type': 'Laptop', 'encrypted': True, 'returned': False})
    return {'name': 'HiveFive', 'synthetic': True, 'assessment_date': '2026-10-30', 'people': people,
            'accounts': accounts, 'devices': devices,
            'policies': {'disciplinary_process': True, 'reporting_channel': True},
            'policy_note': 'Quy tắc nội bộ mô phỏng: đầy đủ hồ sơ, đào tạo đạt và bảo vệ thiết bị; không phải ngưỡng chứng nhận ISO.'}


def apply_scenario(enterprise, scenario_id):
    person = enterprise['people'][-1]
    if scenario_id == 'new-hire':
        person.update(nda_signed=False, terms_signed=False)
    elif scenario_id == 'training':
        for employee in enterprise['people'][-8:]:
            employee.update(training_complete=False, training_passed=False)
    elif scenario_id == 'phishing':
        person.update(reporting_trained=False, event_reported=False)
    elif scenario_id == 'offboarding':
        person.update(status='terminated')
    elif scenario_id == 'remote':
        person.update(remote=True)
        enterprise['devices'][-1]['encrypted'] = False
        next(a for a in enterprise['accounts'] if a['person_id'] == person['id'] and a['system'] == 'VPN')['mfa'] = False


def _observations(enterprise, person, control_id, fields):
    observed = {field: person.get(field) for field in fields}
    observed.update(context_observations(enterprise, person, control_id))
    policies = enterprise.get('policies') or {}
    if control_id == 'A.6.4':
        observed['disciplinary_process'] = policies.get('disciplinary_process')
    if control_id == 'A.6.8':
        observed['reporting_channel'] = policies.get('reporting_channel')
    if control_id == 'A.6.5':
        observed['employment_status_known'] = True if person.get('status') in ('active', 'terminated') else None
    if control_id in ('A.6.5', 'A.6.7'):
        accounts, devices = enterprise.get('accounts'), enterprise.get('devices')
        if accounts is None or devices is None:
            observed['asset_inventory_complete'] = None
            return observed
        own_accounts = [a for a in accounts if a['person_id'] == person['id']]
        own_devices = [d for d in devices if d['person_id'] == person['id']]
        if control_id == 'A.6.5' and person.get('status') == 'terminated':
            retained = [a for a in own_accounts if a.get('active') is True and valid_retention(a, assessment_date(enterprise))]
            observed['active_accounts'] = [a['id'] for a in own_accounts if a.get('active') is not False and a not in retained]
            exception_records = [dict(a['retention_exception'], valid=valid_retention(a, assessment_date(enterprise)), applied=a in retained)
                                 if isinstance(a['retention_exception'], dict) else {'account_id': a['id'], 'valid': False, 'reason': 'Ngoại lệ sai định dạng'}
                                 for a in own_accounts if a.get('retention_exception')]
            if exception_records:
                observed['retention_exception_records'] = exception_records
                observed['approved_retained_accounts'] = [a['id'] for a in retained]
                observed['context_recommendation'] = 'Chỉ giữ tài khoản đúng phạm vi, có người duyệt, lý do và còn hạn; khi chưa được duyệt hoặc hết hạn phải thu hồi/rà soát lại. Đây là chính sách mô phỏng.'
            observed['unreturned_devices'] = [d['id'] for d in own_devices if d.get('returned') is not True]
            observed['access_revoked'] = not observed['active_accounts']
            observed['assets_returned'] = not observed['unreturned_devices']
        if control_id == 'A.6.7':
            observed['remote_status_known'] = True if isinstance(person.get('remote'), bool) else None
            if person.get('remote') and person.get('status') != 'terminated':
                vpn = [a for a in own_accounts if a['system'] == 'VPN' and a.get('active') is True]
                observed['device_encryption'] = all(d.get('encrypted') is True for d in own_devices) if own_devices else None
                observed['vpn_mfa'] = all(a.get('mfa') is True for a in vpn) if vpn else None
    return observed


def evaluate_enterprise(enterprise):
    from agent_core.triad import ISO_27002_CITATIONS
    controls = []
    for control_id, name, fields, owner, action in CONTROLS:
        evidences, findings, missing = [], [], []
        people = enterprise.get('people') or []
        for person in people:
            observed = _observations(enterprise, person, control_id, fields)
            evidence_id = f"SIM-{control_id}-{person['id']}"
            content_hash = hashlib.sha256(json.dumps(observed, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
            evidences.append({'evidence_id': evidence_id, 'person_id': person['id'],
                              'source': f"simulation://hivefive/people/{person['id']}",
                              'content': observed, 'sha256': content_hash})
            if any(value is None for value in observed.values()):
                missing.append(person['id'])
            failures = [key for key, value in observed.items() if value is False]
            if failures:
                findings.append({'person_id': person['id'], 'department': person['department'],
                                 'evidence_id': evidence_id, 'failed_checks': failures})
        if missing or not people:
            status = 'Insufficient Evidence'
        elif len(findings) == len(people):
            status = 'Non-Compliant'
        elif findings:
            status = 'Partially Compliant'
        else:
            status = 'Compliant'
        citation = ISO_27002_CITATIONS.get(control_id, {})
        controls.append({
            'control_id': control_id, 'name': name, 'status': status,
            'owner': owner,
            'pillar': citation.get('pillar', 'people'),
            'iso_clause': citation.get('clause', f'ISO/IEC 27002:2022 {control_id}'),
            'priority': ('Cao' if control_id in ('A.6.5', 'A.6.6', 'A.6.7') else 'Trung bình') if findings or missing or not people else 'Theo dõi',
            'rationale': f'{len(people)} hồ sơ; {len(findings)} hồ sơ có vấn đề; {len(missing)} hồ sơ thiếu bằng chứng.' if people else 'Chưa có bằng chứng nhân sự.',
            'recommended_action': action if findings or missing or not people else 'Duy trì kiểm tra định kỳ và lưu bằng chứng.',
            'findings': findings, 'missing_evidence': missing,
            'evidences': evidences,
        })
    return controls


class ModelUnavailable(RuntimeError):
    pass


def explain_with_ollama(controls):
    """LLM writes commentary only; evidence-based statuses remain authoritative."""
    actionable = [c for c in controls if c['status'] != 'Compliant']
    summary = [{key: c[key] for key in ('control_id', 'status', 'rationale', 'recommended_action', 'owner')} for c in actionable]
    payload = {'model': 'qwen2.5:7b', 'stream': False,
               'messages': [
                   {'role': 'system', 'content': 'Bạn là trợ lý diễn tập an toàn thông tin cho HiveFive. Viết kế hoạch xử lý bằng tiếng Việt tối đa 150 từ. Đầu vào CHỈ gồm các kiểm soát có vấn đề hoặc thiếu bằng chứng. Với từng kiểm soát được cung cấp, nêu hành động và bộ phận phụ trách. Không suy luận về kiểm soát khác, không viết rằng tất cả đều tuân thủ, không đổi trạng thái, không kết luận chứng nhận ISO, không tự nhận đã thực hiện khắc phục. Nếu danh sách rỗng, chỉ đề xuất duy trì kiểm tra và lưu bằng chứng.'},
                   {'role': 'user', 'content': 'Các kiểm soát cần xử lý: ' + json.dumps(summary, ensure_ascii=False)}],
               'options': {'temperature': 0, 'num_predict': 500}}
    request = Request('http://127.0.0.1:11434/api/chat', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
    try:
        with urlopen(request, timeout=60) as response:
            explanation = json.load(response)['message']['content']
        if not isinstance(explanation, str) or not explanation.strip():
            raise ValueError('Empty model response')
        return explanation.strip()
    except (URLError, HTTPError, TimeoutError, OSError, ValueError, KeyError, TypeError) as exc:
        raise ModelUnavailable('Không kết nối được Ollama hoặc model chưa trả lời hợp lệ. Kiểm tra Ollama và qwen2.5:7b, hoặc chọn chế độ Quy tắc để chạy lại.') from exc


def run_simulation(scenario_id, mode='rules'):
    if mode not in ('rules', 'ai'):
        raise ValueError('Chế độ không hợp lệ.')
    scenario = next((s for s in SCENARIOS if s['id'] == scenario_id), None)
    if scenario is None:
        raise ValueError('Không tìm thấy tình huống mô phỏng.')
    enterprise = build_enterprise()
    apply_scenario(enterprise, scenario_id)
    controls = evaluate_enterprise(enterprise)
    explanation = explain_with_ollama(controls) if mode == 'ai' else None
    affected = {f['person_id'] for c in controls for f in c['findings']}
    return {
        'scenario': scenario, 'mode': mode,
        'mode_label': 'Quy tắc + AI giải thích (Ollama)' if mode == 'ai' else 'Quy tắc nội bộ (không gọi AI)',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'enterprise': enterprise, 'controls': controls, 'ai_explanation': explanation,
        'summary': {'people': len(enterprise['people']), 'affected_people': len(affected),
                    'controls_with_findings': sum(bool(c['findings']) for c in controls),
                    'insufficient_evidence': sum(c['status'] == 'Insufficient Evidence' for c in controls)},
        'audit_trail': ['PLAN: chọn tình huống và 8 kiểm soát con người',
                        'COLLECT: tạo bản sao bằng chứng nhân sự, tài khoản và thiết bị',
                        'EVALUATE: đối chiếu chính sách nội bộ theo hồ sơ',
                        'EXPLAIN: Ollama giải thích kết quả' if mode == 'ai' else 'EXPLAIN: dùng lý giải từ quy tắc',
                        'VERIFY: trạng thái tính từ bằng chứng, thiếu dữ liệu không coi là đạt',
                        'REPORT: đề xuất xử lý để HR/IT xem xét'],
        'limitations': 'Dữ liệu và kết quả diễn tập giả lập. Chỉ đánh giá nhóm A.6 theo quy tắc dự án; không xác nhận tuân thủ toàn bộ hoặc chứng nhận ISO 27001. Chưa thực hiện hành động trên hệ thống thật.',
    }
