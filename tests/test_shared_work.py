from contextlib import contextmanager
from unittest.mock import MagicMock
import pytest
from backend import shared_work


def control(cid='A.6.1', flow='COMPLETED', status='evaluated', supported=True):
    return dict(control_id=cid, workflow_status=flow, assessment_state=status,
                collector_supported=supported, latest_evaluation_id=10,
                conclusion='Partially Compliant', assigned_to='Alice', active_job_id='existing')


@pytest.mark.parametrize('flow,status,expected', [
    ('RUNNING','stale','running'), ('COMPLETED','stale','stale'),
    ('COMPLETED','evaluated','evaluated'), ('WAITING_EVIDENCE','evaluated','waiting_evidence'),
    ('NEEDS_REVIEW','evaluated','awaiting_review'), ('NOT_STARTED','not_evaluated','not_started')])
def test_state_separates_execution_from_compliance(flow,status,expected):
    assert shared_work.state(control(flow=flow,status=status)) == expected


def test_queue_skips_review_missing_evidence_and_unsupported(monkeypatch):
    rows=[control(),control('A.6.2','WAITING_EVIDENCE'),control('A.6.3','NEEDS_REVIEW'),
          control('A.6.4','NOT_STARTED','not_evaluated',False),
          control('A.6.5','NOT_STARTED','not_evaluated'), control('A.6.6',status='stale')]
    monkeypatch.setattr(shared_work,'dossier',lambda _: {'controls':rows})
    assert shared_work.board('a')['next_control_id']=='A.6.6'
    rows.pop()
    assert shared_work.board('a')['next_control_id']=='A.6.5'


@pytest.fixture
def claim_env(monkeypatch):
    con=MagicMock()
    @contextmanager
    def connection(): yield con
    monkeypatch.setattr(shared_work,'get_connection',connection)
    claim=MagicMock(return_value={'job_id':'new','workflow_status':'RUNNING'})
    monkeypatch.setattr(shared_work.teamwork,'claim_job',claim)
    return claim


@pytest.mark.parametrize('flow,expected', [('RUNNING','following'),('COMPLETED','reused'),('WAITING_EVIDENCE','reused'),('NEEDS_REVIEW','reused')])
def test_second_user_reuses_or_follows_without_worker(monkeypatch,claim_env,flow,expected):
    c=control(flow=flow); c['shared_state']=shared_work.state(c)
    monkeypatch.setattr(shared_work,'board',lambda _: {'controls':[c],'next_control_id':None})
    result=shared_work.start('assessment','second-user','A.6.1')
    assert result['action']==expected
    claim_env.assert_not_called()


def test_stale_result_runs_again_and_preserves_target(monkeypatch,claim_env):
    c=control(status='stale'); c['shared_state']='stale'
    monkeypatch.setattr(shared_work,'board',lambda _: {'controls':[c],'next_control_id':'A.6.1'})
    assert shared_work.start('assessment','Bob')['action']=='started'
    claim_env.assert_called_once_with('assessment','A.6.1','Bob')


def test_legacy_claim_race_follows_winner(monkeypatch,claim_env):
    c=control(status='not_evaluated',flow='NOT_STARTED');c['shared_state']='not_started'
    monkeypatch.setattr(shared_work,'board',lambda _: {'controls':[c],'next_control_id':'A.6.1'})
    claim_env.side_effect=ValueError('busy')
    monkeypatch.setattr(shared_work.teamwork,'progress_board',lambda _: [control(flow='RUNNING')])
    assert shared_work.start('assessment','Bob')['job_id']=='existing'


@pytest.mark.parametrize('method,path', [('GET','shared-work'),('POST','shared-work/start')])
def test_shared_routes_check_membership_before_read_or_claim(monkeypatch,method,path):
    from fastapi import HTTPException
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.team_api import require_user
    from backend import enterprise_api
    def deny(*args): raise HTTPException(403,'Not a member')
    monkeypatch.setattr(enterprise_api,'require_campaign',deny)
    app.dependency_overrides[require_user]=lambda: {'user_id':'u'}
    monkeypatch.setattr(shared_work,'board',lambda *_: pytest.fail('Must not read'))
    monkeypatch.setattr(shared_work,'start',lambda *_: pytest.fail('Must not claim'))
    try:
        with TestClient(app) as client:
            url='/api/assessments/7f7c009b-bdcd-5b33-934e-15251ad2c976/enterprise/'+path
            response=client.request(method,url,**({'json':{}} if method=='POST' else {}))
            assert response.status_code==403
    finally:
        app.dependency_overrides.pop(require_user,None)
