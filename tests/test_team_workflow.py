"""Unit tests for evidence-first and multi-user API wiring (requires project dependencies)."""
import pytest
from fastapi.testclient import TestClient
from backend import main, teamwork
from backend import team_api
from agent_core import graph_builder


@pytest.fixture(autouse=True)
def suppress_db_startup(monkeypatch):
    monkeypatch.setattr(main.database,'initialize_database',lambda:None)
    monkeypatch.setattr(main.teamwork,'init_teamwork',lambda:None)
    monkeypatch.setattr(main.enterprise_lab,'init_enterprise_lab',lambda:None)
    yield
    main.app.dependency_overrides.clear()


def test_password_hash_is_salted_and_checked():
    a=teamwork.hash_password('really_long_password_123')
    b=teamwork.hash_password('really_long_password_123')
    assert a!=b
    assert teamwork.verify_password('really_long_password_123',a)
    assert not teamwork.verify_password('wrong_password',a)
    with pytest.raises(ValueError):
        teamwork.hash_password('short')


def test_unauthenticated_progress_rejected():
    with TestClient(main.app) as client:
        response=client.get('/api/assessments/00000000-0000-0000-0000-000000000001/progress')
    assert response.status_code==401


def test_verify_unknown_id_becomes_insufficient():
    state={
        'control_id':'A.6.1','collected_evidences':[{'evidence_id':'good-1'}],
        'proposed_evidence_ids':['invented-id'],'compliance_status':'Compliant',
        'confidence':.95,'rationale':'claim without verified evidence','audit_trail':[],
    }
    outcome=graph_builder.node_verify(state)
    assert outcome['compliance_status']=='Insufficient Evidence'
    assert outcome['validated_evidence_ids']==[]


def test_verify_only_traces_real_cited_ids():
    state={
        'collected_evidences':[{'evidence_id':'good-1'},{'evidence_id':'good-2'}],
        'proposed_evidence_ids':['good-2','hallucinated','good-2'],
        'compliance_status':'Partially Compliant','confidence':.8,
        'rationale':'some evidence','audit_trail':[],
    }
    outcome=graph_builder.node_verify(state)
    assert outcome['validated_evidence_ids']==['good-2']
    assert outcome['compliance_status']=='Partially Compliant'


def test_claimed_control_endpoint_starts_one_job(monkeypatch):
    calls=[]
    actor={'user_id':'00000000-0000-0000-0000-000000000002','role':'assessor','display_name':'X'}
    main.app.dependency_overrides[team_api.require_user]=lambda:actor
    monkeypatch.setattr(team_api,'require_campaign',lambda *a:None)
    monkeypatch.setattr(team_api.database,'get_control',lambda _: {'control_id':'A.6.1'})
    monkeypatch.setattr(team_api.teamwork,'claim_job',lambda *args: {'job_id':'00000000-0000-0000-0000-000000000003','workflow_status':'RUNNING'})
    monkeypatch.setattr(team_api.executor,'submit',lambda *args:calls.append(args))
    with TestClient(main.app) as client:
        response=client.post('/api/assessments/00000000-0000-0000-0000-000000000001/controls/A.6.1/run')
    assert response.status_code==202
    assert len(calls)==1
