"""Pure lab business-record changes used by the assessment inventory."""
import copy
from datetime import timedelta
from agent_core.evidence_context import assessment_date

ACTIONS = {
    'terminate': 'Ghi nhận nghỉ việc',
    'recover_access': 'Thu hồi tài khoản và nhận lại laptop',
    'training_missing': 'Ghi nhận chưa hoàn tất đào tạo',
    'training_complete': 'Ghi nhận hoàn tất đào tạo và đạt kiểm tra',
    'training_unverified': 'Chưa xác minh được kết quả đào tạo (thiếu bằng chứng)',
    'training_expired': 'Ghi nhận chứng nhận đào tạo đã hết hạn',
    'training_conflict': 'Ghi nhận HR và LMS mâu thuẫn kết quả đào tạo',
    'role_change': 'Chuyển vai trò, chưa rà soát quyền cũ',
    'role_review': 'Xác nhận đã rà soát quyền theo vai trò mới',
    'retention_request': 'Nghỉ việc: đề nghị giữ tài khoản HR để bàn giao',
    'retention_approve': 'Ghi nhận quản lý phê duyệt ngoại lệ giữ HR (mô phỏng)',
    'retention_expire': 'Ghi nhận ngoại lệ giữ HR đã hết hạn',
    'advance_day': 'Chuyển ngày mô phỏng: tự đối chiếu thời hạn toàn doanh nghiệp',
    'nda_missing': 'Ghi nhận chưa ký NDA và cam kết lao động',
    'nda_signed': 'Ghi nhận đã ký NDA và cam kết lao động',
    'remote_unprotected': 'Làm từ xa, laptop và VPN chưa được bảo vệ',
    'remote_protected': 'Bật mã hóa laptop, MFA VPN và xác nhận chính sách',
    'screening_missing': 'Ghi nhận thiếu hồ sơ thẩm tra',
    'screening_complete': 'Bổ sung hồ sơ thẩm tra',
    'discipline_missing': 'Chưa phổ biến quy trình xử lý vi phạm',
    'discipline_complete': 'Đã phổ biến quy trình xử lý vi phạm',
    'report_missing': 'Ghi nhận sự kiện chưa được báo cáo',
    'report_complete': 'Ghi nhận đã hướng dẫn và báo cáo sự kiện',
}




def apply_business_change(enterprise, person_id, action):
    if action not in ACTIONS:
        raise ValueError('Thao tác doanh nghiệp không hợp lệ.')
    person = next((p for p in enterprise['people'] if p['id'] == person_id), None)
    if person is None:
        raise ValueError('Không tìm thấy nhân sự.')
    accounts = [a for a in enterprise['accounts'] if a['person_id'] == person_id]
    devices = [d for d in enterprise['devices'] if d['person_id'] == person_id]
    before = copy.deepcopy({'person': person, 'accounts': accounts, 'devices': devices,
                            'assessment_date': assessment_date(enterprise).isoformat()})
    if action == 'advance_day':
        enterprise['assessment_date'] = (assessment_date(enterprise) + timedelta(days=1)).isoformat()
    elif action == 'terminate':
        person['status'] = 'terminated'
    elif action == 'recover_access':
        if person['status'] != 'terminated':
            raise ValueError('Thao tác thu hồi khi nghỉ việc chỉ áp dụng cho người đã nghỉ việc.')
        for account in accounts:
            account['active'] = False
        for device in devices:
            device['returned'] = True
        person['post_employment_ack'] = True
    elif action in ('training_expired', 'training_conflict'):
        person.update(training_complete=True, training_passed=True)
        if action == 'training_expired':
            person['training_valid_until'] = (assessment_date(enterprise) - timedelta(days=1)).isoformat()
        else:
            person['lms_training_passed'] = False
    elif action.startswith('training_'):
        complete = None if action == 'training_unverified' else action == 'training_complete'
        person.update(training_complete=complete, training_passed=complete)
        if action == 'training_complete':
            if 'training_valid_until' in person:
                person['training_valid_until'] = (assessment_date(enterprise) + timedelta(days=365)).isoformat()
            if 'lms_training_passed' in person:
                person['lms_training_passed'] = True
    elif action in ('role_change', 'role_review'):
        if person['status'] != 'active':
            raise ValueError('Chuyển vai trò và rà soát quyền chỉ áp dụng cho người đang làm việc.')
        if action == 'role_review' and not person.get('access_review_required'):
            raise ValueError('Chưa có yêu cầu rà soát quyền khi chuyển vai trò.')
        person.update(role='Điều phối viên', access_review_required=True)
        for account in accounts:
            account['role_reviewed'] = action == 'role_review'
    elif action.startswith('retention_'):
        if person['status'] != 'terminated':
            raise ValueError('Ngoại lệ bàn giao chỉ áp dụng cho người đã nghỉ việc.')
        hr = next(a for a in accounts if a['system'] == 'HR')
        if action == 'retention_request':
            for account in accounts:
                account['active'] = account is hr
            for device in devices:
                device['returned'] = True
            person['post_employment_ack'] = True
            hr['retention_exception'] = {'account_id': hr['id'], 'scope': 'offboarding-retention',
                'approved': False, 'approver': None, 'reason': 'Đối chiếu hồ sơ bàn giao (giả lập)',
                'expires_on': (assessment_date(enterprise) + timedelta(days=1)).isoformat()}
        else:
            exception = hr.get('retention_exception')
            if not exception or not hr['active']:
                raise ValueError('Cần đề nghị giữ tài khoản HR đang mở trước khi ghi nhận phê duyệt/hết hạn.')
            if action == 'retention_approve':
                exception.update(approved=True, approver='IT Manager (giả lập)')
            else:
                exception['expires_on'] = (assessment_date(enterprise) - timedelta(days=1)).isoformat()
    elif action.startswith('nda_'):
        signed = action == 'nda_signed'
        person.update(nda_signed=signed, terms_signed=signed)
    elif action.startswith('remote_'):
        protected = action == 'remote_protected'
        person.update(remote=True, remote_policy_ack=protected)
        for device in devices:
            device['encrypted'] = protected
        for account in accounts:
            if account['system'] == 'VPN':
                account['mfa'] = protected
    elif action.startswith('screening_'):
        person['screened'] = action == 'screening_complete'
    elif action.startswith('discipline_'):
        person['disciplinary_informed'] = action == 'discipline_complete'
    elif action.startswith('report_'):
        complete = action == 'report_complete'
        person.update(reporting_trained=complete, event_reported=complete)
    after = {'person': person, 'accounts': accounts, 'devices': devices,
             'assessment_date': assessment_date(enterprise).isoformat()}
    return before, after
