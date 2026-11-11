import base64
import json
import subprocess
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from agent_core import a8_assessment as a8
from evidence_collectors import a8_live as live
from test_a8_assessment import api_env  # Shared isolated API storage/actors.


def control(cid):
    return next(c for c in a8.catalog('live') if c['control_id']==cid)


def encoded(fields):
    fields={'observed_at':datetime.now(timezone.utc).isoformat(),'asset_id':'test-container',**fields}
    return '\n'.join(k+'\t'+('MISSING' if v is None else base64.b64encode(v.encode()).decode())
                     for k,v in fields.items()).encode()


def probe(monkeypatch,fields):
    mock=MagicMock(return_value=SimpleNamespace(returncode=0,stdout=encoded(fields)))
    monkeypatch.setattr(live.subprocess,'run',mock)
    return mock


def test_live_catalog_is_separate_and_does_not_mutate_replay():
    original=a8.catalog()
    current=a8.catalog('live')
    assert len(current)==18 and set(live.LIVE_IDS)=={c['control_id'] for c in current}
    assert a8.digest(current)!=a8.digest(original)
    assert all(c['rubric_version']=='a8-live-v2-active' for c in current)
    assert a8.catalog()==original


def test_unsupported_live_control_never_uses_fixture_or_model(monkeypatch):
    mock=MagicMock(side_effect=AssertionError('Must not invoke a command'))
    monkeypatch.setattr(live.subprocess,'run',mock)
    monkeypatch.setattr(a8.ollama,'Client',MagicMock(side_effect=AssertionError('Must not invoke model')))
    c=control('A.8.1');c['control_id']='A.8.99';e=live.collect_live('mixed',c)
    assert set(e['facts'].values())=={None}
    assert e['collection_errors'][0]['error']=='live_probe_not_implemented'
    assert a8.assess(c,e,'llm')['execution_source']=='evidence-availability-check'


@pytest.mark.parametrize('rc,expected',[('0',False),('1',True),('127',None)])
def test_installation_checks_actual_exit_code_and_inventory(monkeypatch,rc,expected):
    mock=probe(monkeypatch,{'install_access_rc':rc,'install_stat':'755 root root','installed.tsv':'bash\t1\n','approved.tsv':'bash\t1\n'})
    e=live.collect_live('conforming',control('A.8.19'))
    assert list(e['facts'].values())==[expected,True]
    args=mock.call_args.args[0]
    assert args==['docker','exec','iso-a8-lab','/bin/sh','/live_probe.sh','conforming','A.8.19']
    assert 'shell' not in mock.call_args.kwargs


def test_restore_missing_is_unknown_and_changed_backup_fails(monkeypatch):
    probe(monkeypatch,{'backup.dat':'changed','backup.sha256':'0'*64,'restored.dat':None})
    e=live.collect_live('incomplete',control('A.8.13'))
    assert list(e['facts'].values())==[False,None]
    assert a8.rules(e)['status']=='Insufficient Evidence'


def test_live_failure_and_stale_time_do_not_pass(monkeypatch):
    mock=probe(monkeypatch,{'observed_at':'2020-01-01T00:00:00+00:00','install_access_rc':'1'})
    e=live.collect_live('conforming',control('A.8.19'))
    assert set(e['facts'].values())=={None} and e['collection_errors']
    mock.side_effect=subprocess.TimeoutExpired('docker',15)
    e=live.collect_live('conforming',control('A.8.19'))
    assert set(e['facts'].values())=={None}


def test_live_profile_and_field_injection_rejected(monkeypatch):
    with pytest.raises(ValueError):live.collect_live('../../host',control('A.8.13'))
    with pytest.raises(ValueError):live._parse(b'unknown\tZg==')
    with pytest.raises(ValueError):live._parse(b'asset_id\tYQ==\nasset_id\tYg==')


def test_unsupported_model_conclusion_is_error_never_replaced(monkeypatch):
    c=control('A.8.13')
    e={'evidence_id':'E1','control_id':c['control_id'],'asset_id':'asset','facts':dict(zip(c['checks'],[True,None])),
       'is_synthetic':True,'artifacts':[{'artifact':'backup.dat','content':'x'}]}
    client=MagicMock()
    client.chat.return_value={'message':{'content':json.dumps({'status':'Partially Compliant','rationale':'bad', 'evidence_ids':['E1']})}}
    monkeypatch.setattr(a8.ollama,'Client',lambda **_:client)
    with pytest.raises(a8.UnsupportedConclusion):a8.assess(c,e,'llm')
    assert client.chat.call_args.kwargs['format']=='json'


def test_model_cannot_promote_mixed_facts_to_a_definitive_status(monkeypatch):
    c=control('A.8.3')
    e={'evidence_id':'E1','control_id':c['control_id'],'asset_id':'asset',
       'facts':dict(zip(c['checks'],[True,False])),'is_synthetic':True,'artifacts':[{'content':'review rejected'}]}
    client=MagicMock()
    client.chat.return_value={'message':{'content':json.dumps({'status':'Non-Compliant','rationale':'bad','evidence_ids':['E1']})}}
    monkeypatch.setattr(a8.ollama,'Client',lambda **_:client)
    with pytest.raises(a8.RubricConclusionMismatch) as exc:a8.assess(c,e,'llm')
    assert exc.value.diagnostic['proposed_status']=='Non-Compliant'
    assert exc.value.diagnostic['rubric_status']=='Partially Compliant'


def test_live_api_has_no_replay_labels_and_preserves_blindness(api_env,monkeypatch):
    from backend.main import app
    from fastapi.testclient import TestClient
    api,actor=api_env
    monkeypatch.setattr(api,'runtime_status',lambda:'running')
    # An entirely unavailable source is useful here: no real engine or Docker access.
    monkeypatch.setattr(live.subprocess,'run',MagicMock(side_effect=OSError()))
    base='/api/assessments/7f7c009b-bdcd-5b33-934e-15251ad2c976/a8'
    with TestClient(app) as client:
        assert client.post(base+'/runs',json={'transport':'live','profile':'stale'}).status_code==422
        created=client.post(base+'/runs',json={'transport':'live','profile':'mixed','mode':'rules'}).json()
        assert 'designer_reference' not in created
        assert api.read(created['assessment_id'],created['run_id'])['designer_reference']==[]
        api.worker(created['assessment_id'],created['run_id'],'mixed','rules','live')
        result=client.get(base+'/runs/'+created['run_id']).json()
        assert all(r['rated']==0 and r['accuracy'] is None for r in result['designer_comparison']['per_control'])
        assert result['readiness']['complete_independent_reviewers']==0
        cohort=client.get(base+'/summary').json()['cohorts'][0]
        assert cohort['transport']=='live' and all(r['rated']==0 for r in cohort['designer']['per_control'])
        actor['user_id']='independent-reviewer'
        hidden=client.get(base+'/runs/'+created['run_id']).json()
        assert hidden['blind'] and 'readiness' not in hidden and 'report' not in hidden
