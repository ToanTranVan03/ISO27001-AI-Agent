import json
from pathlib import Path
from agent_core.review_quality import inspect_rationale,pending_quality_reviews
from test_a8_assessment import api_env


def report():return json.loads(Path('docs/a8-results/live-v2-ollama-pilot.json').read_text(encoding='utf-8'))['report']


def test_filler_is_blocked_and_real_time_reasoning_is_not():
    r=report()
    assert inspect_rationale(r,'A.8.2','s d f '+('f'*60),[])['blocked']
    check=inspect_rationale(r,'A.8.17','signature_verify_rc=0, offset_ms=5000.164 exceeds policy.',[])
    assert not check['blocked'] and not check['issues']


def test_copy_from_other_source_warns_without_inventing_a_grade():
    check=inspect_rationale(report(),'A.8.17','delivery_receipts is empty; monitoring failed.',[])
    assert any(i['code']=='references_other_control_sources' for i in check['issues'])
    assert 'status' not in check
    duplicate=inspect_rationale(report(),'A.8.2','Same deliberate review explanation.',[
        dict(control_id='A.8.1',rationale='Same deliberate review explanation.')])
    assert any(i['code']=='duplicate_other_control' for i in duplicate['issues'])


def test_preview_and_submit_validate_without_exposing_answers(api_env):
    from backend.main import app
    from fastapi.testclient import TestClient
    api,actor=api_env;aid='7f7c009b-bdcd-5b33-934e-15251ad2c976';rid='00000000-0000-0000-0000-000000000099'
    doc=dict(run_id=rid,created_by='starter',created_at='test',mode='llm',profile='mixed',
        state='finished',report=report(),reviews=[],review_protocol=api.REVIEW_PROTOCOL)
    api.save(api.folder(aid)/(rid+'.json'),doc)
    actor.update(user_id='reviewer',role='assessor')
    base=f'/api/assessments/{aid}/a8/runs/{rid}'
    with TestClient(app) as client:
        payload=dict(control_id='A.8.1',expected='Partially Compliant',rationale='s d f '+('f'*70),report_sha256=doc['report']['sha256'])
        assert client.post(base+'/reviews',json=payload).status_code==422
        assert api.read(aid,rid)['reviews']==[]
        payload['rationale']='Test reviewer read the recorded observations.'
        assert client.post(base+'/reviews',json=payload).status_code==200
        payload['control_id']='A.8.2'
        preview=client.post(base+'/review-check',json={k:payload[k] for k in ('control_id','rationale')}).json()
        assert preview['issues'] and not {'status','facts','expected','reviews'}&preview.keys()
        assert client.post(base+'/reviews',json=payload).status_code==409
        payload['quality_warning_acknowledged']=True
        assert client.post(base+'/reviews',json=payload).status_code==200
        assert api.read(aid,rid)['reviews'][-1]['quality_warning_acknowledged']
        assert not pending_quality_reviews(doc['report'],api.read(aid,rid)['reviews'])
        # Acknowledging a warning must not allow overwriting a locked review.
        assert client.post(base+'/reviews',json=payload).status_code==409


def test_historical_filler_cannot_unlock_soa_approval_even_with_independence_flags(api_env):
    from backend.main import app
    from fastapi.testclient import TestClient
    from test_a8_completion import label
    api,actor=api_env;aid='7f7c009b-bdcd-5b33-934e-15251ad2c976';rid='00000000-0000-0000-0000-000000000088'
    r=report();labels=[label(r,i,'reviewer','Partially Compliant') for i in range(18)]
    for item in labels:item['rationale']='Test-only independent declaration for '+item['control_id']
    labels[0]['rationale']='s d f '+('f'*80)
    doc=dict(run_id=rid,created_by='starter',state='finished',report=r,reviews=labels,review_protocol=api.REVIEW_PROTOCOL)
    api.save(api.folder(aid)/(rid+'.json'),doc)
    before=(api.folder(aid)/(rid+'.json')).read_bytes()
    with TestClient(app) as client:
        result=client.post(f'/api/assessments/{aid}/a8/runs/{rid}/soa-approval',json=dict(
            note='Test only: must not approve invalid rationale',decisions=[dict(control_id=x['control_id'],applicable=True,
            reason='Test decision, not a real approval',treatment='Test treatment, not an actual plan') for x in r['records']]))
        assert result.status_code==409
        assert 'Căn cứ' in result.json()['detail']
    assert before==(api.folder(aid)/(rid+'.json')).read_bytes()
