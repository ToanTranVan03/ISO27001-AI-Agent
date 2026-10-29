"""No-database API tests for autonomous lab jobs, isolation and scope."""
from uuid import UUID
from fastapi.testclient import TestClient
from backend import main, auto_audit

ASSESSMENT = '00000000-0000-0000-0000-000000000001'
RUN_ID = '00000000-0000-0000-0000-000000000007'
USER = '00000000-0000-0000-0000-000000000002'


def no_startup(monkeypatch):
    for owner, name in [
        (main.database, 'initialize_database'),
        (main.teamwork, 'init_teamwork'),
        (main.enterprise_lab, 'init_enterprise_lab'),
        (main.auto_audit, 'initialize_auto_audit'),
    ]:
        monkeypatch.setattr(owner, name, lambda: None)


def test_scope_orders_all_controls_numerically(monkeypatch):
    monkeypatch.setattr(auto_audit.database, 'list_controls', lambda: [
        {'control_id': key} for key in ['A.8.34','A.8.2','A.7.1','A.6.8','A.6.1','A.5.1']
    ])
    assert auto_audit.control_scope() == [
        'A.6.1','A.6.8','A.7.1','A.8.2','A.8.34'
    ]


def test_auto_audit_endpoints_require_auth(monkeypatch):
    no_startup(monkeypatch)
    with TestClient(main.app) as client:
        assert client.post(f'/api/assessments/{ASSESSMENT}/auto-audits').status_code == 401
        assert client.get(f'/api/assessments/{ASSESSMENT}/auto-audits/latest').status_code == 401
        assert client.get(f'/api/auto-audits/{RUN_ID}').status_code == 401
        assert client.get(f'/api/auto-audits/{RUN_ID}/events').status_code == 401


def test_start_queues_worker_and_requires_membership(monkeypatch):
    no_startup(monkeypatch)
    main.app.dependency_overrides[auto_audit.require_user] = lambda: {'user_id': USER, 'role': 'assessor'}
    submitted = []
    seen = []
    monkeypatch.setattr(auto_audit, 'require_campaign', lambda assessment_id, user: seen.append((str(assessment_id), user['user_id'])))
    monkeypatch.setattr(auto_audit, 'create_run', lambda assessment_id, user_id: (RUN_ID, ['A.6.1', 'A.6.2']))
    monkeypatch.setattr(auto_audit, 'get_run', lambda run_id: {'run_id': run_id, 'status': 'RUNNING', 'total': 2})
    monkeypatch.setattr(auto_audit.worker_pool, 'submit', lambda *args: submitted.append(args))
    try:
        with TestClient(main.app) as client:
            response = client.post(f'/api/assessments/{ASSESSMENT}/auto-audits')
        assert response.status_code == 202
        assert response.json()['run_id'] == RUN_ID
        assert submitted[0][0] is auto_audit.execute_run
        assert submitted[0][-1] == ['A.6.1', 'A.6.2']
        assert seen == [(ASSESSMENT, USER)]
    finally:
        main.app.dependency_overrides.clear()
