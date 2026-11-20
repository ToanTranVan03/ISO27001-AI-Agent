import copy
import json
from pathlib import Path
from fastapi.testclient import TestClient
from test_a8_assessment import api_env

AID='7f7c009b-bdcd-5b33-934e-15251ad2c976'
RID='00000000-0000-0000-0000-000000000077'


def setup_doc(api):
    report=json.loads(Path('docs/a8-results/live-v2-ollama-pilot.json').read_text(encoding='utf-8'))['report']
    doc=dict(run_id=RID,created_by='starter',created_at='test',state='finished',mode='llm',profile='mixed',
        report=report,reviews=[],review_protocol=api.REVIEW_PROTOCOL)
    api.save(api.folder(AID)/(RID+'.json'),doc)
    return doc,dict(control_id=report['records'][0]['control_id'],report_sha256=report['sha256'],
        state='needs_new_review',note='Test coordination note: obtain a new independent review on frozen evidence.')


def test_followup_is_append_only_and_never_changes_labels_report_or_blind_pack(api_env):
    from backend.main import app
    api,actor=api_env;doc,payload=setup_doc(api)
    before=copy.deepcopy(doc)
    actor.update(role='admin',user_id='coordinator')
    url=f'/api/assessments/{AID}/a8/runs/{RID}'
    with TestClient(app) as client:
        for _ in range(2):assert client.post(url+'/review-followups',json=payload).status_code==201
        saved=api.read(AID,RID)
        assert saved['report']==before['report'] and saved['reviews']==before['reviews']
        assert len(saved['review_followups'])==2
        assert saved['review_followups'][0]['followup_id']!=saved['review_followups'][1]['followup_id']
        assert saved['review_followups'][0]['evidence_sha256']==doc['report']['records'][0]['evidence']['source_sha256']
        assert 'soa_approval_history' not in saved
        actor.update(role='assessor',user_id='new-reviewer')
        blind=client.get(url).json()
        assert blind['blind'] and 'review_followups' not in blind
        assert client.post(url+'/review-followups',json=payload).status_code==403


def test_followup_rejects_stale_out_of_scope_and_invalid_notes_without_writing(api_env):
    from backend.main import app
    api,actor=api_env;_,payload=setup_doc(api);actor.update(role='admin',user_id='coordinator')
    path=api.folder(AID)/(RID+'.json');before=path.read_bytes()
    with TestClient(app) as client:
        for changes,status in [({'report_sha256':'0'*64},409),({'control_id':'A.7.1'},422),
                ({'note':'short'},422),({'state':'approved'},422),({'expected':'Compliant'},422)]:
            assert client.post(f'/api/assessments/{AID}/a8/runs/{RID}/review-followups',json={**payload,**changes}).status_code==status
    assert path.read_bytes()==before
