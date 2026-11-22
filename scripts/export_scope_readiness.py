"""Export a read-only 56-control handoff; never creates sources or decisions."""
import argparse
import csv
import json
import os
from pathlib import Path
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from agent_core.a8_assessment import digest
from backend.source_requests import markdown


def source_states(row):
    gaps=set(row['gaps'])
    states=[]
    if 'explicit_sources_missing' in gaps:states.append('MISSING_EVIDENCE')
    else:states.append('EVIDENCE_RECORDED')
    if 'source_content_unusable' in gaps:states.append('UNUSABLE_CONTENT')
    if 'source_integrity_failed' in gaps:states.append('INTEGRITY_FAILED')
    if any((s.get('source_quality') or {}).get('integrity',{}).get('state') != 'verified'
           for s in row['sources']):states.append('ORIGINAL_NOT_FULLY_VERIFIED')
    if 'human_criteria_review_not_current' in gaps or 'criteria_unknown' in gaps:
        states.append('COVERAGE_NOT_CONFIRMED')
    return states


def export(scope, directory):
    if scope['scope_total'] != 56 or len(scope['controls']) != 56:
        raise ValueError('Unexpected scope; expected 56 controls')
    packet=scope['handoff_packet']
    if packet['sha256'] != digest({k:v for k,v in packet.items() if k!='sha256'}):
        raise ValueError('Handoff hash mismatch')
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    metadata=dict(protocol='scope-readiness-export-v1',checked_at=datetime.now(ZoneInfo('Asia/Bangkok')).isoformat(),
        assessment_id=scope['assessment_id'],rubric_sha256=scope['rubric_sha256'],
        handoff_sha256=packet['sha256'],acceptance=scope['acceptance'],
        rubric_confirmed=bool(scope['rubric_approval']),soa_status=scope['soa']['approval'],
        human_assessment=False,read_only=True,
        note='A recorded or technically usable source is not proof of authenticity, coverage or compliance. '
             'Unknown metadata is not automatically a corruption. Independent accuracy is not asserted.')
    for name,value in [('snapshot.json',metadata),('handoff.json',packet),
                       ('source-requests.json',scope['source_requests']),('worklist.json',scope['acceptance_worklist'])]:
        with (directory/name).open('x',encoding='utf-8') as stream:
            json.dump(value,stream,ensure_ascii=False,indent=2)
    (directory/'source-requests.md').write_text(markdown(scope['source_requests']),encoding='utf-8')
    with (directory/'controls.csv').open('x',encoding='utf-8-sig',newline='') as stream:
        writer=csv.writer(stream)
        writer.writerow(['control_id','source_states','source_ids','machine_conclusion','current_human_conclusion','gaps'])
        for row in packet['controls']:
            writer.writerow([row['control_id'],';'.join(source_states(row)),
                ';'.join(s['evidence_id'] for s in row['sources']),row['machine_conclusion'],
                row['current_human_conclusion'] or '', ';'.join(row['gaps'])])
    return metadata


def main():
    from dotenv import load_dotenv
    load_dotenv(ROOT/'.env')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default='http://127.0.0.1:8000')
    parser.add_argument('--assessment-id',required=True)
    parser.add_argument('--output-dir',required=True)
    args=parser.parse_args()
    base=args.base_url.rstrip('/')
    # Prevent accidental credential forwarding to an external service.
    from urllib.parse import urlparse
    parsed=urlparse(base)
    if parsed.scheme!='http' or parsed.hostname not in ('127.0.0.1','localhost','::1') or parsed.username or parsed.password:
        parser.error('Use a local HTTP backend only')
    with requests.Session() as session:
        login=session.post(base+'/api/auth/login',json={
            'username':os.getenv('INITIAL_ADMIN_USERNAME','admin'),
            'password':os.environ['INITIAL_ADMIN_PASSWORD']},timeout=20)
        login.raise_for_status();session.headers['Authorization']='Bearer '+login.json()['access_token']
        try:
            response=session.get(base+'/api/assessments/'+args.assessment_id+'/enterprise/scope56',timeout=60)
            response.raise_for_status();result=export(response.json(),args.output_dir)
            print(json.dumps({'assessment_id':result['assessment_id'],'output':args.output_dir,'read_only':True}))
        finally:session.post(base+'/api/auth/logout',timeout=15).raise_for_status()


if __name__=='__main__':main()
