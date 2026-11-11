"""Representative A.6 assessment of lab business records, never office animation state."""
import hashlib
import json
from agent_core.evidence_context import assessment_date, context_observations, valid_retention

ISO_27002_CITATIONS = {'A.6.1': {'pillar': 'people', 'clause': 'ISO/IEC 27002:2022 Clause 6.1'}, 'A.6.2': {'pillar': 'people', 'clause': 'ISO/IEC 27002:2022 Clause 6.2'}, 'A.6.3': {'pillar': 'people', 'clause': 'ISO/IEC 27002:2022 Clause 6.3'}, 'A.6.4': {'pillar': 'people', 'clause': 'ISO/IEC 27002:2022 Clause 6.4'}, 'A.6.5': {'pillar': 'cross_pillar', 'clause': 'ISO/IEC 27002:2022 Clause 6.5'}, 'A.6.6': {'pillar': 'people', 'clause': 'ISO/IEC 27002:2022 Clause 6.6'}, 'A.6.7': {'pillar': 'cross_pillar', 'clause': 'ISO/IEC 27002:2022 Clause 6.7'}, 'A.6.8': {'pillar': 'people', 'clause': 'ISO/IEC 27002:2022 Clause 6.8'}}

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
