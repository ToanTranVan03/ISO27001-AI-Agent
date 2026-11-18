from contextlib import contextmanager,nullcontext
import pytest
from backend import teamwork


def test_profile_routes_only_read_and_update_the_signed_in_account(monkeypatch):
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.team_api import require_user
    client=TestClient(app)
    assert client.get('/api/auth/profile').status_code==401
    assert client.put('/api/auth/profile',json={'display_name':'Test Name'}).status_code==401
    user={'user_id':'self','username':'reviewer','role':'assessor','display_name':'Current'}
    app.dependency_overrides[require_user]=lambda:user
    calls=[]
    monkeypatch.setattr(teamwork,'account_profile',lambda uid:({**user,'email':''} if uid=='self' else pytest.fail('Foreign profile')))
    def update(uid,**fields):
        assert uid=='self';calls.append(fields);return {**user,**fields}
    monkeypatch.setattr(teamwork,'update_account_profile',update)
    try:
        assert client.get('/api/auth/profile').json()['role']=='assessor'
        for extra in ({'role':'admin'},{'user_id':'someone-else'},{'username':'admin'}):
            assert client.put('/api/auth/profile',json={'display_name':'Test Name',**extra}).status_code==422
        assert not calls
        response=client.put('/api/auth/profile',json={'display_name':'Updated Name','email':'member@example.com'})
        assert response.status_code==200 and response.json()['role']=='assessor'
        assert calls[0]['display_name']=='Updated Name'
    finally:app.dependency_overrides.pop(require_user,None)


@pytest.mark.parametrize('fields',[{'display_name':' '},{'display_name':'x'*101},
    {'display_name':'Name\nadmin'},{'display_name':'Name','email':'not-an-email'},
    {'display_name':'Name','position':'x'*151}])
def test_invalid_profile_is_rejected_before_database_write(monkeypatch,fields):
    monkeypatch.setattr(teamwork,'get_connection',lambda:pytest.fail('Invalid input must not write'))
    with pytest.raises(ValueError):teamwork.update_account_profile('self',**fields)


def test_update_changes_only_display_and_contact_fields(monkeypatch):
    captured=[]
    class Cursor:
        def execute(self,sql,args):captured.append((sql,args))
        def fetchone(self):return ['self']
    class Connection:
        def cursor(self):return nullcontext(Cursor())
    @contextmanager
    def connect():yield Connection()
    monkeypatch.setattr(teamwork,'get_connection',connect)
    monkeypatch.setattr(teamwork,'account_profile',lambda uid:{'user_id':uid})
    teamwork.update_account_profile('self',' Name ','',' Team ',' Reviewer ')
    sql,args=captured[0]
    assert sql.startswith('UPDATE team_users SET display_name=%s,profile=%s WHERE user_id=%s')
    assert args[0]=='Name' and args[2]=='self'
    assert args[1].obj=={'email':'','organization':'Team','position':'Reviewer'}
