import json
from unittest.mock import Mock
from run_acceptance_checks import run,check_response


def response(code,payload):
    return Mock(status_code=code,json=lambda:payload)


def test_status_failure_is_not_reported_as_pass():
    assert not check_response(response(500,{}),200)['passed']


def test_acceptance_runner_does_not_submit_reviews_or_start_model(monkeypatch):
    from run_acceptance_checks import requests
    calls=[]
    class Session:
        def __init__(self):self.headers={};self.user=''
        def get(self,path,**kwargs):
            calls.append(('GET',path))
            if path.endswith('/me'):return response(200,{'role':'assessor'})
            if path.endswith('/assessments'):return response(200,[{'assessment_id':'known'}])
            if '/assessments/' in path and '/known/' not in path:return response(403,{})
            return response(200,{})
        def post(self,path,json=None,**kwargs):
            calls.append(('POST',path))
            if path.endswith('/login'):return response(200,{'access_token':'private-token'})
            if path.endswith('/logout'):return response(200,{})
            assert path.endswith(('/batches','/approval'))
            return response(403,{})
        def close(self):pass
    monkeypatch.setattr(requests,'Session',Session)
    monkeypatch.setattr(requests,'get',lambda *args,**kwargs:response(401,{}))
    report=run('http://local',[('member','private-password')])
    assert report['passed'] and not report['gui_tested']
    assert 'private-password' not in json.dumps(report) and 'private-token' not in json.dumps(report)
    assert not any('/reviews' in p or '/run?' in p for _,p in calls)


def test_missing_credentials_do_not_become_passed_accounts(monkeypatch):
    from run_acceptance_checks import requests
    monkeypatch.setattr(requests,'get',lambda *args,**kwargs:response(401,{}))
    report=run('http://local',[('missing',None)])
    assert not report['passed'] and report['missing_credentials']==['missing']
