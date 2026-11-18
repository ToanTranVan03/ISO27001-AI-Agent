import copy
from contextlib import contextmanager,nullcontext
from unittest.mock import MagicMock
import pytest
from backend import batch_work as batch


def control(cid='A.8.13',state='stale'):
    return dict(control_id=cid,shared_state=state,collector_supported=False,criteria=['probe criterion'],
        evidence=[dict(evidence_id=cid,sha256_hash='source-hash',is_synthetic=False,source_quality={'usable':True})])


def test_source_only_bounded_plan_skips_fresh_missing_and_lab_presets():
    good=control();fresh=control('A.8.15','evaluated');bad=control('A.8.16');bad['evidence'][0]['source_quality']['usable']=False
    preset=control('A.6.1');preset.update(evidence=[],collector_supported=True)
    rows=[good,fresh,bad,preset,control('A.8.19','running')]
    assert [c['control_id'] for c in batch.plan_controls({'controls':rows})]==['A.8.13']
    assert len(batch.plan_controls({'controls':rows},1,True))==1
    assert len(batch.plan_controls({'controls':rows},56,True))==2
    with pytest.raises(ValueError):batch.plan_controls({'controls':rows},57)
    token=batch.source_token(good);good['evidence'][0]['sha256_hash']='changed';assert batch.source_token(good)!=token


@pytest.fixture
def worker(monkeypatch):
    rows=[control(),control('A.8.15')]
    state=dict(batch_id='batch',assessment_id='assessment',created_by='coordinator',status='RUNNING',
               plan=batch.plan_controls({'controls':rows}),results=[])
    cur=MagicMock();cur.fetchone.return_value=[True]
    class Connection:
        def cursor(self):return nullcontext(cur)
    @contextmanager
    def connect():yield Connection()
    monkeypatch.setattr(batch,'get_connection',connect)
    monkeypatch.setattr(batch,'get',lambda *args:copy.deepcopy(state))
    monkeypatch.setattr(batch.shared_work,'board',lambda *args:{'controls':rows})
    def persist(aid,bid,results,status=None,error=None):
        state['results']=copy.deepcopy(results)
        if status:state['status']=status
        state['error']=error
    monkeypatch.setattr(batch,'persist',persist)
    monkeypatch.setattr(batch.teamwork,'claim_job',lambda aid,cid,uid:{'job_id':cid+'-job'})
    finish=MagicMock();monkeypatch.setattr(batch.teamwork,'finish_job',finish)
    monkeypatch.setattr(batch.teamwork,'get_job',lambda jid:{'status':'SUCCEEDED'})
    return state,rows,finish


def test_worker_executes_source_only_once_per_control_and_saves_progress(worker):
    state,rows,finish=worker;execute=MagicMock()
    batch.process('assessment','batch',execute)
    assert state['status']=='COMPLETED'
    assert [r['status'] for r in state['results']]==['SUCCEEDED','SUCCEEDED']
    assert all(c.args[3] is True for c in execute.call_args_list)
    batch.process('assessment','batch',execute)
    assert execute.call_count==2


def test_stop_request_survives_progress_update_and_stops_before_next_control(worker):
    state,rows,finish=worker
    def execute(*args):state['status']='STOP_REQUESTED'
    batch.process('assessment','batch',execute)
    assert state['status']=='STOPPED' and len(state['results'])==1


def test_changed_sources_before_or_after_job_claim_never_reach_model(worker,monkeypatch):
    state,rows,finish=worker;rows[0]['evidence'][0]['sha256_hash']='changed'
    def claim(aid,cid,uid):
        assert uid=='coordinator';rows[1]['evidence'][0]['sha256_hash']='changed-after-claim';return {'job_id':'job'}
    monkeypatch.setattr(batch.teamwork,'claim_job',claim)
    execute=MagicMock();batch.process('assessment','batch',execute)
    assert all(r['status']=='SKIPPED_SOURCE_CHANGED' for r in state['results'])
    execute.assert_not_called();finish.assert_called_once()


def test_failed_control_is_recorded_and_batch_does_not_retry_it(worker,monkeypatch):
    state,rows,finish=worker
    monkeypatch.setattr(batch.teamwork,'get_job',lambda jid:{'status':'FAILED','error_message':'Model timeout'})
    execute=MagicMock();batch.process('assessment','batch',execute)
    assert execute.call_count==2 and all(r['status']=='FAILED' for r in state['results'])
    assert state['status']=='COMPLETED'  # Completion of traversal, not success/compliance.


def test_unexpected_worker_error_unlocks_current_job_and_preserves_history(worker):
    state,rows,finish=worker
    def fail(*args):raise RuntimeError('Worker crash')
    batch.process('assessment','batch',fail)
    assert state['status']=='FAILED';finish.assert_called_once()


def test_batch_routes_enforce_campaign_and_coordinator_role(monkeypatch):
    from fastapi import HTTPException
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.team_api import require_user
    from backend import enterprise_api
    path='/api/assessments/7f7c009b-bdcd-5b33-934e-15251ad2c976/enterprise/shared-work/batches'
    client=TestClient(app);assert client.get(path).status_code==401
    app.dependency_overrides[require_user]=lambda:{'user_id':'member','role':'assessor'}
    monkeypatch.setattr(batch,'recent',lambda *args:pytest.fail('No foreign read'))
    try:
        def deny(*args):raise HTTPException(403,'Not a member')
        monkeypatch.setattr(enterprise_api,'require_campaign',deny)
        assert client.get(path).status_code==403
        monkeypatch.setattr(enterprise_api,'require_campaign',lambda *args:None)
        assert client.post(path,json={}).status_code==403
        assert client.post(path+'/00000000-0000-0000-0000-000000000001/stop').status_code==403
    finally:app.dependency_overrides.pop(require_user,None)
