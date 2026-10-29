"""Strictly synthetic enterprise-lab definition. No external targets or secrets.

These lab records are training fixtures, not a real asset inventory or a certification.
Only admin preset changes are supported; callers cannot inject arbitrary instructions.
"""
import hashlib
import json
from uuid import UUID, NAMESPACE_URL, uuid5

PRESETS = ('healthy', 'partial', 'gap')
NODE_SPECS = {
    'hr': {
        'title': 'Nhân sự & tuyển dụng', 'department': 'People', 'icon': '👥',
        'description': 'Hồ sơ thẩm tra trước tuyển dụng (toàn bộ là dữ liệu giả lập)',
        'controls': ['A.6.1'], 'tool': 'Tool_People_Evidence_Check',
        'values': {
            'healthy': {'employees_total': 12, 'screening_records': 12, 'screening_policy_approved': True, 'hr_confirmation_available': True},
            'partial': {'employees_total': 12, 'screening_records': 7, 'screening_policy_approved': True, 'hr_confirmation_available': False},
            'gap': {'employees_total': 12, 'screening_records': 0, 'screening_policy_approved': False, 'hr_confirmation_available': False},
        },
    },
    'physical': {
        'title': 'Phòng máy & an ninh vật lý', 'department': 'Physical', 'icon': '🏢',
        'description': 'Chu vi khu vực bảo vệ, nhật ký kiểm tra và xác nhận tại chỗ',
        'controls': ['A.7.1'], 'tool': 'Tool_Physical_Asset_Check',
        'values': {
            'healthy': {'zones_defined': 3, 'zones_access_restricted': 3, 'perimeter_policy_exists': True, 'site_inspection_attested': True},
            'partial': {'zones_defined': 3, 'zones_access_restricted': 1, 'perimeter_policy_exists': True, 'site_inspection_attested': False},
            'gap': {'zones_defined': 3, 'zones_access_restricted': 0, 'perimeter_policy_exists': False, 'site_inspection_attested': False},
        },
    },
    'iam': {
        'title': 'IAM / Xác thực', 'department': 'Technology', 'icon': '🔐',
        'description': 'MFA, tài khoản đặc quyền và cấu hình xác thực giả lập',
        'controls': ['A.8.5'], 'tool': 'Tool_Technical_Evidence_Collector:iam',
        'values': {
            'healthy': {'active_accounts': 18, 'mfa_enabled_accounts': 18, 'privileged_accounts': 3, 'privileged_mfa_accounts': 3, 'password_min_length': 14},
            'partial': {'active_accounts': 18, 'mfa_enabled_accounts': 12, 'privileged_accounts': 3, 'privileged_mfa_accounts': 2, 'password_min_length': 10},
            'gap': {'active_accounts': 18, 'mfa_enabled_accounts': 0, 'privileged_accounts': 3, 'privileged_mfa_accounts': 0, 'password_min_length': 6},
        },
    },
    'network': {
        'title': 'Gateway / Mạng', 'department': 'Technology', 'icon': '🌐',
        'description': 'Chính sách bảo vệ mạng và thay đổi cấu hình giả lập',
        'controls': ['A.8.20'], 'tool': 'Tool_Technical_Evidence_Collector:network',
        'values': {
            'healthy': {'network_policy_defined': True, 'rules_approved': 12, 'rules_total': 12, 'change_log_available': True},
            'partial': {'network_policy_defined': True, 'rules_approved': 7, 'rules_total': 12, 'change_log_available': False},
            'gap': {'network_policy_defined': False, 'rules_approved': 0, 'rules_total': 12, 'change_log_available': False},
        },
    },
    'secops': {
        'title': 'SecOps / Sao lưu', 'department': 'Technology', 'icon': '🛡️',
        'description': 'Bản ghi diễn tập sao lưu, kiểm tra toàn vẹn và khôi phục giả lập',
        'controls': ['A.8.13'], 'tool': 'Tool_Technical_Evidence_Collector:backup',
        'values': {
            'healthy': {'scheduled_backups': True, 'recent_jobs': 8, 'successful_jobs': 8, 'integrity_checks_passed': 8, 'restore_test_passed': True},
            'partial': {'scheduled_backups': True, 'recent_jobs': 8, 'successful_jobs': 6, 'integrity_checks_passed': 4, 'restore_test_passed': False},
            'gap': {'scheduled_backups': False, 'recent_jobs': 0, 'successful_jobs': 0, 'integrity_checks_passed': 0, 'restore_test_passed': False},
        },
    },
}
CONTROL_TO_NODE = {control: key for key, spec in NODE_SPECS.items() for control in spec['controls']}


def make_snapshot(assessment_id: str, node_key: str, scenario: str, revision: int) -> dict:
    """Build immutable synthetic JSON snapshot, with stable ID based on assessment/revision."""
    if node_key not in NODE_SPECS or scenario not in PRESETS or revision < 1:
        raise ValueError('Invalid lab node, scenario, or revision.')
    assessment_id = str(UUID(assessment_id))
    spec = NODE_SPECS[node_key]
    control_id = spec['controls'][0]
    payload = {
        'source_kind': 'SIMULATED_ENTERPRISE_LAB',
        'is_synthetic': True,
        'assessment_id': assessment_id,
        'lab_node': node_key,
        'scenario': scenario,
        'revision': revision,
        'control_id': control_id,
        'tool': spec['tool'],
        'facts': spec['values'][scenario],
        'limitations': 'Synthetic lab state only; human/real-world validation may still be required. Not ISO certification.',
    }
    content = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    digest = hashlib.sha256(content.encode('utf-8')).hexdigest()
    evidence_id = 'LAB-' + uuid5(NAMESPACE_URL, f'{assessment_id}:{node_key}:{revision}:{digest}').hex[:24].upper()
    return {
        'evidence_id': evidence_id,
        'control_id': control_id,
        'source': f'lab://{node_key}/v{revision}',
        'sha256_hash': digest,
        'extracted_text': content,
        'evidence_type': 'SYNTHETIC_LAB_SNAPSHOT',
        'origin': 'SIMULATED_ENTERPRISE_LAB',
    }
