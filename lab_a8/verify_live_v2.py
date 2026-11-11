"""Execute the 72 representative lab probes; not a human accuracy experiment."""
import argparse
import json
from pathlib import Path
from agent_core import a8_assessment as a8
from evidence_collectors.a8_live import LIVE_PROFILES,VERSION


def verify():
    expected={'conforming':'Compliant','mixed':'Partially Compliant','nonconforming':'Non-Compliant','incomplete':'Insufficient Evidence'}
    reports=[];checks=[]
    for profile in LIVE_PROFILES:
        snapshot=a8.capture(profile,'live')
        report=a8.run(profile,'rules','live',snapshot=snapshot)
        reports.append(report)
        for record in report['records']:
            checks.append(dict(profile=profile,control_id=record['control_id'],status=record['status'],
                expected_scenario_status=expected[profile],scenario_check_passed=record['status']==expected[profile],
                collection_errors=record['evidence']['collection_errors']))
        print('checked '+profile,flush=True)
    payload=dict(kind='engineering-scenario-verification',rubric_version=VERSION,is_human_accuracy=False,
                 note='Expected scenarios specified by lab designer; not independent labels or proof of full ISO coverage.',
                 checks=checks,reports=reports,total=len(checks),passed=sum(c['scenario_check_passed'] for c in checks))
    payload['sha256']=a8.digest(payload)
    return payload


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
    path=Path(args.output)
    if path.exists():parser.error('Choose a new output; never overwrite previous evidence')
    result=verify();path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2)
    print(json.dumps(dict(total=result['total'],passed=result['passed'])))
    raise SystemExit(0 if result['passed']==result['total'] else 1)
