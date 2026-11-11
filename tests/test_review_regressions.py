"""Regressions found during the source review; no real assessment records."""
import json
import pytest
from pydantic import ValidationError
from agent_core.graph_builder import ControlEvaluationOutput
from backend import database


@pytest.mark.parametrize('confidence',['invalid',None,True,-1,101,float('nan'),float('inf')])
def test_invalid_model_confidence_never_turns_into_85_percent(confidence):
    with pytest.raises(ValidationError):
        ControlEvaluationOutput(status='Compliant',confidence=confidence,rationale='Claim',evidence_ids=['e'])


def test_missing_confidence_is_rejected_instead_of_invented():
    with pytest.raises(ValidationError):
        ControlEvaluationOutput(status='Compliant',rationale='Claim',evidence_ids=['e'])


def test_model_rubric_matches_authoritative_approval_file(monkeypatch,tmp_path):
    rubric=tmp_path/'rubrics.json'
    rubric.write_text(json.dumps({'A.8.5':{'Compliant':'Version 1'}}),encoding='utf-8')
    monkeypatch.setattr(database,'RUBRICS_PATH',rubric)
    monkeypatch.setattr(database,'get_connection',lambda:pytest.fail('Stale DB seed must not replace approved rubric'))
    assert database.get_rubric('A.8.5')['Compliant']=='Version 1'
    rubric.write_text(json.dumps({'A.8.5':{'Compliant':'Version 2'}}),encoding='utf-8')
    assert database.get_rubric('A.8.5')['Compliant']=='Version 2'


@pytest.mark.parametrize('new_source,expected',[(False,'current'),(True,'stale')])
def test_document_evaluation_freshness_does_not_require_synthetic_snapshot(monkeypatch,new_source,expected):
    from contextlib import nullcontext
    from backend import company_evidence
    class Cursor:
        def execute(self,*args):pass
        def fetchall(self):return [(3,None,['PLAN USER_EVIDENCE_ONLY'],new_source)]
    class Connection:
        def cursor(self):return nullcontext(Cursor())
    monkeypatch.setattr(company_evidence,'get_connection',lambda:nullcontext(Connection()))
    monkeypatch.setattr(company_evidence.company,'snapshot',lambda _: {'snapshot_hash':'changed-company'})
    row={'control_id':'A.6.1','latest_evaluation_id':3,'compliance_status':'Insufficient Evidence','workflow_status':'WAITING_EVIDENCE'}
    result=company_evidence.fresh_progress('campaign',[row])[0]
    assert result['data_freshness']==expected


def test_legacy_evidence_write_cannot_bypass_running_control_lock(monkeypatch):
    from contextlib import nullcontext
    calls=[]
    class Cursor:
        def execute(self,sql,params):calls.append(sql)
        def fetchone(self):return ('RUNNING',)
    class Connection:
        def cursor(self):return nullcontext(Cursor())
    monkeypatch.setattr(database,'get_connection',lambda:nullcontext(Connection()))
    with pytest.raises(database.EvaluationBusy):
        database.save_evidence(evidence_id='e',control_id='A.6.1',evidence_type='test',source='s',
            extracted_text='text',sha256_hash='hash',assessment_id='campaign')
    assert len(calls)==1 and 'FOR UPDATE' in calls[0]


def test_legacy_evaluation_busy_rejects_before_model_and_failure_releases_claim(monkeypatch):
    from backend import main
    from fastapi import HTTPException
    monkeypatch.setattr(main,'resolve_company',lambda *_:'campaign')
    monkeypatch.setattr(database,'get_control',lambda cid:{'control_id':cid,'name':'name','objective':'objective'})
    def busy(*args):raise ValueError('busy')
    monkeypatch.setattr(main.teamwork,'claim_job',busy)
    monkeypatch.setattr(main.agent_graph,'invoke',lambda *_:pytest.fail('Busy control must not call model'))
    actor={'user_id':'u'}
    with pytest.raises(HTTPException) as exc:
        main.evaluate_control(main.EvaluationRequest(control_id='A.6.1'),actor)
    assert exc.value.status_code==409
    monkeypatch.setattr(main.teamwork,'claim_job',lambda *_:{'job_id':'job'})
    def unavailable(*args):raise RuntimeError('Model unavailable')
    monkeypatch.setattr(main.agent_graph,'invoke',unavailable)
    finished=[]
    monkeypatch.setattr(main.teamwork,'finish_job',lambda *args:finished.append(args))
    with pytest.raises(HTTPException) as exc:
        main.evaluate_control(main.EvaluationRequest(control_id='A.6.1'),actor)
    assert exc.value.status_code==502 and finished[0][0]=='job' and finished[0][1] is None
