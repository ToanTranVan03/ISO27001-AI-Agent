import json
from contextlib import nullcontext
from fastapi.testclient import TestClient
from backend import company_storage,company
from backend.main import app


def test_retired_office_endpoints_are_not_registered():
    with TestClient(app) as client:
        for path in ('/api/live','/api/agent/history','/api/simulation','/static/mission.js'):
            assert client.get(path).status_code==404
        for path in ('/workspace','/legacy','/enterprise','/simulation'):
            assert client.get(path,follow_redirects=False).status_code==307


def test_inventory_migration_is_additive_and_does_not_recreate_incident_workflow(monkeypatch):
    calls=[]
    class Cursor:
        def execute(self,sql,params=None):calls.append(sql)
    class Connection:
        def cursor(self):return nullcontext(Cursor())
    monkeypatch.setattr(company_storage,'get_connection',lambda:nullcontext(Connection()))
    monkeypatch.setattr(company,'initialize_company',lambda:None)
    company_storage.initialize_company_inventory()
    assert all(not s.lstrip().upper().startswith(('DELETE','DROP','UPDATE','TRUNCATE')) for s in calls)
    assert all('ON CONFLICT DO NOTHING' in s for s in calls if s.lstrip().startswith('INSERT'))
    assert not any('enterprise_incident' in s or 'mission' in s or 'asset_activity' in s for s in calls)
    seed=json.loads(company_storage.SEED.read_text(encoding='utf-8'))
    assert {r['asset_id'] for r in seed['relationships']}<={a['asset_id'] for a in seed['assets']}
    assert {r['employee_id'] for r in seed['relationships']}<={p['employee_id'] for p in seed['people']}
