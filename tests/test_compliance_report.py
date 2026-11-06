from backend.compliance_report import build_dossier, newer_evidence


def row(cid='A.6.1', evaluation=None):
    return {'control_id': cid, 'compliance_status': 'Compliant', 'latest_evaluation_id': evaluation}


def test_preset_and_stored_status_do_not_replace_evaluation():
    report = build_dossier('a', [row()], {'A.6.1': [{'evidence_id': 'e'}]})
    assert report['controls'][0]['assessment_state'] == 'not_evaluated'
    assert report['controls'][0]['historical_conclusion'] is None
    assert len(report['sha256']) == 64


def test_unsupported_collector_is_not_not_applicable():
    result = build_dossier('a', [row('A.5.1')], {})['controls'][0]
    assert not result['collector_supported']
    assert result['assessment_state'] == 'not_evaluated'


def test_new_lab_evidence_invalidates_current_conclusion_but_retains_history():
    evidence = {'A.6.1': [{'created_at': '2026-11-06T10:00:00+00:00'}]}
    history = {'A.6.1': [{'evaluation_id': 3, 'created_at': '2026-11-05T10:00:00+00:00'}]}
    result = build_dossier('a', [row(evaluation=3)], evidence, history)['controls'][0]
    assert result['assessment_state'] == 'stale'
    assert result['historical_conclusion'] == 'Compliant'
    assert result['evaluation_history'] == history['A.6.1']


def test_freshness_uses_real_time_not_timezone_string_order():
    assert not newer_evidence({'created_at': '2026-11-06T10:00:00+07:00'},
                              {'created_at': '2026-11-06T04:00:00+00:00'})
    assert newer_evidence({'created_at': None}, {'created_at': '2026-11-06T04:00:00+00:00'})


def test_dossier_route_rejects_other_campaign_before_reading(monkeypatch):
    from fastapi import HTTPException
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.team_api import require_user
    import backend.enterprise_api as api
    app.dependency_overrides[require_user] = lambda: {'user_id': 'u'}
    def deny(*args):
        raise HTTPException(403, 'Not a member')
    monkeypatch.setattr(api, 'require_campaign', deny)
    monkeypatch.setattr(api.teamwork, 'progress_board', lambda *args: (_ for _ in ()).throw(AssertionError('Must not read')))
    try:
        with TestClient(app) as client:
            assert client.get('/api/assessments/7f7c009b-bdcd-5b33-934e-15251ad2c976/enterprise/compliance-report').status_code == 403
    finally:
        app.dependency_overrides.pop(require_user, None)
