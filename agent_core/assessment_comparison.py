"""Read-only A.8 run comparison; changed conclusions do not prove remediation."""
from agent_core.a8_assessment import digest


def compare_reports(before, after):
    for report in (before, after):
        if report.get('sha256') != digest({k:v for k,v in report.items() if k != 'sha256'}):
            raise ValueError('Report hash mismatch')
        ids = [r['control_id'] for r in report['records']]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate controls in report')
    old = {r['control_id']:r for r in before['records']}
    new = {r['control_id']:r for r in after['records']}
    if old.keys() != new.keys():
        raise ValueError('Control sets differ; do not compare different scopes')
    same_recipe = all(before.get(k) == after.get(k) for k in
                      ('catalog_sha256','rubric_version','implementation_sha256','mode','model','generation_options','transport'))
    rows=[]
    for cid, first in old.items():
        second=new[cid]
        source_changed=first['evidence']['source_sha256'] != second['evidence']['source_sha256']
        rows.append(dict(control_id=cid,source_changed=source_changed,
            before_evidence_sha256=first['evidence']['source_sha256'],
            after_evidence_sha256=second['evidence']['source_sha256'],
            before_status=first.get('status'),after_status=second.get('status'),
            before_error=first.get('error'),after_error=second.get('error'),
            status_changed=first.get('status') != second.get('status'),
            interpretation='ENGINE_ERROR_REQUIRES_REVIEW' if first.get('error') or second.get('error') else
                'RECIPE_CHANGED_NOT_ATTRIBUTABLE_TO_REMEDIATION' if not same_recipe else
                'SOURCE_CHANGED_REQUIRES_REVIEW' if source_changed else
                'SAME_SOURCE_OUTPUT_CHANGED' if first.get('status') != second.get('status') else 'SAME_SOURCE_SAME_STATUS'))
    result=dict(protocol='a8-run-comparison-v1',before_report_sha256=before['sha256'],
        after_report_sha256=after['sha256'],same_recipe=same_recipe,controls=rows,
        remediation_verified=False,independent_validation=False,
        note='Technical comparison only. New capture hashes can include timestamps; inspect original artifacts. '
             'A changed conclusion is not proof of remediation. Human confirmation remains required.')
    result['sha256']=digest(result)
    return result


def main():
    import argparse
    import json
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before',required=True)
    parser.add_argument('--after',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    def load(path):
        doc=json.loads(Path(path).read_text(encoding='utf-8-sig'))
        return doc.get('report',doc)
    result=compare_reports(load(args.before),load(args.after))
    output=Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2)
    print(json.dumps({'controls':len(result['controls']),'same_recipe':result['same_recipe'],'output':str(output)}))


if __name__=='__main__':main()
