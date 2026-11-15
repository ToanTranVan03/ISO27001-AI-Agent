"""Conservative rationale checks, not grading or proof of human authorship."""
from collections import Counter
import re


def normalize(text):
    return ' '.join(text.casefold().split())


def markers(record):
    texts=[a['artifact'] for a in record['evidence'].get('artifacts',[])]
    texts.extend(c.get('raw_source','') for c in record.get('criteria_details',[]))
    return {t for text in texts for t in re.findall(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9]+)*',text)
            if ('_' in t or '.' in t) and t not in ('probe.json','capture.json')}


def inspect_rationale(report,control_id,rationale,own_reviews):
    record=next(r for r in report['records'] if r['control_id']==control_id)
    text=normalize(rationale)
    chars=[c for c in text if c.isalnum()]
    issues=[]
    if len(text)<10 or not chars or (len(chars)>=20 and max(Counter(chars).values())/len(chars)>0.6):
        issues.append(dict(code='filler_or_too_short',severity='error',
                           message='Căn cứ quá ngắn hoặc chủ yếu là ký tự lặp; hãy mô tả quan sát từ nguồn.'))
    duplicate=sorted({r['control_id'] for r in own_reviews if r['control_id']!=control_id and normalize(r.get('rationale',''))==text})
    if duplicate:
        issues.append(dict(code='duplicate_other_control',severity='warning',related_controls=duplicate,
            message='Căn cứ trùng nguyên văn control khác của bạn: '+', '.join(duplicate)+'. Hãy kiểm tra dán nhầm.'))
    current=markers(record)
    foreign={}
    for other in report['records']:
        if other['control_id']==control_id:continue
        found=sorted(t for t in markers(other)-current if re.search(r'(?<!\w)'+re.escape(t)+r'(?!\w)',rationale,re.I))
        if found:foreign[other['control_id']]=found
    if foreign:
        issues.append(dict(code='references_other_control_sources',severity='warning',references=foreign,
            message='Có tên tệp/trường thuộc tiêu chí control khác; kiểm tra viện dẫn và phạm vi trước khi nộp.'))
    return dict(issues=issues,blocked=any(i['severity']=='error' for i in issues),
                note='Kiểm tra hình thức và dấu hiệu dán nhầm, không xác nhận căn cứ đúng hoặc nhãn độc lập.')


def audit_reviews(report,reviews):
    result=[]
    for review in reviews:
        own=[r for r in reviews if r.get('reviewer_id')==review.get('reviewer_id')]
        check=inspect_rationale(report,review['control_id'],review.get('rationale',''),own)
        if check['issues']:result.append(dict(reviewer_id=review.get('reviewer_id'),
            reviewer_name=review.get('reviewer_name'),control_id=review['control_id'],**check))
    return result


def pending_quality_reviews(report,reviews):
    pending=[]
    for r in reviews:
        own=[x for x in reviews if x.get('reviewer_id')==r.get('reviewer_id')]
        # Preserve a real acknowledgment made at submission time. Later reviews
        # must not retroactively make the first occurrence an unacknowledged copy.
        check=r.get('quality_check') or inspect_rationale(report,r['control_id'],r.get('rationale',''),own)
        if check['blocked'] or (check['issues'] and not r.get('quality_warning_acknowledged')):pending.append(r)
    return pending
