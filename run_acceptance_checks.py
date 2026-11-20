"""Non-destructive live API acceptance checks. Never labels or approves records."""
import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo
import requests


def check_response(response,expected):
    return dict(expected_status=expected,actual_status=response.status_code,passed=response.status_code==expected)


def run(base,accounts):
    report=dict(protocol='live-api-acceptance-v1',checked_at=datetime.now(ZoneInfo('Asia/Bangkok')).isoformat(),
        surface='API_ONLY',gui_tested=False,human_assessment=False,checks=[],missing_credentials=[])
    def record(name,response,expected,actor='anonymous'):
        report['checks'].append(dict(name=name,actor=actor,**check_response(response,expected)))
        return response
    record('Profile requires login',requests.get(base+'/api/auth/profile',timeout=15),401)
    foreign=str(uuid4())
    for username,password in accounts:
        if not password:report['missing_credentials'].append(username);continue
        session=requests.Session()
        try:
            response=session.post(base+'/api/auth/login',json={'username':username,'password':password},timeout=15)
            record('Login',response,200,username)
            if response.status_code!=200:continue
            session.headers['Authorization']='Bearer '+response.json()['access_token']
            me=record('Current account',session.get(base+'/api/auth/me',timeout=15),200,username).json()
            campaigns=record('Campaign membership',session.get(base+'/api/assessments',timeout=15),200,username).json()
            if not isinstance(campaigns,list) or not campaigns:
                report['checks'].append(dict(name='Campaign available',actor=username,passed=False));continue
            prefix=base+'/api/assessments/'+campaigns[0]['assessment_id']
            for name,path in [('Account profile','/api/auth/profile'),('56-control scope',prefix+'/enterprise/scope56'),
                ('Company inventory',prefix+'/enterprise/company'),('Shared dossier',prefix+'/enterprise/shared-work'),
                ('Batch history',prefix+'/enterprise/shared-work/batches'),('A8 catalog',prefix+'/a8/catalog?transport=live')]:
                record(name,session.get(path if path.startswith('http') else base+path,timeout=30),200,username)
            record('Reject foreign campaign',session.get(base+'/api/assessments/'+foreign+'/enterprise/company',timeout=15),403,username)
            if me.get('role')!='admin':
                record('Assessor cannot start batch',session.post(prefix+'/enterprise/shared-work/batches',json={},timeout=15),403,username)
                record('Assessor cannot approve SoA',session.post(prefix+'/enterprise/scope56/approval',json={'fingerprint':'0'*64,'note':'Automated authorization rejection check only.'},timeout=15),403,username)
            else:
                record('Invalid validation plan rejected',session.post(prefix+'/a8/candidate-runs/validate',json={'plan':{}},timeout=15),422,username)
        finally:
            if 'Authorization' in session.headers:
                record('Logout',session.post(base+'/api/auth/logout',timeout=15),200,username)
            session.close()
    report['passed']=bool(report['checks']) and all(c['passed'] for c in report['checks']) and not report['missing_credentials']
    report['note']='API behavior only. No evidence uploaded, model started, human label submitted or approval created. Not UI acceptance or ISO certification.'
    return report


def main():
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent/'.env')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default='http://127.0.0.1:8000')
    parser.add_argument('--output',required=True)
    args=parser.parse_args();output=Path(args.output)
    if output.exists():parser.error('Output exists; choose a new filename to keep prior results.')
    accounts=[(os.getenv('INITIAL_ADMIN_USERNAME','admin'),os.getenv('INITIAL_ADMIN_PASSWORD')),
              ('ledangkhoa',os.getenv('ACCEPTANCE_KHOA_PASSWORD')),('ledoanvantu',os.getenv('ACCEPTANCE_TU_PASSWORD'))]
    report=run(args.base_url.rstrip('/'),accounts)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as stream:json.dump(report,stream,ensure_ascii=False,indent=2)
    print(json.dumps({'passed':report['passed'],'checks':len(report['checks']),'output':str(output),'gui_tested':False}))
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
