import hashlib
import json
from contextlib import nullcontext
import pytest
from evidence_collectors import source_intake as intake
from evidence_collectors.source_verification import source_quality
from backend.review_criteria import validate_sources

AID='7f7c009b-bdcd-5b33-934e-15251ad2c976'
RAW=b'Synthetic source integrity test only. A dated personnel record must be reviewed separately.'


def web(monkeypatch,tmp_path):
    monkeypatch.setattr(intake,'ORIGINALS',tmp_path)
    item=intake.prepare(AID,'A.6.1','test.txt',RAW,intake.controls()[0]['expected_evidence_types'][0],'Synthetic integrity test only')
    intake.preserve(AID,RAW)
    return item


def check(item,aid=AID):
    return source_quality(aid,'A.6.1',item['evidence_id'],item['evidence_type'],item['source'],item['extracted_text'],item['sha256_hash'])


def test_web_integrity_does_not_assert_authenticity_or_iso_coverage(monkeypatch,tmp_path):
    item=web(monkeypatch,tmp_path);result=check(item)
    assert result['usable'] and result['integrity']['state']=='verified'
    assert json.loads(item['extracted_text'])['provenance_verified'] is False
    legacy=source_quality(AID,'A.6.1','legacy','type','old.docx','Readable original text but preservation is not independently established.','hash')
    assert legacy['usable'] and legacy['integrity']['state']=='not_verifiable'


@pytest.mark.parametrize('change,issue',[('missing','original_missing'),('changed','original_hash_mismatch'),('text','extracted_content_identity_mismatch'),('campaign','extracted_content_identity_mismatch'),('metadata','web_manifest_mismatch')])
def test_corrupt_sources_are_retained_but_not_usable(monkeypatch,tmp_path,change,issue):
    item=web(monkeypatch,tmp_path);original=intake.original_path(AID,item['sha256_hash'])
    aid=AID
    if change=='missing':original.unlink()
    elif change=='changed':original.write_bytes(b'corrupt')
    elif change=='text':
        value=json.loads(item['extracted_text']);value['content']='Modified extracted content that must not be accepted silently.';item['extracted_text']=json.dumps(value,ensure_ascii=False,sort_keys=True)
    elif change=='campaign':aid='00000000-0000-0000-0000-000000000001'
    else:
        value=json.loads(item['extracted_text']);value['original_sha256']='a'*64;item['extracted_text']=json.dumps(value)
    result=check(item,aid)
    assert not result['usable'] and issue in result['issues'] and result['integrity']['state']=='failed'
    evidence=[{'evidence_id':item['evidence_id'],'source_quality':result}]
    with pytest.raises(ValueError):validate_sources([{'verdict':'met','evidence_ids':[item['evidence_id']]}],evidence)
    validate_sources([{'verdict':'unknown','evidence_ids':[item['evidence_id']]}],evidence)


def test_captured_artifacts_are_rechecked_without_reading_an_answer_key():
    artifact={'artifact':'test.log','content':'Synthetic actual artifact contents for software integrity test.'}
    artifact['sha256']=hashlib.sha256(artifact['content'].encode()).hexdigest()
    rid='00000000-0000-0000-0000-000000000001'
    payload={'assessment_id':AID,'control_id':'A.8.15','run_id':rid,'artifacts':[artifact]}
    def capture(wrong_id=False):
        text=json.dumps(payload);checksum=hashlib.sha256(text.encode()).hexdigest()
        eid='A8CAP-'+hashlib.sha256(json.dumps([AID,'A.8.15',checksum]).encode()).hexdigest()[:40]
        return source_quality(AID,'A.8.15','wrong' if wrong_id else eid,'type','a8-capture://'+rid+'/A.8.15',text,checksum)
    assert capture()['integrity']['state']=='verified'
    assert 'capture_identity_mismatch' in capture(True)['issues']
    artifact['content']='Changed contents but checksum was not updated.'
    assert 'capture_artifact_hash_mismatch' in capture()['issues']


def test_model_input_filter_uses_same_integrity_gate_as_human_review(monkeypatch,tmp_path):
    from backend import database
    item=web(monkeypatch,tmp_path);intake.original_path(AID,item['sha256_hash']).write_bytes(b'corrupt')
    source={'evidence_id':item['evidence_id'],'evidence_type':item['evidence_type'],'source':item['source'],
            'content':item['extracted_text'],'sha256_hash':item['sha256_hash']}
    monkeypatch.setattr(database,'collect_evidence',lambda *_:([source,{'evidence_id':'preset'}],{}))
    class Cursor:
        def execute(self,*_):pass
        def fetchall(self):return [(item['evidence_id'],)]
    class Connection:
        def cursor(self):return nullcontext(Cursor())
    monkeypatch.setattr(database,'get_connection',lambda:nullcontext(Connection()))
    sources,diagnostic=database.collect_user_evidence('A.6.1',AID)
    assert sources==[] and diagnostic['source_quality_rejected']==[item['evidence_id']]


@pytest.mark.parametrize('integrity,current',[('verified',True),('failed',False)])
def test_cited_original_integrity_changes_freshness_without_rewriting_history(integrity,current):
    from backend.compliance_report import build_dossier
    cid='A.8.25'
    board=[dict(control_id=cid,workflow_status='COMPLETED',compliance_status='Compliant',latest_evaluation_id=1)]
    evidence={cid:[dict(evidence_id='source',created_at='2026-11-20T01:00:00+00:00',source_quality={'integrity':{'state':integrity}})]}
    history={cid:[dict(evaluation_id=1,status='Compliant',evidence_ids=['source'],created_at='2026-11-20T02:00:00+00:00')]}
    result=build_dossier(AID,board,evidence,history)
    row=result['controls'][0]
    assert row['assessment_state']==('evaluated' if current else 'stale')
    assert row['historical_conclusion']=='Compliant'
    assert row['conclusion']==('Compliant' if current else 'Cần tái đánh giá')
    assert history[cid][0]['status']=='Compliant'
