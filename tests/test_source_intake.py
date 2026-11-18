import json
from contextlib import contextmanager,nullcontext
import pytest
from evidence_collectors import source_intake as intake
from evidence_collectors.source_quality import evidence_quality

AID='7f7c009b-bdcd-5b33-934e-15251ad2c976'
TEXT=b'Observed firewall policy: inbound TCP 22 is restricted to the administrator subnet.'


def prepare(**changes):
    c=intake.controls()[0]
    args=dict(assessment_id=AID,control_id=c['control_id'],filename='record.log',raw=TEXT,
              evidence_type=c['expected_evidence_types'][0],origin='Export supplied by lab owner',observed_at='2026-11-17T08:00:00+07:00')
    args.update(changes)
    return intake.prepare(**args)


def test_all_56_controls_accept_valid_sources_with_their_own_type():
    for c in intake.controls():
        item=prepare(control_id=c['control_id'],evidence_type=c['expected_evidence_types'][0])
        payload=json.loads(item['extracted_text'])
        assert payload['control_id']==c['control_id'] and payload['observed_at']=='2026-11-17T01:00:00+00:00'
        assert payload['provenance_verified'] is False
        assert evidence_quality(item['extracted_text'])['usable']


def test_identity_changes_with_bytes_metadata_and_campaign_but_retries_reuse_identity():
    first=prepare()
    assert first==prepare()
    for change in ({'raw':TEXT+b' Additional event recorded.'},{'origin':'Another export source'},
                   {'assessment_id':'00000000-0000-0000-0000-000000000001'}):
        assert prepare(**change)['evidence_id']!=first['evidence_id']


@pytest.mark.parametrize('change',[
    {'filename':'../x.log'},{'filename':'folder\\x.log'},{'filename':'_REQUIRED.md'},
    {'filename':'x.exe'},{'raw':b'x'},{'raw':b'f'*200},{'raw':b'\x00'+TEXT},
    {'raw':b'\xff'*30},{'origin':'x'},{'observed_at':'2026-11-17T08:00:00'},
    {'observed_at':'2099-11-17T08:00:00+07:00'},{'control_id':'A.9.1'},
    {'evidence_type':'not_supported'},{'filename':'source.json','raw':b'{ broken json but long enough for quality check'},
])
def test_invalid_source_never_prepares_evidence(change):
    with pytest.raises((ValueError,UnicodeError)):prepare(**change)


def test_metadata_wrapper_does_not_hide_unusable_content():
    payload={'source_kind':'USER_PROVIDED_PACKAGE','origin':'Long provenance metadata from responsible owner','content':'x'}
    assert not evidence_quality(json.dumps(payload))['usable']
    payload['content']=True
    assert not evidence_quality(json.dumps(payload))['usable']


def test_original_is_preserved_once_and_tampering_is_not_overwritten(tmp_path,monkeypatch):
    monkeypatch.setattr(intake,'ORIGINALS',tmp_path)
    path=intake.preserve(AID,TEXT)
    assert path.read_bytes()==TEXT and intake.preserve(AID,TEXT)==path
    path.write_bytes(b'changed')
    with pytest.raises(ValueError,match='không khớp'):intake.preserve(AID,TEXT)
    assert path.read_bytes()==b'changed'


def test_download_lookup_is_bound_to_campaign_control_and_evidence(monkeypatch,tmp_path):
    from backend import database
    item=prepare();monkeypatch.setattr(intake,'ORIGINALS',tmp_path);intake.preserve(AID,TEXT)
    class Cursor:
        def execute(self,sql,args):assert args==(AID,'A.6.1',item['evidence_id'])
        def fetchone(self):return (item['extracted_text'],item['sha256_hash'])
    class Connection:
        def cursor(self):return nullcontext(Cursor())
    @contextmanager
    def connect():yield Connection()
    monkeypatch.setattr(database,'get_connection',connect)
    path,name=intake.retrieve(AID,'A.6.1',item['evidence_id'])
    assert name=='record.log' and path.read_bytes()==TEXT
    path.write_bytes(b'tampered')
    with pytest.raises(ValueError):intake.retrieve(AID,'A.6.1',item['evidence_id'])


def test_web_intake_keeps_auth_scope_and_validation_before_storage(monkeypatch,tmp_path):
    from fastapi import HTTPException
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend import enterprise_api
    from backend.team_api import require_user
    from evidence_collectors import control_packages
    base=f'/api/assessments/{AID}/enterprise/scope56/controls/A.6.1/sources'
    c=intake.controls()[0];form={'evidence_type':c['expected_evidence_types'][0],'origin':'Lab export by owner'}
    client=TestClient(app)
    assert client.post(base+'/upload',data=form,files={'file':('record.log',TEXT)}).status_code==401
    app.dependency_overrides[require_user]=lambda:{'user_id':'reviewer','role':'member'}
    monkeypatch.setattr(intake,'ORIGINALS',tmp_path)
    def deny(*args):raise HTTPException(403,'Not a campaign member')
    try:
        monkeypatch.setattr(enterprise_api,'require_campaign',deny)
        assert client.post(base+'/upload',data=form,files={'file':('record.log',TEXT)}).status_code==403
        assert client.get(base+'/WEB-test/original').status_code==403
        monkeypatch.setattr(enterprise_api,'require_campaign',lambda *_:None)
        stored=[]
        def store(aid,cid,uid,packet):
            assert (aid,cid,uid)==(AID,'A.6.1','reviewer')
            stored.extend(packet['items']);return {'inserted':[packet['items'][0]['evidence_id']],'reused':[],'issues':[]}
        monkeypatch.setattr(control_packages,'store',store)
        bad=client.post(base+'/upload',data=form,files={'file':('record.log',b'x')})
        assert bad.status_code==422 and not stored
        good=client.post(base+'/upload',data=form,files={'file':('record.log',TEXT)})
        assert good.status_code==201 and good.json()['original_preserved'] and len(stored)==1
    finally:app.dependency_overrides.pop(require_user,None)
