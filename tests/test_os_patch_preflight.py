from copy import deepcopy
import hashlib
import json

from evidence_collectors import control_packages
from evidence_collectors.os_patch_preflight import intake_manifest, preflight


def packet(tmp_path):
    common = dict(asset_id='SYNTHETIC-VM', os_family='test-os', patch_id='test-patch')
    records = {
        'before': dict(common, observed_at='2026-11-28T01:00:00Z', os_build='1', patch_present=False),
        'execution': dict(common, approved_at='2026-11-28T01:01:00Z', executed_at='2026-11-28T01:02:00Z',
                          approval_reference='synthetic-approval', status='succeeded'),
        'after': dict(common, observed_at='2026-11-28T01:03:00Z', os_build='2', patch_present=True,
                      health='ok', reboot_state='not_required', reboot_reason='Synthetic test only'),
    }
    for stage, record in records.items():
        content = f'Synthetic unit-test source for {stage}'.encode()
        file = f'{stage}.txt'
        (tmp_path / file).write_bytes(content)
        record['artifact'] = dict(file=file, sha256=hashlib.sha256(content).hexdigest())
    return records


def test_preflight_ready_for_review_preserves_packet(tmp_path):
    manifest = packet(tmp_path)
    before = deepcopy(manifest)
    assert preflight(manifest, tmp_path)['ready_for_review']
    assert manifest == before


def test_preflight_rejects_wrong_asset_timeline_and_tampered_files(tmp_path):
    manifest = packet(tmp_path)
    manifest['after']['asset_id'] = 'OTHER-VM'
    manifest['after']['observed_at'] = manifest['before']['observed_at']
    (tmp_path / 'before.txt').write_text('tampered')
    report = preflight(manifest, tmp_path)
    assert not report['ready_for_review']
    assert any('asset_id' in issue for issue in report['issues'])
    assert any('Thứ tự' in issue for issue in report['issues'])
    assert any('SHA-256' in issue for issue in report['issues'])


def test_patch_success_without_independent_after_source_cannot_pass(tmp_path):
    manifest = packet(tmp_path)
    manifest['after']['artifact'] = manifest['execution']['artifact']
    manifest['after']['patch_present'] = None
    assert not preflight(manifest, tmp_path)['ready_for_review']
    manifest['after']['artifact'] = {'file': '../outside.txt'}
    assert any('cạnh manifest' in issue for issue in preflight(manifest, tmp_path)['issues'])


def test_intake_uses_checked_files_and_rejects_change_after_preflight(tmp_path,monkeypatch):
    monkeypatch.setattr(control_packages,'ROOT',tmp_path)
    aid='7f7c009b-bdcd-5b33-934e-15251ad2c976'
    folder=control_packages.directory(aid,'A.8.8')
    folder.mkdir(parents=True)
    manifest=packet(folder)
    for record in manifest.values():
        for field in ('observed_at','approved_at','executed_at'):
            if field in record:record[field]=record[field].replace('2026','2020')
    assert preflight(manifest,folder)['ready_for_review']
    intake=intake_manifest(manifest,'Synthetic integration test')
    (folder/'manifest.json').write_text(json.dumps(intake),encoding='utf-8')
    assert len(control_packages.inspect(aid,'A.8.8')['items'])==3
    (folder/'after.txt').write_text('Changed synthetic test file with enough text to be read.')
    report=control_packages.inspect(aid,'A.8.8')
    assert len(report['items'])==2
    assert any('after.txt: SHA-256' in issue for issue in report['issues'])
