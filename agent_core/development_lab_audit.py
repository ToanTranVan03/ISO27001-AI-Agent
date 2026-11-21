"""Read-only criterion-level disagreement audit against an assistant-authored key."""
from collections import Counter
import hashlib
import json
from agent_core.development_lab import build_bundle,expected_status,parse_result,designer_reference,reference_hash

LABELS={
 'key_unknown_model_not_met':'Khóa thiết kế chưa rõ, model kết luận không đạt',
 'key_met_model_unknown':'Khóa thiết kế ghi đạt, model yêu cầu thêm bằng chứng',
 'key_not_met_model_met':'Khóa thiết kế ghi không đạt, model ghi đạt',
 'other_verdict_difference':'Khác kết quả tiêu chí giữa model và khóa thiết kế',
 'technical_error':'Không có kết quả tiêu chí hợp lệ',
}


def audit(report,bundle=None,reference=None):
    bundle=bundle or build_bundle()
    current_reference=designer_reference()
    frozen=report.get('designer_reference_snapshot')
    if frozen is not None and reference_hash(frozen)!=report.get('designer_reference_sha256'):
        raise ValueError('Frozen designer key hash mismatch')
    reference=reference if reference is not None else frozen if frozen is not None else current_reference
    if report['bundle_sha256']!=bundle['sha256']:raise ValueError('Source bundle changed; cannot compare with current key')
    cases={c['control_id']:c for c in bundle['cases']}
    results=report.get('final_results',report['results'])
    if len({r['control_id'] for r in results})!=len(results):raise ValueError('Duplicate control result')
    rows=[];invalid=[];types=Counter()
    for result in results:
        cid=result['control_id']
        if cid not in cases:raise ValueError('Result outside source bundle')
        case=cases[cid]
        expected_hashes={a['filename']:a['sha256'] for a in case['artifacts']}
        if result['source_hashes']!=expected_hashes:raise ValueError('Source hashes do not match frozen bundle')
        error=result.get('error');checks={}
        if not error:
            try:
                parsed=parse_result(result['raw_response'],case)
                if parsed['status']!=result['status'] or parsed['checks']!=result['checks']:
                    raise ValueError('Saved status/checks disagree with original response')
                checks={c['criterion_index']:c for c in parsed['checks']}
            except (ValueError,KeyError,TypeError) as exc:error=str(exc)
        if error:invalid.append(dict(control_id=cid,error=error))
        key=reference[cid]['designer_verdicts']
        if len(key)!=len(case['criteria']):raise ValueError('Key criterion count mismatch')
        criteria=[]
        for i,text in enumerate(case['criteria']):
            check=checks.get(i);actual=check['verdict'] if check else None
            difference=actual!=key[i]
            code=None
            if difference:
                code='technical_error' if error else {
                    ('unknown','not_met'):'key_unknown_model_not_met',
                    ('met','unknown'):'key_met_model_unknown',
                    ('not_met','met'):'key_not_met_model_met',
                }.get((key[i],actual),'other_verdict_difference')
                types[code]+=1
            criteria.append(dict(criterion_index=i,criterion=text,designer_verdict=key[i],model_verdict=actual,
                differs=difference,category=code,category_label=LABELS.get(code),
                model_rationale=check['rationale'] if check else None,
                citations=[dict(filename=name,sha256=expected_hashes[name]) for name in check['source_files']] if check else []))
        rows.append(dict(control_id=cid,name=case['name'],designer_status=expected_status(key),model_status=result['status'] if not error else None,
            status_differs=bool(error) or result['status']!=expected_status(key),error=error,criteria=criteria,
            differing_criteria=sum(c['differs'] for c in criteria),review_state='PENDING_HUMAN_REVIEW'))
    payload=dict(protocol='development-criterion-audit-v1',run_id=report['run_id'],bundle_sha256=bundle['sha256'],
        report_sha256=hashlib.sha256(json.dumps(report,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),
        is_synthetic=True,independent_validation=False,key_authority='ASSISTANT_DESIGNER_NOT_PROFESSIONALLY_VALIDATED',
        key_binding='FROZEN_BEFORE_RUN' if frozen is not None else 'LEGACY_CURRENT_KEY_NOT_FROZEN',
        designer_reference_sha256=reference_hash(reference),key_matches_current=reference_hash(reference)==reference_hash(current_reference),
        result_stage='after_one_retry' if report.get('repair_attempts') else 'first_attempt',
        controls_audited=len(rows),pending_controls=sorted(set(cases)-{r['control_id'] for r in rows}),
        controls_with_status_difference=sum(r['status_differs'] for r in rows),
        controls_with_criterion_difference=sum(bool(r['differing_criteria']) for r in rows),
        differing_criteria=sum(r['differing_criteria'] for r in rows),categories=dict(types),invalid_results=invalid,controls=rows,
        note='Đối chiếu khóa thiết kế do trợ lý soạn; khác biệt là mục cần rà, chưa chứng minh model hoặc khóa đúng/sai. Không thay nhãn, nguồn hoặc phê duyệt.')
    return payload
