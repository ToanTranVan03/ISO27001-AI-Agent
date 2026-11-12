"""Explicit machine-generated rubric review, isolated from human rating storage."""
from copy import deepcopy
from hashlib import sha256
from agent_core.a8_assessment import digest, rules
from agent_core.a8_benchmark import score


def simulate(report):
    if digest({k:v for k,v in report.items() if k!='sha256'}) != report.get('sha256'):
        raise ValueError('Report hash mismatch')
    labels=[]
    seen=set()
    for record in report['records']:
        cid=record['control_id']
        if cid in seen: raise ValueError('Duplicate control')
        seen.add(cid)
        evidence=record['evidence']
        facts=evidence['facts']
        if not record['criteria_checks'] or set(facts)!=set(record['criteria_checks']):
            raise ValueError('Criteria/facts mismatch')
        for artifact in evidence.get('artifacts',[]):
            if sha256(artifact['content'].encode()).hexdigest()!=artifact['sha256']:
                raise ValueError('Artifact hash mismatch')
        # Apply the declared lab rubric, not the model prediction or designer key.
        expected=rules(evidence)['status']
        criteria=[dict(check=key,value=facts[key],verdict='unknown' if facts[key] is None else
                       'met' if facts[key] else 'not_met',evidence_id=evidence['evidence_id'])
                  for key in record['criteria_checks']]
        labels.append(dict(control_id=cid,case_id=record['case_id'],expected=expected,
            reviewer_id='SIMULATED-RUBRIC-REVIEWER',reviewer_name='Bộ chấm giả lập theo rubric lab',
            label_origin='simulated-rubric-v1',assistance='ai_assisted',prior_exposure='yes',
            is_simulated=True,eligible_for_human_comparison=False,
            report_sha256=report['sha256'],evidence_sha256=evidence['source_sha256'],criteria=criteria,
            rationale='; '.join(f"{c['check']}={c['value']} ({c['verdict']})" for c in criteria)))
    result=dict(protocol='simulated-review-v1',is_simulated=True,source_report_sha256=report['sha256'],
        reviewer_kind='deterministic-rubric-simulator',labels=labels,
        simulated_comparison=score([deepcopy(report)],labels),
        human_label_count=0,eligible_for_soa_approval=False,
        note='Chấm giả lập từ facts đã parse và rubric lab dùng chung với guard. Không phải người thật, chấm mù, đọc nguồn độc lập hay accuracy chuyên gia. Không ghi vào nhãn người chấm hoặc phê duyệt SoA.')
    result['sha256']=digest(result)
    return result
