from copy import deepcopy
from fastapi.testclient import TestClient
from test_a8_assessment import api_env
from agent_core.a8_assessment import run


def test_both_assessors_can_distinguish_history_and_current_blind_runs(api_env):
    from backend.main import app
    api,actor=api_env
    aid='7f7c009b-bdcd-5b33-934e-15251ad2c976'
    old='00000000-0000-0000-0000-000000000001'
    new='00000000-0000-0000-0000-000000000002'
    doc=dict(run_id=old,created_by='admin',created_at='2026-11-10',state='finished',mode='rules',profile='mixed',reviews=[],report=run('mixed','rules'))
    api.save(api.folder(aid)/(old+'.json'),doc)
    current=deepcopy(doc);current.update(run_id=new,created_at='2026-11-15',review_protocol=api.REVIEW_PROTOCOL)
    api.save(api.folder(aid)/(new+'.json'),current)
    base=f'/api/assessments/{aid}/a8/runs'
    with TestClient(app) as client:
        for uid in ('khoa','tu'):
            actor.update(user_id=uid,role='assessor')
            rows=client.get(base).json()
            assert rows[0]['can_review'] and rows[0]['has_artifacts']
            assert not rows[1]['can_review']
            assert all(r['profile']=='Ẩn hồ sơ' and 'report' not in r for r in rows)
            assert client.get(base+'/'+old).json()['can_review'] is False
            pack=client.get(base+'/'+new).json()
            assert pack['can_review'] and 'report' not in pack
            assert all('facts' not in r['evidence'] for r in pack['evidence_pack'])
    assert api.read(aid,old)==doc and api.read(aid,new)==current
