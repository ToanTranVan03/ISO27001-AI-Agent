import copy
import json
from contextlib import nullcontext
import pytest
from agent_core import a8_assessment as a8
from backend import a8_evidence_import as importer

AID='7f7c009b-bdcd-5b33-934e-15251ad2c976'
RID='00000000-0000-0000-0000-000000000001'


def document():
    # Isolated unit fixture only; no production study or human labels are created.
    report=a8.run('mixed','rules');report['transport']='live'
    report['sha256']=a8.digest({k:v for k,v in report.items() if k!='sha256'})
    return dict(state='finished',report=report)


def test_import_preparation_preserves_raw_sources_but_excludes_predictions_and_labels():
    doc=document();before=copy.deepcopy(doc)
    packets,skipped=importer.prepare_sources(AID,RID,doc)
    assert len(packets)==18 and not skipped and doc==before
    source=json.loads(packets[0]['extracted_text'])
    assert source['is_synthetic'] and not source['provenance_verified']
    assert source['artifacts']==doc['report']['records'][0]['evidence']['artifacts']
    assert not {'status','rationale','expected','facts','reviews','profile'}&source.keys()
    assert importer.prepare_sources(AID,RID,doc)[0]==packets
    assert importer.prepare_sources('00000000-0000-0000-0000-000000000002',RID,doc)[0][0]['evidence_id']!=packets[0]['evidence_id']


def test_import_refuses_replay_tampered_report_and_bad_artifact_hash():
    doc=document();doc['report']['transport']='files'
    with pytest.raises(ValueError):importer.prepare_sources(AID,RID,doc)
    doc=document();doc['report']['records'][0]['status']='Compliant'
    with pytest.raises(ValueError,match='Report hash'):importer.prepare_sources(AID,RID,doc)
    doc=document();doc['report']['records'][0]['evidence']['artifacts'][0]['content']='changed'
    doc['report']['sha256']=a8.digest({k:v for k,v in doc['report'].items() if k!='sha256'})
    with pytest.raises(ValueError,match='Artifact hash'):importer.prepare_sources(AID,RID,doc)


def test_import_locks_all_controls_before_writing_and_is_idempotent(monkeypatch):
    doc=document();packets,_=importer.prepare_sources(AID,RID,doc)
    inserted=set();calls=[]
    class Cursor:
        busy=False
        last=None
        def execute(self,sql,params):
            calls.append(sql)
            if 'INSERT INTO evidence(' in sql:
                self.last=(params[0],) if params[0] not in inserted else None
                inserted.add(params[0])
        def fetchall(self):return [(p['control_id'],'RUNNING' if self.busy else 'NOT_STARTED') for p in packets]
        def fetchone(self):return self.last
    cursor=Cursor()
    class Connection:
        def cursor(self):return nullcontext(cursor)
    monkeypatch.setattr(importer,'get_connection',lambda:nullcontext(Connection()))
    cursor.busy=True
    with pytest.raises(ValueError,match='đang đánh giá'):importer.import_sources(AID,RID,doc,'admin')
    assert not inserted and all('INSERT' not in sql for sql in calls)
    cursor.busy=False
    first=importer.import_sources(AID,RID,doc,'admin');second=importer.import_sources(AID,RID,doc,'admin')
    assert len(first['inserted'])==18 and len(second['reused'])==18 and not second['inserted']
    assert all('TRUE' in sql for sql in calls if 'INSERT INTO evidence(' in sql)


def test_representative_sources_alone_cannot_establish_full_control_compliance():
    from agent_core.graph_builder import node_verify
    state=dict(source_mode='user_evidence_only',collected_evidences=[dict(evidence_id='e',source='a8-capture://run/A.8.1')],
               proposed_evidence_ids=['e'],compliance_status='Compliant',confidence=0.9,rationale='claimed full compliance',audit_trail=[])
    result=node_verify(state)
    assert result['compliance_status']=='Insufficient Evidence' and result['confidence']==0
    assert result['validated_evidence_ids']==['e']


def test_explicit_lab_source_filter_binds_like_pattern_as_parameter(monkeypatch):
    from backend import database
    calls=[]
    class Cursor:
        def execute(self,sql,params):calls.append((sql,params))
        def fetchall(self):return [('captured',)]
    class Connection:
        def cursor(self):return nullcontext(Cursor())
    monkeypatch.setattr(database,'get_connection',lambda:nullcontext(Connection()))
    monkeypatch.setattr(database,'collect_evidence',lambda *_:([dict(evidence_id='captured'),dict(evidence_id='preset')],{}))
    sources,_=database.collect_user_evidence('A.8.1',AID)
    assert sources==[dict(evidence_id='captured')]
    sql,params=calls[0]
    assert 'source LIKE %s' in sql and params==(AID,'A.8.1','a8-capture://%')
