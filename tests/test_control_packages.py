import json
import pytest
from evidence_collectors import control_packages as packages
from backend.scope56 import build_scope

AID='7f7c009b-bdcd-5b33-934e-15251ad2c976'


def test_preparing_56_templates_creates_no_evidence(monkeypatch,tmp_path):
    monkeypatch.setattr(packages,'ROOT',tmp_path)
    report=packages.prepare(AID)
    assert report['control_count']==56
    assert all(not packages.inspect(AID,c['control_id'])['items'] for c in packages.controls())


def source(monkeypatch,tmp_path,name='policy.txt'):
    monkeypatch.setattr(packages,'ROOT',tmp_path)
    c=packages.controls()[0];folder=packages.directory(AID,c['control_id']);folder.mkdir(parents=True)
    (folder/'policy.txt').write_text('Evidence supplied by responsible officer. Review actual records before concluding.',encoding='utf-8')
    manifest={'control_id':c['control_id'],'sources':[{'file':name,'evidence_type':c['expected_evidence_types'][0]}]}
    (folder/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
    return c,folder


def test_reads_actual_text_idempotent_hash_and_version_change(monkeypatch,tmp_path):
    c,folder=source(monkeypatch,tmp_path)
    first=packages.inspect(AID,c['control_id'])
    assert len(first['items'])==1
    assert first['items']==packages.inspect(AID,c['control_id'])['items']
    payload=json.loads(first['items'][0]['extracted_text'])
    assert not payload['provenance_verified'] and payload['observed_at'] is None
    (folder/'policy.txt').write_text('New evidence content',encoding='utf-8')
    assert packages.inspect(AID,c['control_id'])['items'][0]['evidence_id']!=first['items'][0]['evidence_id']


@pytest.mark.parametrize('name',['../private.txt','_REQUIRED.md','manifest.json','sub/f.txt'])
def test_rejects_escape_and_templates_as_evidence(monkeypatch,tmp_path,name):
    c,_=source(monkeypatch,tmp_path,name)
    report=packages.inspect(AID,c['control_id'])
    assert not report['items'] and report['issues']


def test_soa_approval_invalidates_when_underlying_snapshot_changes():
    controls=packages.controls()
    decisions={c['control_id']:dict(applicable=True,reason='In project scope',treatment='Maintain controls') for c in controls}
    original=build_scope(AID,{'controls':[],'company_snapshot_hash':'before'},decisions=decisions)
    reviews={c['control_id']:dict(conclusion='Insufficient Evidence',review_token=c['review_token'],reviewed_by='human') for c in original['controls']}
    reviewed=build_scope(AID,{'controls':[],'company_snapshot_hash':'before'},decisions=decisions,reviews=reviews)
    assert not reviewed['soa']['approval_ready']
    rubric_approval={'rubric_sha256':reviewed['rubric_sha256'],'approved_by':'admin'}
    reviewed=build_scope(AID,{'controls':[],'company_snapshot_hash':'before'},decisions=decisions,reviews=reviews,rubric_approvals=[rubric_approval])
    assert reviewed['soa']['approval_ready']
    approval={'fingerprint':reviewed['soa']['fingerprint'],'approved_by':'admin'}
    approved=build_scope(AID,{'controls':[],'company_snapshot_hash':'before'},decisions=decisions,reviews=reviews,approvals=[approval],rubric_approvals=[rubric_approval])
    assert approved['soa']['approval']=='HUMAN_APPROVED_PROJECT_SCOPE'
    changed=build_scope(AID,{'controls':[],'company_snapshot_hash':'after'},decisions=decisions,reviews=reviews,approvals=[approval],rubric_approvals=[rubric_approval])
    assert changed['soa']['approval']=='DRAFT_NOT_APPROVED' and not changed['soa']['approval_ready']


def test_user_document_mode_never_runs_synthetic_people_collector(monkeypatch):
    from agent_core import graph_builder as graph
    from backend import database,company_evidence
    monkeypatch.setattr(database,'collect_user_evidence',lambda *_:([{'evidence_id':'document-only'}],{}))
    monkeypatch.setattr(company_evidence,'collect_people',lambda *_:pytest.fail('Must not read synthetic people'))
    state={'assessment_id':AID,'control_id':'A.6.1','source_mode':'user_evidence_only','audit_trail':[]}
    graph.node_plan(state);graph.node_collect(state)
    assert state['collected_evidences']==[{'evidence_id':'document-only'}]
    assert 'company_evaluation' not in state



def test_full_scope_review_and_approval_gates(monkeypatch,tmp_path):
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend import enterprise_api as api,a8_api
    from backend.team_api import require_user
    monkeypatch.setattr(a8_api,'STORE',tmp_path)
    monkeypatch.setattr(api,'require_campaign',lambda *_:None)
    actor={'user_id':'human','role':'member'}
    app.dependency_overrides[require_user]=lambda:actor
    report=build_scope(AID,{'controls':[]})
    monkeypatch.setattr(api,'scope56',lambda *_:report)
    base=f'/api/assessments/{AID}/enterprise/scope56'
    try:
        with TestClient(app) as client:
            review={'control_id':'A.6.1','review_token':report['controls'][0]['review_token'],
                    'conclusion':'Compliant','rationale':'Reviewer checked the source documentation','evidence_ids':[]}
            assert client.post(base+'/reviews',json=review).status_code==422
            review['conclusion']='Insufficient Evidence'
            assert client.post(base+'/reviews',json=review).status_code==200
            review['review_token']='0'*64
            assert client.post(base+'/reviews',json=review).status_code==409
            approval={'fingerprint':report['soa']['fingerprint'],'note':'Responsible officer confirms scoped applicability and evidence'}
            assert client.post(base+'/approval',json=approval).status_code==403
            actor['role']='admin'
            assert client.post(base+'/approval',json=approval).status_code==409
            report['soa']['approval_ready']=True
            assert client.post(base+'/approval',json=approval).status_code==200
    finally:app.dependency_overrides.pop(require_user,None)



def test_missing_user_evidence_is_unknown_without_model(monkeypatch):
    from agent_core import graph_builder as graph
    monkeypatch.setattr(graph.ollama,'Client',lambda **_:pytest.fail('No evidence must not call model'))
    state={'source_mode':'user_evidence_only','collected_evidences':[],'audit_trail':[]}
    graph.node_evaluate(state)
    assert state['compliance_status']=='Insufficient Evidence' and not state['proposed_evidence_ids']
