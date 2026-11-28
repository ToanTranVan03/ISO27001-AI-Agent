"""Read-only, evidence-aware period summaries. Model confidence is never compliance."""
from collections import Counter
import hashlib
import json


def period_fingerprint(controls):
    fields=('control_id','review_token','conclusion','assessment_state','workflow_status','applicability','human_review_current','human_review')
    rows=[{k:c.get(k) for k in fields} for c in sorted(controls,key=lambda c:c['control_id'])]
    return hashlib.sha256(json.dumps(rows,ensure_ascii=False,sort_keys=True,default=str).encode()).hexdigest()


def summarize_periods(client_id,periods):
    result=[];previous={}
    for period in periods:
        rows=period['controls'];counts=Counter();current={};changes=[]
        for c in rows:
            excluded=bool(c.get('applicability') and c['applicability'].get('applicable') is False)
            status=('Not Applicable' if excluded else 'Not Evaluated' if not c.get('latest_evaluation_id') else
                    'Needs Reassessment' if c.get('assessment_state') in ('stale','failed') else c.get('conclusion','Insufficient Evidence'))
            counts[status]+=1;current[c['control_id']]=status
            if c['control_id'] in previous and previous[c['control_id']]!=status:
                changes.append(dict(control_id=c['control_id'],before=previous[c['control_id']],after=status,
                    interpretation='Status changed; verify scope, rubric and sources before attributing improvement'))
        assessed=sum(counts[s] for s in ('Compliant','Partially Compliant','Non-Compliant','Insufficient Evidence'))
        denominator=len(rows)-counts['Not Applicable']
        result.append(dict(assessment_id=period['assessment_id'],name=period['name'],created_at=period['created_at'],
            period=period.get('period',{}),
            source_sha256=period_fingerprint(rows),
            counts=dict(counts),total=len(rows),assessed=assessed,
            compliant_share_percent=round(100*counts['Compliant']/denominator,2) if denominator else None,
            coverage_percent=round(100*assessed/denominator,2) if denominator else None,
            formula='Compliant / (scope controls - recorded exclusions) * 100; coverage = assessed / same denominator',
            changes=changes,human_reviews_current=sum(bool(c.get('human_review_current')) for c in rows)))
        previous=current
    return dict(client_id=client_id,periods=result,certification_claim=False,
        note='Visible saved assessments only. Machine result share is not certification, model confidence or independently measured accuracy. Missing evidence is not automatically a violation.')
