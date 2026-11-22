from scripts.check_source_before_intake import check
from evidence_collectors.source_intake import controls

AID='7f7c009b-bdcd-5b33-934e-15251ad2c976'


def test_valid_preflight_never_stores_original_or_creates_evidence(tmp_path,monkeypatch):
    from evidence_collectors import source_intake
    def forbidden(*args,**kwargs):raise AssertionError('Preflight must not store evidence')
    monkeypatch.setattr(source_intake,'preserve',forbidden)
    source=tmp_path/'source.txt'
    raw=b'Synthetic test only: observed security policy requires personnel review.'
    source.write_bytes(raw);c=controls()[0]
    report=check(source,AID,c['control_id'],c['expected_evidence_types'][0],'Synthetic software test')
    assert report['passed'] and not report['writes_evidence'] and report['warnings']
    assert not report['coverage_verified'] and not report['provenance_verified']
    assert list(tmp_path.iterdir())==[source] and source.read_bytes()==raw
    assert 'Synthetic test only' not in str(report)  # no private text in report


def test_invalid_content_metadata_and_missing_file_stay_rejected(tmp_path):
    source=tmp_path/'source.txt';source.write_text('x',encoding='utf-8');c=controls()[0]
    for path,cid,kind in [(source,c['control_id'],c['expected_evidence_types'][0]),
                          (source,'A.9.1','unknown'),(tmp_path/'absent.txt',c['control_id'],'unknown')]:
        report=check(path,AID,cid,kind,'Synthetic software test')
        assert not report['passed'] and report['issues'] and not report['writes_evidence']
