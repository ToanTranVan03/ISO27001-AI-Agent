from backend.scope56 import build_scope


def test_scope_and_soa_cover_56_without_fake_conclusions():
    report=build_scope('a',{'controls':[]})
    assert report['scope_total']==56 and report['priority_count']==18
    assert sorted(report['pillars'].values())==[8,14,34]
    assert len(report['soa']['entries'])==56
    assert all(r['conclusion']=='Chưa đánh giá' for r in report['controls'])
    assert all(e['applicable'] is None for e in report['soa']['entries'])
    assert report['soa']['approval']=='DRAFT_NOT_APPROVED'


def test_experiment_pass_is_not_promoted_to_formal_conclusion():
    report=build_scope('a',{'controls':[]},{'A.8.5':[{'status':'Compliant','source':'A8_EXPERIMENT_ONLY'}]})
    row=next(c for c in report['controls'] if c['control_id']=='A.8.5')
    assert row['priority_a8'] and row['experiment_results']
    assert row['conclusion']=='Chưa đánh giá'
    assert row['support_stage']=='partial_lab'
    assert next(e for e in report['soa']['entries'] if e['control_id']=='A.8.5')['implementation_status']=='Chưa đánh giá'


def test_acceptance_counts_do_not_turn_synthetic_sources_into_submitted_evidence():
    formal={'controls':[dict(control_id='A.8.5',evidence=[
        dict(evidence_id='lab',sha256_hash='a',is_synthetic=True,evidence_type='lab')]) ]}
    report=build_scope('a',formal)
    assert report['acceptance']['controls_with_evidence']==1
    assert report['acceptance']['controls_with_submitted_sources']==0
    assert report['acceptance']['controls_with_current_human_review']==0
    row=next(r for r in report['controls'] if r['control_id']=='A.8.5')
    assert 'tính áp dụng' in row['next_action']
    assert row['evidence_types_to_check']
    formal['controls'][0]['evidence'][0]['is_synthetic']=False
    assert build_scope('a',formal)['acceptance']['controls_with_submitted_sources']==1


def test_exclusion_and_treatment_are_explicit_and_preserve_failed_status():
    formal={'controls':[dict(control_id='A.8.5',conclusion='Non-Compliant',assessment_state='evaluated',evidence=[])]}
    decision={'A.8.5':dict(applicable=False,reason='Explicit scope decision',treatment='Requires supervisor review',recorded_by='admin')}
    report=build_scope('a',formal,decisions=decision)
    row=next(e for e in report['soa']['entries'] if e['control_id']=='A.8.5')
    assert row['applicable'] is False and row['implementation_status']=='Non-Compliant'
    assert row['treatment']=='Requires supervisor review'


def test_scope_route_checks_membership_before_reading(monkeypatch):
    from fastapi import HTTPException
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend import enterprise_api,shared_work
    from backend.team_api import require_user
    app.dependency_overrides[require_user]=lambda:{'user_id':'u'}
    def deny(*_):raise HTTPException(403,'Not a member')
    monkeypatch.setattr(enterprise_api,'require_campaign',deny)
    monkeypatch.setattr(shared_work,'dossier',lambda *_:(_ for _ in ()).throw(AssertionError('Must not read')))
    try:
        with TestClient(app) as c:
            assert c.get('/api/assessments/7f7c009b-bdcd-5b33-934e-15251ad2c976/enterprise/scope56').status_code==403
    finally:app.dependency_overrides.pop(require_user,None)


def test_overview_does_not_bypass_blind_review(monkeypatch,tmp_path):
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend import enterprise_api,shared_work,a8_api
    from backend.team_api import require_user
    aid='7f7c009b-bdcd-5b33-934e-15251ad2c976'
    rid='00000000-0000-0000-0000-000000000001'
    monkeypatch.setattr(a8_api,'STORE',tmp_path)
    a8_api.save(a8_api.folder(aid)/(rid+'.json'),dict(created_by='creator',reviews=[],report={'records':[{'control_id':'A.8.5'}]}))
    monkeypatch.setattr(enterprise_api,'require_campaign',lambda *_:None)
    monkeypatch.setattr(shared_work,'dossier',lambda _: {'controls':[]})
    app.dependency_overrides[require_user]=lambda:{'user_id':'blinded-reviewer'}
    try:
        with TestClient(app) as c:
            r=c.get(f'/api/assessments/{aid}/enterprise/scope56')
            assert r.status_code==200
            assert all(not row['experiment_results'] for row in r.json()['controls'])
    finally:app.dependency_overrides.pop(require_user,None)
