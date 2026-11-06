"""Route/auth contract smoke tests. Run with `python -m pytest tests -q`."""
from fastapi.testclient import TestClient
from backend import main, team_api


def test_react_home_served_from_dist(monkeypatch, tmp_path):
    """Home is React, not the old Control Workspace; no database needed."""
    (tmp_path / 'index.html').write_text('<html>SPACEBASE_MARKER</html>', encoding='utf-8')
    monkeypatch.setattr(main, 'REACT_DIST', tmp_path)
    monkeypatch.setattr(main.database, 'initialize_database', lambda: None)
    monkeypatch.setattr(main.teamwork, 'init_teamwork', lambda: None)
    monkeypatch.setattr(main.enterprise_lab, 'init_enterprise_lab', lambda: None)
    with TestClient(main.app) as client:
        assert 'SPACEBASE_MARKER' in client.get('/').text
        assert 'SPACEBASE_MARKER' in client.get('/spacebase').text


def test_private_api_requires_bearer(monkeypatch):
    monkeypatch.setattr(main.database, 'initialize_database', lambda: None)
    monkeypatch.setattr(main.teamwork, 'init_teamwork', lambda: None)
    monkeypatch.setattr(main.enterprise_lab, 'init_enterprise_lab', lambda: None)
    with TestClient(main.app) as client:
        response = client.get('/api/auth/me')
        assert response.status_code == 401
        response = client.get('/api/assessments')
        assert response.status_code == 401


def test_login_contract(monkeypatch):
    monkeypatch.setattr(main.database, 'initialize_database', lambda: None)
    monkeypatch.setattr(main.teamwork, 'init_teamwork', lambda: None)
    monkeypatch.setattr(main.enterprise_lab, 'init_enterprise_lab', lambda: None)
    monkeypatch.setattr(team_api.teamwork, 'login', lambda username, password: {
        'access_token': 'mock-token', 'user': {'username': username, 'role': 'admin'},
    } if (username, password) == ('test-admin', 'test-password') else None)
    with TestClient(main.app) as client:
        good = client.post('/api/auth/login', json={'username': 'test-admin', 'password': 'test-password'})
        assert good.status_code == 200
        assert good.json()['access_token'] == 'mock-token'
        bad = client.post('/api/auth/login', json={'username': 'test-admin', 'password': 'wrong'})
        assert bad.status_code == 401
