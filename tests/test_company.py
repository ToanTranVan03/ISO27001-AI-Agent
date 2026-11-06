import copy
import pytest
from backend.company import canonical_employee, project_company
from backend.company_evidence import bind_lab
from backend.enterprise_spec import make_snapshot
from agent_core.live import apply_business_change
from agent_core.simulation import evaluate_enterprise
from backend.office_logic import transition, DEFAULT_STATE


def fixture():
    people = [{'employee_id': 'EMP-050', 'display_name': 'Person', 'department': 'IT',
        'job_title': 'Engineer', 'employment_status': 'active', 'account_status': 'active',
        'state': {'training_complete': True, 'training_passed': True, 'remote': True}}]
    accounts = [{'account_id': 'EMP-050-VPN', 'employee_id': 'EMP-050', 'system_name': 'VPN',
                 'state': {'active': True, 'mfa': None}}]
    assets = [{'asset_id': 'OFFICE-EMP-050', 'asset_type': 'hardware', 'asset_name': 'Workstation',
               'employee_id': 'EMP-050', 'state': {'encrypted': None, 'returned': False}}]
    return people, accounts, assets, {'assessment_date': '2026-11-06', 'policies': {}}


def test_alias_is_explicit_and_invalid_identity_never_maps_to_someone_else():
    assert canonical_employee('HF-050') == 'EMP-050'
    assert canonical_employee('emp-003') == 'EMP-003'
    for bad in ('HF-50', 'EMP-050-extra', '050'):
        with pytest.raises(ValueError): canonical_employee(bad)


def test_projection_preserves_unknowns_and_columns_override_old_profile_fields():
    p,a,d,m = fixture()
    p[0]['account_status'] = 'disabled'
    p[0]['state'].update(id='HF-wrong',status='terminated')
    result = project_company('assessment',p,a,d,m)
    assert result['people'][0]['id'] == 'EMP-050'
    assert result['people'][0]['status'] == 'active'
    assert result['accounts'][0]['active'] is False
    assert result['accounts'][0]['mfa'] is None
    assert result['devices'][0]['encrypted'] is None


def test_hash_tracks_device_account_person_and_assessment_without_mutating_inputs():
    rows = fixture(); original = copy.deepcopy(rows)
    first = project_company('a',*rows)
    assert rows == original
    assert project_company('a',*rows)['snapshot_hash'] == first['snapshot_hash']
    assert project_company('b',*rows)['snapshot_hash'] != first['snapshot_hash']
    rows[1][0]['state']['mfa'] = True
    assert project_company('a',*rows)['snapshot_hash'] != first['snapshot_hash']
    rows[2][0]['state']['media_status'] = 'unregistered'
    assert project_company('a',*rows)['snapshot_hash'] != first['snapshot_hash']


def test_business_event_and_evaluator_share_identity_and_current_profile():
    data = project_company('a',*fixture())
    before,after = apply_business_change(data,'EMP-050','training_missing')
    assert before['person']['training_passed'] is True
    assert after['person']['training_passed'] is False
    control = next(c for c in evaluate_enterprise(data) if c['control_id']=='A.6.3')
    assert control['findings'][0]['person_id'] == 'EMP-050'


def test_lab_counts_come_from_inventory_not_preset_and_evidence_changes_with_source():
    data = project_company('a',*fixture())
    base = make_snapshot('7f7c009b-bdcd-5b33-934e-15251ad2c976','iam','healthy',1)
    first = bind_lab(base,data,'iam')
    import json
    facts = json.loads(first['extracted_text'])['facts']
    assert facts['active_accounts'] == 1
    assert facts['mfa_enabled_accounts'] == 0
    assert facts['unknown_mfa_accounts'] == 1
    data['accounts'][0]['mfa'] = True
    assert bind_lab(base,data,'iam')['evidence_id'] != first['evidence_id']


def test_returned_workstation_cannot_be_reopened_by_office_command():
    with pytest.raises(ValueError):
        transition('/di-lam',{**DEFAULT_STATE,'returned':True})


def test_soc_asset_changes_are_visible_in_account_and_device_projections():
    p,a,d,m = fixture()
    a[0]['state']['asset_id'] = 'IAM-ACCOUNT'
    d.append({'asset_id':'IAM-ACCOUNT','asset_type':'software','asset_name':'Account',
              'employee_id':'EMP-050','state':{'account_status':'disabled'}})
    d[0]['state']['encryption_status'] = 'enabled'
    data = project_company('a',p,a,d,m)
    assert data['accounts'][0]['active'] is False
    assert data['devices'][0]['encrypted'] is True


def test_assigned_training_never_keeps_old_complete_flag():
    p,a,d,m = fixture()
    p[0]['state']['training_status'] = 'assigned'
    data = project_company('a',p,a,d,m)
    assert data['people'][0]['training_passed'] is False


def test_unknown_training_stays_missing_instead_of_becoming_a_violation():
    p,a,d,m = fixture()
    p[0]['state'].update(training_passed=None,training_complete=None,training_status='not_verified')
    data = project_company('a',p,a,d,m)
    result = next(c for c in evaluate_enterprise(data) if c['control_id']=='A.6.3')
    assert data['people'][0]['training_passed'] is None
    assert result['missing_evidence'] == ['EMP-050']
    assert not result['findings']


def test_shared_company_api_requires_authentication():
    from fastapi.testclient import TestClient
    from backend.main import app
    with TestClient(app) as client:
        for path in ('/api/live','/api/simulation','/api/agent/history',
                     '/api/assessments/7f7c009b-bdcd-5b33-934e-15251ad2c976/enterprise/company'):
            assert client.get(path).status_code == 401


def test_member_cannot_approve_retention_through_shared_events(monkeypatch):
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.team_api import require_user
    from backend import enterprise_api, company
    monkeypatch.setattr(enterprise_api,'require_campaign',lambda *args:None)
    monkeypatch.setattr(company,'change',lambda *args,**kwargs:pytest.fail('Must reject before changing company'))
    app.dependency_overrides[require_user] = lambda:{'user_id':'member','role':'member'}
    try:
        with TestClient(app) as client:
            assert client.post('/api/assessments/7f7c009b-bdcd-5b33-934e-15251ad2c976/enterprise/company/events',
                json={'employee_id':'EMP-050','action':'retention_approve'}).status_code==403
    finally:
        app.dependency_overrides.pop(require_user,None)


def test_dashboard_invalidates_old_company_result_without_erasing_history(monkeypatch):
    from contextlib import contextmanager, nullcontext
    import json
    from backend import company_evidence
    class Cursor:
        def execute(self,sql,params):
            assert params[0]=='campaign'
        def fetchall(self):
            return [(3,json.dumps({'snapshot_hash':'old'}))]
    class Connection:
        def cursor(self):return nullcontext(Cursor())
    @contextmanager
    def connection():yield Connection()
    monkeypatch.setattr(company_evidence,'get_connection',connection)
    monkeypatch.setattr(company_evidence.company,'snapshot',lambda aid:{'snapshot_hash':'new'})
    rows=[{'control_id':'A.6.3','latest_evaluation_id':3,'compliance_status':'Compliant','workflow_status':'COMPLETED'}]
    result=company_evidence.fresh_progress('campaign',rows)[0]
    assert result['data_freshness']=='stale'
    assert result['compliance_status'] is None
    assert result['workflow_status']=='NOT_STARTED'
    assert result['latest_evaluation_id']==3
    assert rows[0]['compliance_status']=='Compliant'
