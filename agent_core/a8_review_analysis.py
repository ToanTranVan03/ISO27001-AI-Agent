"""Evidence-bound reviewer comparisons. Never invent consensus or human labels."""
from itertools import combinations
from agent_core.a8_benchmark import score
from agent_core.a8_assessment import STATUSES


def declared_independent(review):
    return review.get('assistance')=='unassisted' and review.get('prior_exposure')=='no'


def review_category(review):
    if declared_independent(review):return 'independent'
    if review.get('assistance') in ('ai_assisted','team_discussion') or review.get('prior_exposure')=='yes':return 'assisted'
    return 'unclassified'


def analyze_reviews(report, reviews, creator_id):
    records={r['control_id']:r for r in report['records']}
    by_reviewer={}
    rejected=0
    for review in reviews:
        record=records.get(review.get('control_id'))
        uid=str(review['reviewer_id']) if review.get('reviewer_id') is not None else ''
        if (not uid or uid==str(creator_id) or not record or
                review.get('report_sha256')!=report['sha256'] or
                review.get('evidence_sha256')!=record['evidence']['source_sha256'] or
                review.get('expected') not in STATUSES or review.get('case_id')!=record['case_id']):
            rejected+=1
            continue
        # Duplicate labels are a data-quality error, not a last-writer-wins vote.
        labels=by_reviewer.setdefault(uid,{})
        if record['control_id'] in labels:
            raise ValueError('Duplicate locked reviewer label')
        labels[record['control_id']]=review
    comparisons={uid:score([report],list(labels.values())) for uid,labels in by_reviewer.items()}
    independent={uid:{cid:r for cid,r in items.items() if declared_independent(r)} for uid,items in by_reviewer.items()}
    disagreements=[]
    for cid,record in records.items():
        labels=[dict(reviewer_id=uid,expected=items[cid]['expected'],rationale=items[cid].get('rationale',''))
                for uid,items in by_reviewer.items() if cid in items]
        if labels and (len({r['expected'] for r in labels})>1 or any(r['expected']!=record['status'] for r in labels)):
            disagreements.append(dict(control_id=cid,machine_status=record['status'],machine_error=record.get('error'),
                evidence_sha256=record['evidence']['source_sha256'],reviews=labels,
                resolution='PENDING_HUMAN_DISCUSSION'))
    pairs=[]
    for left,right in combinations(sorted(by_reviewer),2):
        a,b=by_reviewer[left],by_reviewer[right]
        shared=set(a)&set(b)
        n=len(shared)
        observed=sum(a[c]['expected']==b[c]['expected'] for c in shared)/n if n else None
        chance=sum(sum(a[c]['expected']==s for c in shared)*sum(b[c]['expected']==s for c in shared)
                   for s in STATUSES)/(n*n) if n else None
        kappa=(observed-chance)/(1-chance) if n and chance<1 else None
        pairs.append(dict(reviewers=[left,right],paired_controls=n,agreement=observed,cohens_kappa=kappa,
                          note='Kappa không xác định nếu không có cặp hoặc mọi nhãn cùng một lớp.'))
    return dict(reviewer_comparisons=comparisons,pairwise_agreement=pairs,disagreements=disagreements,
                reviewer_progress=[dict(reviewer_id=uid,submitted=len(items),total=len(records),
                    submitted_controls=sorted(items),complete=set(items)==set(records),
                    independently_declared=sum(review_category(r)=='independent' for r in items.values()),
                    assisted=sum(review_category(r)=='assisted' for r in items.values()),
                    unclassified=sum(review_category(r)=='unclassified' for r in items.values()),
                    display_name=next((r['reviewer_name'] for r in items.values() if r.get('reviewer_name')),None))
                    for uid,items in sorted(by_reviewer.items())],
                submitted_label_count=sum(len(items) for items in by_reviewer.values()),
                complete_reviewers=[uid for uid,items in by_reviewer.items() if set(items)==set(records)],
                complete_independent_reviewers=[uid for uid,items in independent.items() if set(items)==set(records)],
                independent_reviewer_comparisons={uid:score([report],list(items.values())) for uid,items in independent.items()},
                rejected_labels=rejected,
                note='Chỉ ghép nhãn đúng report/hash; tách nhãn có hỗ trợ hoặc chưa khai báo khỏi đối chiếu độc lập. Tự khai báo chưa chứng minh chuyên môn hay độc lập bên ngoài. Không sửa nhãn mù gốc.')
