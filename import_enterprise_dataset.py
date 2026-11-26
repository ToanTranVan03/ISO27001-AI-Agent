"""Import generated DEVELOPMENT data through authorized APIs into NEW clients only.

Credentials are read from ISO_IMPORT_USERNAME / ISO_IMPORT_PASSWORD. No model calls,
design keys, labels, approvals or existing-client mutations are performed.
"""
import argparse
import csv
import calendar
from datetime import date
import json
import os
from pathlib import Path
from urllib.parse import urlparse
import requests
from generate_enterprise_dataset import validate

MAPPING={'people.csv':'A.6.1','screening.csv':'A.6.1','accounts.csv':'A.6.5','assets.csv':'A.8.1','backup-observations.json':'A.8.13','conflicting-observations.json':'A.8.24'}


def import_dataset(root,base,receipt_path,execute=False):
    root=Path(root).resolve();receipt_path=Path(receipt_path)
    if receipt_path.exists():raise ValueError('Receipt exists; preserve prior import history')
    checked=validate(root)
    if not checked['passed']:raise ValueError('Dataset validation failed')
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    plan=dict(protocol='synthetic-api-import-v1',synthetic=True,independent_validation=False,model_called=False,clients=[],errors=[])
    if not execute:return dict(plan,preflight_only=True,enterprises=len(manifest['enterprises']),periods=sum(len(e['periods']) for e in manifest['enterprises']))
    parsed=urlparse(base)
    if parsed.scheme not in ('http','https') or parsed.hostname not in ('localhost','127.0.0.1','::1') or parsed.username or parsed.password:
        raise ValueError('Importer accepts a local API only, without URL credentials')
    session=requests.Session()
    def call(method,path,**kwargs):
        response=session.request(method,base.rstrip('/')+path,timeout=120,**kwargs);response.raise_for_status();return response.json()
    auth=call('POST','/api/auth/login',json={'username':os.environ['ISO_IMPORT_USERNAME'],'password':os.environ['ISO_IMPORT_PASSWORD']})
    session.headers['Authorization']='Bearer '+auth['access_token']
    def persist():
        receipt_path.parent.mkdir(parents=True,exist_ok=True)
        receipt_path.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    try:
        for enterprise in manifest['enterprises']:
            periods=enterprise['periods'];first=periods[0]
            def period_input(period):
                start=date.fromisoformat(period['observed_at']);end=start.replace(day=calendar.monthrange(start.year,start.month)[1])
                return dict(name='SYNTHETIC '+period['period'],isms_scope='Generated development dataset; not an actual enterprise audit or independent evaluation',period_start=start.isoformat(),period_end=end.isoformat(),assessment_kind='monthly')
            profile=dict(name='SYNTHETIC '+enterprise['enterprise_id'],sector='Synthetic development only',contact='Generated fixture — no real person',locations='Isolated demonstration',data_classification='synthetic_development',campaign=period_input(first))
            created=call('POST','/api/clients',json=profile);client=dict(client_id=created['client_id'],enterprise_id=enterprise['enterprise_id'],periods=[]);plan['clients'].append(client);persist()
            for index,period in enumerate(periods):
                campaign=created['campaign'] if index==0 else call('POST',f"/api/clients/{created['client_id']}/campaigns",json=period_input(period))
                aid=campaign['assessment_id'];prefix=f'/api/assessments/{aid}';item=dict(assessment_id=aid,period=period['period'],sources=[],inventory_loaded=False);client['periods'].append(item);persist()
                scope=call('GET',prefix+'/enterprise/scope56');controls={c['control_id']:c for c in scope['controls']}
                folder=(root/period['directory']).resolve()
                if not folder.is_relative_to(root):raise ValueError('Unsafe period path')
                # Structured inventory stays declared context, never fabricated proof.
                people=list(csv.DictReader((folder/'people.csv').open(encoding='utf-8')))
                if len(people)>999:raise ValueError('Inventory API currently supports EMP-001..EMP-999')
                snapshot=call('GET',prefix+'/enterprise/company')
                for person in people:
                    response=call('PUT',prefix+'/enterprise/company/inventory/person/'+person['employee_id'],json=dict(name=person['name'],department=person['department'],job_title='Synthetic fixture role',employment_status=person['status'],note='SYNTHETIC DEVELOPMENT: no real employee or compliance assertion',expected_snapshot_hash=snapshot['snapshot_hash']))
                    snapshot=response['snapshot']
                for filename,kind in [('accounts.csv','account'),('assets.csv','asset')]:
                    with (folder/filename).open(encoding='utf-8',newline='') as stream:
                        for row in csv.DictReader(stream):
                            identifier=row['account_id'] if kind=='account' else row['asset_id']
                            body=dict(name='SYNTHETIC '+identifier,employee_id=row['employee_id'],department=row.get('department','Synthetic department'),note='SYNTHETIC DEVELOPMENT directory declaration; not verified compliance',expected_snapshot_hash=snapshot['snapshot_hash'])
                            if kind=='account':body['active']={'True':True,'False':False}.get(row['active'])
                            else:body['asset_type']=row['asset_type']
                            response=call('PUT',prefix+f'/enterprise/company/inventory/{kind}/{identifier}',json=body)
                            snapshot=response['snapshot']
                item['inventory_loaded']=True;persist()
                for filename,cid in MAPPING.items():
                    file=folder/filename
                    if not file.exists():continue
                    try:
                        response=call('POST',prefix+f'/enterprise/scope56/controls/{cid}/sources/upload',data=dict(evidence_type=controls[cid]['expected_evidence_types'][0],origin='SYNTHETIC DEVELOPMENT DATA — not independent or production',observed_at=period['observed_at']+'T00:00:00+00:00',note='Generated fixture, no expert labels or approval. Period '+period['period']),files={'file':(filename,file.read_bytes(),'application/octet-stream')})
                        item['sources'].append(dict(file=filename,control_id=cid,evidence_id=response['evidence_id']))
                    except requests.RequestException as exc:item['sources'].append(dict(file=filename,control_id=cid,error=type(exc).__name__));plan['errors'].append(dict(assessment_id=aid,file=filename,error=type(exc).__name__))
                    persist()
        plan['completed']=True;persist();return plan
    except Exception as exc:
        plan['completed']=False;plan['errors'].append(dict(stage='import',error=type(exc).__name__));persist();raise
    finally:
        try:session.post(base.rstrip('/')+'/api/auth/logout',timeout=15)
        finally:session.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--dataset',required=True);parser.add_argument('--base',default='http://127.0.0.1:8000');parser.add_argument('--receipt',required=True);parser.add_argument('--execute',action='store_true')
    args=parser.parse_args();result=import_dataset(args.dataset,args.base,args.receipt,args.execute)
    print(json.dumps({k:v for k,v in result.items() if k!='clients'},ensure_ascii=True))
