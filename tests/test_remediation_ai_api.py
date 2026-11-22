from contextlib import contextmanager
from copy import deepcopy
from uuid import UUID
from types import SimpleNamespace
import json
import pytest
from fastapi import HTTPException
from backend import remediation_api as api


def setup(monkeypatch):
    doc={'control_id':'A.6.1','description':'Synthetic record gap only','location':'Synthetic HR',
         'root_cause':'Unknown','risk':'unconfirmed','rubric_sha256':'rubric',
         'baseline':{'review_token':'token','criteria':['Inspect sample record'],'conclusion':'Insufficient Evidence'},
         'actions':[],'history':[]}
    @contextmanager
    def connection():
        class Connection:
            @contextmanager
            def cursor(self):
                class Cursor:
                    def execute(self,sql,args):self.sql=sql
                    def fetchall(self):return [('source','x'*3000)] if 'SELECT evidence_id,extracted_text' in self.sql else []
                yield Cursor()
        yield Connection()
    monkeypatch.setattr(api,'get_connection',connection)
    monkeypatch.setattr(api,'membership',lambda *_:'consultant')
    monkeypatch.setattr(api,'read',lambda *args:(1,deepcopy(doc)))
    monkeypatch.setattr(api,'scope_control',lambda *_:({'review_token':'token','expected_evidence_types':['HR'],
        'evidence':[dict(evidence_id='source',sha256_hash='hash',is_synthetic=False,extracted_text='x'*3000)]},{'rubric_sha256':'rubric'}))
    saved=[]
    monkeypatch.setattr(api,'save',lambda cur,aid,rid,v,value:saved.append(value) or value)
    return saved


def test_ollama_http_schema_contract_creates_only_draft(monkeypatch):
    import requests
    saved=setup(monkeypatch)
    proposal=dict(title='Inspect records',steps='Request original records and verify their scope',acceptance='Review each criterion and cite originals',department='HR',resources='Record owner',tasks=['Collect records'])
    proposal.update(problem='Record scope has not been verified',possible_causes='Possible retention gap; requires verification',objective='Verify original sample records',rationale='Current evidence is insufficient',target_location='Test HR service',estimated_effort='Owner must estimate after source review',required_evidence='Original records and verification log',recheck_method='Reassess the frozen rubric with new originals',clarification_questions=['Who owns the source?'])
    def post(url,**kwargs):
        assert url.endswith('/api/chat') and isinstance(kwargs['json']['format'],dict)
        assert kwargs['json']['stream'] is False
        supplied=json.loads(kwargs['json']['messages'][1]['content'])
        assert supplied['source_excerpts_untrusted'][0]['truncated'] is True
        assert len(supplied['source_excerpts_untrusted'][0]['excerpt'])==1500
        return SimpleNamespace(raise_for_status=lambda:None,json=lambda:{'message':{'content':json.dumps(proposal)}})
    monkeypatch.setattr(requests,'post',post)
    value=api.ai_proposal(UUID(int=1),UUID(int=2),api.Expected(expected_version=1),{'user_id':'consultant'})
    assert value['actions'][0]['state']=='PENDING_APPROVAL'
    assert value['actions'][0]['assignee'] is None


def test_bad_model_response_is_logged_not_replaced_with_a_plan(monkeypatch):
    import requests
    saved=setup(monkeypatch)
    monkeypatch.setattr(requests,'post',lambda *args,**kwargs:SimpleNamespace(raise_for_status=lambda:None,json=lambda:{'message':{'content':'invalid original response'}}))
    with pytest.raises(HTTPException) as exc:api.ai_proposal(UUID(int=1),UUID(int=2),api.Expected(expected_version=1),{'user_id':'consultant'})
    assert exc.value.status_code==502 and not saved[-1]['actions']
    assert saved[-1]['history'][-1]['raw_response']=='invalid original response'
