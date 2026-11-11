import json
from datetime import datetime,timezone
from unittest.mock import MagicMock
from types import SimpleNamespace
import pytest
from agent_core import a8_assessment as a8
from evidence_collectors import a8_live as live
from evidence_collectors.a8_live_extended import SPECS,evaluate
from test_a8_live import encoded

HASH='1'*64
NOW=datetime.now(timezone.utc)
SAMPLES={
 'A.8.1':dict(read_rc=1,decrypt_rc=0,decrypted_sha256=HASH,original_sha256=HASH,plaintext_copy_exists=False),
 'A.8.2':dict(privileged_write_rc=1,account='uid=1001(labadmin)',review_csv='subject,decision,reviewed_at\nlabadmin,approved,'+NOW.isoformat()+'\n'),
 'A.8.5':dict(bad_password={'response':'401 invalid'},authenticated={'response':'200 ok'},no_second_factor={'response':'403 missing'}),
 'A.8.7':dict(scanner_exit_code=66,quarantine_files=['quarantined.txt'],signature_mtime=NOW.isoformat()),
 'A.8.8':dict(scan_configuration={'enabled':True},inventory_rc=0,inventory='pkg\t1.2\n',advisory_catalog=[dict(package='pkg',affected_version='1.0',severity='critical')]),
 'A.8.9':dict(baseline={'ticket':'CAB-LAB-001','sha256':HASH},current_sha256=HASH),
 'A.8.12':dict(transaction={'response':'403 blocked'},audit_events=[dict(action='blocked',payload_sha256=HASH)]),
 'A.8.16':dict(monitor_configuration={'enabled':True},events=[dict(event='file_changed',latency_ms=20)],delivery_receipts=[dict(receipt_sha256=HASH)]),
 'A.8.17':dict(reference_reply={'signature':'signature'},signature_verify_rc=0,offset_ms=0.5,round_trip_ms=10),
 'A.8.20':dict(unapproved_source={'response':'403 denied'},approved_source={'response':'200 allowed'}),
 'A.8.22':dict(employee_to_admin={'response':'403 denied'},employee_to_business={'response':'200 allowed'}),
 'A.8.24':dict(handshake_rc=0,handshake={'tls_version':'TLSv1.3'},key_read_rc=1,key_mode='0o600'),
 'A.8.32':dict(approval={'ticket':'CAB-LAB-032','sha256':HASH},current_release_sha256=HASH,rollback_rc=0,restored_sha256=HASH,expected_release_sha256=HASH)
}


@pytest.mark.parametrize('cid',list(SPECS))
def test_extended_sources_interpreted_and_empty_sources_never_pass(cid):
    assert evaluate(cid,SAMPLES[cid],NOW)==((True,True),[])
    values,errors=evaluate(cid,{},NOW)
    assert values==(None,None) and errors


@pytest.mark.parametrize('cid',list(SPECS))
def test_extended_collector_binds_raw_payload_to_control_and_capture_time(monkeypatch,cid):
    c=next(c for c in a8.catalog('live') if c['control_id']==cid)
    payload=dict(schema='a8-active-observation-v2',control_id=cid,asset_id='test-container',
                 observed_at=NOW.isoformat(),observations=SAMPLES[cid],collection_errors=[])
    raw=encoded({'observed_at':NOW.isoformat(),'probe.json':json.dumps(payload)})
    process=MagicMock(return_value=SimpleNamespace(returncode=0,stdout=raw))
    monkeypatch.setattr(live.subprocess,'run',process)
    evidence=live.collect_live('conforming',c)
    assert evidence['observation_available'] and all(v is True for v in evidence['facts'].values())
    assert evidence['probe_kind']=='container-active-self-test'
    assert any(a['artifact']=='probe.json' for a in evidence['artifacts'])
    payload['control_id']='A.8.999'
    process.return_value.stdout=encoded({'observed_at':NOW.isoformat(),'probe.json':json.dumps(payload)})
    rejected=live.collect_live('conforming',c)
    assert set(rejected['facts'].values())=={None} and rejected['collection_errors']


def test_passive_and_active_catalog_have_distinct_honest_checks():
    controls={c['control_id']:c for c in a8.catalog('live')}
    assert controls['A.8.1']['checks']!=a8.catalog()[0]['checks']
    assert all(c['verification_kind']=='container-active-self-test' for c in controls['A.8.17']['criteria'])
    assert 'không chứng minh NTP' in controls['A.8.17']['criteria'][1]['pass_condition']


def test_probe_errors_do_not_invoke_model_on_metadata_only_packet(monkeypatch):
    c=a8.catalog('live')[0]
    payload=dict(schema='a8-active-observation-v2',control_id=c['control_id'],asset_id='test-container',observed_at=NOW.isoformat(),
                 observations={},collection_errors=[dict(error='FileNotFoundError',detail='Missing active source')])
    monkeypatch.setattr(live.subprocess,'run',MagicMock(return_value=SimpleNamespace(returncode=0,
        stdout=encoded({'observed_at':NOW.isoformat(),'probe.json':json.dumps(payload)}))))
    e=live.collect_live('incomplete',c)
    monkeypatch.setattr(a8.ollama,'Client',lambda **_:pytest.fail('No usable observations, must not call model'))
    assert not e['observation_available'] and a8.assess(c,e,'llm')['execution_source']=='evidence-availability-check'
    assert 'incomplete' not in json.dumps(e)


@pytest.mark.parametrize('payload',[[],None,{'observations':True},'not-an-object'])
def test_malformed_active_packet_is_unknown_not_worker_crash(monkeypatch,payload):
    c=a8.catalog('live')[0]
    monkeypatch.setattr(live.subprocess,'run',MagicMock(return_value=SimpleNamespace(returncode=0,
        stdout=encoded({'probe.json':json.dumps(payload)}))))
    evidence=live.collect_live('mixed',c)
    assert all(v is None for v in evidence['facts'].values()) and evidence['collection_errors']


def test_command_execution_failure_is_unknown_not_policy_failure():
    values,errors=evaluate('A.8.1',{**SAMPLES['A.8.1'],'read_rc':2},NOW)
    assert values==(None,True) and errors
