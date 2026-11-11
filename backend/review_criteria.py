"""Project rubric coverage; not a claim to cover every ISO implementation detail."""
PROTOCOL='human-criteria-review-v2'


def conclusion(checks):
    values=[c['verdict'] for c in checks]
    if not values or 'unknown' in values:return 'Insufficient Evidence'
    if all(v=='met' for v in values):return 'Compliant'
    if all(v=='not_met' for v in values):return 'Non-Compliant'
    return 'Partially Compliant'


def validate(criteria,checks,evidence_ids,declared):
    if len(checks)!=len(criteria) or {c['criterion_index'] for c in checks}!=set(range(len(criteria))):
        raise ValueError('Cần thẩm định từng tiêu chí, không trùng hoặc bỏ sót.')
    available=set(evidence_ids)
    for item in checks:
        if item['verdict'] not in ('met','not_met','unknown') or len(item['rationale'].strip())<10:
            raise ValueError('Mỗi tiêu chí cần kết quả và căn cứ ít nhất 10 ký tự.')
        if not set(item['evidence_ids'])<=available:
            raise ValueError('Viện dẫn tiêu chí phải nằm trong bằng chứng của thẩm định.')
        if item['verdict']!='unknown' and not item['evidence_ids']:
            raise ValueError('Đạt hoặc không đạt tiêu chí cần bằng chứng; không có nguồn phải ghi chưa rõ.')
    if declared!=conclusion(checks):
        raise ValueError('Kết luận chưa khớp kết quả từng tiêu chí theo rubric dự án.')


def current(review,criteria):
    if not review or review.get('protocol')!=PROTOCOL:return False
    try:validate(criteria,review.get('criteria_reviews',[]),review.get('evidence_ids',[]),review['conclusion'])
    except (ValueError,KeyError,TypeError):return False
    return True
