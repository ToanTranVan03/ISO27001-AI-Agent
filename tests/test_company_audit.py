import copy
import pytest
from backend import company


def record():
    return {'snapshot_hash':'a'*64,'assessment_date':'2026-11-18','people':[
        {'id':'EMP-001','status':'active','training_complete':True,'training_passed':True}],
        'accounts':[{'id':'VPN-1','person_id':'EMP-001','active':True}], 'devices':[]}


def test_preview_is_read_only_and_identifies_exact_training_changes(monkeypatch):
    source=record(); original=copy.deepcopy(source)
    monkeypatch.setattr(company,'snapshot',lambda aid:source)
    result=company.preview('campaign','HF-001','training_missing')
    assert source==original
    assert result['snapshot_hash']=='a'*64
    assert result['employee_id']=='EMP-001'
    assert {r['field'] for r in result['changes']}=={'training_complete','training_passed'}
    assert all(r['before'] is True and r['after'] is False for r in result['changes'])


def test_diff_distinguishes_absent_null_false_and_removed_accounts():
    before={'person':{'id':'EMP-001','flag':None},'accounts':[{'id':'VPN-1','active':True}], 'devices':[]}
    after={'person':{'id':'EMP-001','flag':False,'unknown':None},'accounts':[], 'devices':[]}
    changes=company.describe_changes(before,after)
    unknown=next(r for r in changes if r['field']=='unknown')
    assert not unknown['before_present'] and unknown['after_present']
    assert any(r['field']=='flag' and r['before'] is None and r['after'] is False for r in changes)
    assert any(r['entity_id']=='VPN-1' and not r['after_present'] for r in changes)


def test_stale_preview_is_rejected_before_writes(monkeypatch):
    class Cursor:
        def execute(self,sql,params):
            assert not sql.lstrip().startswith(('UPDATE','INSERT'))
        def fetchone(self):return [True]
        def fetchall(self):return []
    monkeypatch.setattr(company,'snapshot',lambda *args:record())
    with pytest.raises(ValueError,match='đã thay đổi'):
        company.change('campaign','EMP-001','training_missing',cur=Cursor(),expected_snapshot_hash='b'*64)


@pytest.mark.parametrize('action',['bad_action','recover_access'])
def test_invalid_preview_does_not_mutate_source(monkeypatch,action):
    source=record(); original=copy.deepcopy(source)
    monkeypatch.setattr(company,'snapshot',lambda aid:source)
    with pytest.raises(ValueError):company.preview('campaign','EMP-001',action)
    assert source==original


def test_audit_routes_require_authentication():
    from fastapi.testclient import TestClient
    from backend.main import app
    client=TestClient(app)
    base='/api/assessments/7f7c009b-bdcd-5b33-934e-15251ad2c976/enterprise/company'
    assert client.get(base+'/history').status_code==401
    assert client.post(base+'/events/preview',json={'employee_id':'EMP-001','action':'terminate'}).status_code==401


def test_audit_routes_check_membership_and_approval_privilege(monkeypatch):
    from fastapi.testclient import TestClient
    from fastapi import HTTPException
    from backend.main import app
    from backend.team_api import require_user
    from backend import enterprise_api
    base='/api/assessments/7f7c009b-bdcd-5b33-934e-15251ad2c976/enterprise/company'
    monkeypatch.setattr(company,'preview',lambda *args:pytest.fail('Not authorized'))
    monkeypatch.setattr(company,'history',lambda *args:pytest.fail('Not authorized'))
    app.dependency_overrides[require_user]=lambda:{'user_id':'member','role':'member'}
    try:
        monkeypatch.setattr(enterprise_api,'require_campaign',lambda *args:None)
        client=TestClient(app)
        assert client.post(base+'/events/preview',json={'employee_id':'EMP-001','action':'retention_approve'}).status_code==403
        def deny(*args):raise HTTPException(403,'Not a member')
        monkeypatch.setattr(enterprise_api,'require_campaign',deny)
        assert client.get(base+'/history').status_code==403
        assert client.post(base+'/events/preview',json={'employee_id':'EMP-001','action':'terminate'}).status_code==403
    finally:app.dependency_overrides.pop(require_user,None)
