"""Unit checks for the opt-in source connector (no production database writes)."""
import json
from pathlib import Path

import pytest
from backend import auto_sources


def test_source_is_off_by_default(monkeypatch):
    monkeypatch.delenv('ISO_AUTO_EVIDENCE_DIR', raising=False)
    assert auto_sources.get_manifest() == (None, [])


def test_manifest_is_never_a_disk_crawl(monkeypatch, tmp_path):
    (tmp_path / 'good.pdf').write_bytes(b'%PDF-1.4')
    (tmp_path / 'other.pdf').write_bytes(b'other')
    (tmp_path / 'manifest.json').write_text(json.dumps({'items': [
        {'control_id': 'A.6.1', 'file': 'good.pdf', 'evidence_type': 'EVID_PPL_HR_RECORD'}
    ]}), encoding='utf-8')
    monkeypatch.setenv('ISO_AUTO_EVIDENCE_DIR', str(tmp_path))
    root, items = auto_sources.get_manifest()
    assert root == tmp_path.resolve()
    assert len(items) == 1
    assert auto_sources.validate_item(items[0], root)[1] == 'good.pdf'


@pytest.mark.parametrize('filename', ['../private.pdf', 'other\\private.pdf', 'x.txt', '/etc/passwd'])
def test_reject_unapproved_filename(tmp_path, filename):
    with pytest.raises(auto_sources.SourceConfigurationError):
        auto_sources.validate_item({'control_id':'A.6.1','file':filename,'evidence_type':'X'}, tmp_path)


def test_reject_manifest_without_items(monkeypatch, tmp_path):
    (tmp_path / 'manifest.json').write_text('{}', encoding='utf-8')
    monkeypatch.setenv('ISO_AUTO_EVIDENCE_DIR', str(tmp_path))
    with pytest.raises(auto_sources.SourceConfigurationError):
        auto_sources.get_manifest()
