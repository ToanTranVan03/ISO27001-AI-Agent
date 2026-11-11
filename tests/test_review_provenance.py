import pytest
from agent_core import a8_assessment as a8
from agent_core.a8_review_analysis import analyze_reviews
from backend.scope56 import build_scope
from test_a8_completion import label
from test_a8_assessment import api_env


@pytest.mark.parametrize('assistance,exposure', [('unknown','unknown'),('ai_assisted','unknown'),('unassisted','yes'),('team_discussion','no')])
def test_completed_assisted_or_undeclared_labels_are_not_independent(assistance,exposure):
    report=a8.run('mixed','rules')
    reviews=[{**label(report,i,'reviewer','Partially Compliant'),'assistance':assistance,'prior_exposure':exposure} for i in range(18)]
    result=analyze_reviews(report,reviews,'creator')
    assert result['complete_reviewers']==['reviewer']
    assert not result['complete_independent_reviewers']
    assert result['reviewer_progress'][0]['submitted']==18
    progress=result['reviewer_progress'][0]
    assert progress['independently_declared']+progress['assisted']+progress['unclassified']==18
    assert all(r['rated']==0 for r in result['independent_reviewer_comparisons']['reviewer']['per_control'])


def test_historical_labels_without_declaration_are_preserved_but_not_assumed_independent():
    report=a8.run('mixed','rules');review=label(report,0,'reviewer','Partially Compliant')
    del review['assistance'];del review['prior_exposure']
    result=analyze_reviews(report,[review],'creator')
    assert result['submitted_label_count']==1 and result['reviewer_progress'][0]['unclassified']==1
    assert 'assistance' not in review  # Analysis must not rewrite locked history.


def test_full_scope_worklist_is_actionable_without_fabricating_approval():
    scope=build_scope('a',{'controls':[]})
    work=scope['acceptance_worklist']
    assert work['by_stage']['applicability']==56 and work['by_stage']['sources']==56
    assert work['by_stage']['review']==56 and not work['soa_approved']
    assert work['tasks'][0]['stage']=='rubric'
    decisions={'A.6.1':dict(applicable=False,reason='Explicit exclusion rationale',treatment='Responsible officer to confirm')}
    updated=build_scope('a',{'controls':[]},decisions=decisions)['acceptance_worklist']
    assert not any(t['control_id']=='A.6.1' for t in updated['tasks'])


def test_api_stores_provenance_and_blocks_assisted_approval(api_env):
    from fastapi.testclient import TestClient
    from backend.main import app
    api,actor=api_env;aid='7f7c009b-bdcd-5b33-934e-15251ad2c976';base=f'/api/assessments/{aid}/a8'
    with TestClient(app) as client:
        rid=client.post(base+'/runs',json={'mode':'rules','profile':'mixed'}).json()['run_id']
        api.worker(aid,rid,'mixed','rules')
        doc=api.read(aid,rid);actor.update(user_id='reviewer',role='assessor')
        for c in a8.catalog():
            response=client.post(base+'/runs/'+rid+'/reviews',json=dict(control_id=c['control_id'],expected='Partially Compliant',
                rationale='Software test only, not actual independent human labels',report_sha256=doc['report']['sha256'],assistance='ai_assisted',prior_exposure='no'))
            assert response.status_code==200
        result=client.get(base+'/runs/'+rid).json()
        assert result['readiness']['complete_submitted_reviewers']==1
        assert result['readiness']['complete_independent_reviewers']==0
        assert all(r['accuracy'] is None for r in result['human_comparison']['per_control'])
        actor.update(user_id='starter',role='admin')
        decisions=[dict(control_id=c['control_id'],applicable=True,reason='Relevant scoped lab service',treatment='Maintain or remediate known gaps') for c in a8.catalog()]
        denied=client.post(base+'/runs/'+rid+'/soa-approval',json={'decisions':decisions,'note':'Test responsible officer approval request'})
        assert denied.status_code==409
        assert all(r['assistance']=='ai_assisted' for r in api.read(aid,rid)['reviews'])
