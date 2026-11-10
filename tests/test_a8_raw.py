import json
from pathlib import Path
import pytest
from evidence_collectors import a8_raw
from agent_core import a8_assessment as a8
from agent_core.a8_benchmark import score


@pytest.mark.parametrize('profile',['stale','conflicting'])
def test_stale_or_conflicting_capture_is_not_a_pass(profile):
    report=a8.run(profile,'rules')
    assert all(r['status']=='Insufficient Evidence' for r in report['records'])
    assert all(r['evidence']['collection_errors'] for r in report['records'])


def test_raw_collector_recomputes_backup_integrity_after_tampering(monkeypatch,tmp_path):
    import shutil
    root=tmp_path/'conforming'/'A.8.13'
    shutil.copytree(a8_raw.ROOT/'conforming'/'A.8.13',root)
    monkeypatch.setattr(a8_raw,'ROOT',tmp_path)
    c=next(c for c in a8.catalog() if c['control_id']=='A.8.13')
    first=a8_raw.collect_raw('conforming',c)
    assert all(first['facts'].values())
    (root/'backup.dat').write_bytes(b'tampered')
    second=a8_raw.collect_raw('conforming',c)
    assert second['facts']['backup_success'] is False
    assert second['source_sha256']!=first['source_sha256']


def test_malformed_clock_record_is_unknown_not_pass(monkeypatch,tmp_path):
    import shutil
    root=tmp_path/'conforming'/'A.8.17'
    shutil.copytree(a8_raw.ROOT/'conforming'/'A.8.17',root)
    (root/'tracking.txt').write_text('corrupt tracking record')
    monkeypatch.setattr(a8_raw,'ROOT',tmp_path)
    c=next(c for c in a8.catalog() if c['control_id']=='A.8.17')
    e=a8_raw.collect_raw('conforming',c)
    assert e['facts']['clock_offset_within_policy'] is None


def test_no_source_means_missing_evidence(monkeypatch,tmp_path):
    monkeypatch.setattr(a8_raw,'ROOT',tmp_path)
    e=a8_raw.collect_raw('conforming',a8.catalog()[0])
    assert all(v is None for v in e['facts'].values())
    assert e['collection_errors']


def test_precision_recall_counts_misclassification():
    report=a8.run('mixed','rules')
    r=report['records'][0]
    labels=[{'case_id':r['case_id'],'expected':'Insufficient Evidence','label_origin':'human'}]
    row=score([report],labels)['per_control'][0]
    assert row['class_metrics']['Insufficient Evidence']['recall']==0
    assert row['class_metrics']['Partially Compliant']['precision']==0
    assert row['mean_duration_ms']>=0



def test_raw_evidence_exposes_original_text_without_reference_labels():
    e=a8.collect('mixed',a8.catalog()[0])
    assert any('Active: active (running)' in a['content'] for a in e['artifacts'])
    assert all(len(a['sha256'])==64 for a in e['artifacts'])
    assert 'mixed' not in json.dumps(e) and 'expected' not in json.dumps(e)
