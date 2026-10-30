"""Project-specific temporal, conflicting-source and exception checks."""
from datetime import date


def assessment_date(enterprise):
    # Legacy snapshots use the documented initial simulation date, never wall-clock drift.
    return date.fromisoformat(enterprise.get('assessment_date', '2026-10-30'))


def valid_retention(account, today):
    exception = account.get('retention_exception') or {}
    if not isinstance(exception, dict):
        return False
    try:
        return (account.get('system') == 'HR' and exception.get('approved') is True and exception.get('account_id') == account['id']
                and exception.get('scope') == 'offboarding-retention'
                and isinstance(exception.get('approver'), str) and bool(exception['approver'].strip())
                and isinstance(exception.get('reason'), str) and bool(exception['reason'].strip())
                and date.fromisoformat(exception['expires_on']) >= today)
    except (ValueError, KeyError, TypeError):
        return False


def context_observations(enterprise, person, cid):
    observed = {}
    if cid == 'A.6.3':
        if 'training_valid_until' in person:
            expiry = person['training_valid_until']
            try:
                observed['training_current'] = date.fromisoformat(expiry) >= assessment_date(enterprise)
            except (TypeError, ValueError):
                observed['training_current'] = None
            observed['training_valid_until'] = expiry
            observed['assessment_date'] = assessment_date(enterprise).isoformat()
            if observed['training_current'] is not True:
                observed['context_recommendation'] = 'HR xác minh thời hạn, tổ chức đào tạo/gia hạn và lưu kết quả mới.'
        if 'lms_training_passed' in person:
            lms, hr = person['lms_training_passed'], person.get('training_passed')
            observed['training_source_agreement'] = True if type(lms) is bool and type(hr) is bool and lms == hr else None
            observed['training_source_comparison'] = f'HR={hr}; LMS={lms}'
            observed['source_resolution'] = 'Nguồn thống nhất' if observed['training_source_agreement'] else 'Cần HR/LMS đối soát; không tự chọn nguồn đúng'
            if observed['training_source_agreement'] is None:
                observed['training_passed'] = None
                observed['context_recommendation'] = 'HR và quản trị LMS đối soát chứng từ gốc trước khi ghi nhận kết quả; chưa kết luận vi phạm chỉ từ hai nguồn mâu thuẫn.'
    if cid == 'A.6.5' and person.get('access_review_required') is True:
        accounts = [a for a in (enterprise.get('accounts') or []) if a['person_id'] == person['id']]
        values = [a.get('role_reviewed') for a in accounts]
        observed['role_access_reviewed'] = False if False in values else True if values and all(v is True for v in values) else None
        observed['current_role'] = person.get('role')
        if observed['role_access_reviewed'] is not True:
            observed['context_recommendation'] = 'HR/IT rà soát quyền theo vai trò mới, loại bỏ quyền cũ không còn phù hợp và lưu xác nhận.'
    return observed
