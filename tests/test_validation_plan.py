from copy import deepcopy
from hashlib import sha256
import pytest
from agent_core import a8_assessment as a8
from agent_core.a8_protocol import prepare
from backend.validation_plan import validate_candidate
from test_a8_assessment import api_env


def reseal(plan):
    snap=plan['snapshot'];snap['sha256']=a8.digest({k:v for k,v in snap.items() if k!='sha256'})
    plan['sha256']=a8.digest({k:v for k,v in plan.items() if k!='sha256'})
    return plan


def candidate():
    import tempfile,shutil
    from pathlib import Path
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory)
        shutil.copytree(a8.LAB/'raw/mixed',root/'mixed')
        for p in (root/'mixed').glob('*/*'):
            if p.is_file() and p.name!='capture.json':p.write_bytes(p.read_bytes()+b'\n')
        return prepare('mixed','files','Test coordinator','Synthetic whitespace-modified regression ONLY, not held-out data',raw_root=root)


def test_candidate_plan_detects_tampering_and_does_not_accept_fixture_declaration():
    plan=candidate();assert validate_candidate(plan)==plan
    for edit in ('hash','recipe','artifact','facts','overlap','independence'):
        bad=deepcopy(plan)
        if edit=='hash':bad['coordinator']='changed'
        elif edit=='recipe':bad['recipe']['model']='different';reseal(bad)
        elif edit=='artifact':bad['snapshot']['evidence'][0]['artifacts'][0]['content']='modified';reseal(bad)
        elif edit=='facts':
            first=bad['snapshot']['evidence'][0];key=next(iter(first['facts']));first['facts'][key]=not first['facts'][key];reseal(bad)
        elif edit=='overlap':
            bad=prepare('mixed','files','Test','Known fixture is not a candidate')
            bad.update(dataset_usage='external-candidate-pending-independent-review',known_fixture_overlap_controls=[])
            for e in bad['snapshot']['evidence']:e['source_kind']='external-lab-candidate-unverified'
            reseal(bad)
        else:bad['independent_validation']=True;reseal(bad)
        with pytest.raises(ValueError):validate_candidate(bad)


def test_candidate_run_is_admin_only_frozen_and_blind(api_env,monkeypatch):
    from backend.main import app
    from fastapi.testclient import TestClient
    api,actor=api_env;aid='7f7c009b-bdcd-5b33-934e-15251ad2c976';base=f'/api/assessments/{aid}/a8'
    plan=candidate()
    with TestClient(app) as client:
        actor.update(user_id='reviewer',role='assessor')
        assert client.post(base+'/candidate-runs',json=dict(plan=plan,mode='rules')).status_code==403
        actor.update(user_id='starter',role='admin')
        response=client.post(base+'/candidate-runs',json=dict(plan=plan,mode='rules'))
        assert response.status_code==202
        rid=response.json()['run_id']
        assert not response.json()['independent_validation']
        assert client.post(base+'/candidate-runs',json=dict(plan=plan,mode='rules')).status_code==409
        monkeypatch.setattr(a8,'collect',lambda *_:pytest.fail('Do not recollect frozen candidate'))
        api.candidate_worker(aid,rid,plan,'rules')
        saved=api.read(aid,rid)
        assert saved['state']=='finished' and saved['designer_reference']==[]
        assert saved['report']['capture_sha256']==plan['snapshot']['sha256']
        actor.update(user_id='reviewer',role='assessor')
        blind=client.get(base+'/runs/'+rid).json()
        assert blind['blind'] and blind['can_review'] and 'report' not in blind and 'protocol' not in blind
        assert all('facts' not in c['evidence'] for c in blind['evidence_pack'])


def test_candidate_export_does_not_inherit_designer_key(tmp_path):
    from agent_core.a8_protocol import execute
    from agent_core.a8_teacher_pipeline import export_all_deliverables
    result=execute(candidate(),'rules')['report']
    exported=export_all_deliverables([result],tmp_path/'out')
    assert all(row['rated']==0 for row in exported['designer_comparisons'][0]['comparison']['per_control'])
    assert not exported['human_comparisons'][0]['analysis']['complete_reviewers']
