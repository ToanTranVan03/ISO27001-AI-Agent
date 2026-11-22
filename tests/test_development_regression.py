import json
import pytest

from scripts import run_development_regression as runner


def output(tmp_path, monkeypatch):
    # Only redirect the write boundary, retaining the real scope and source files.
    root = tmp_path / 'project'
    (root / 'docs').mkdir(parents=True)
    (root / 'docs/56_controls_scope.json').write_bytes(
        (runner.ROOT / 'docs/56_controls_scope.json').read_bytes())
    monkeypatch.setattr(runner, 'ROOT', root)
    return root / 'work/development-lab/new-run'


def reply(prompt):
    case = json.loads(prompt.split('INPUT:\n', 1)[1])
    assert 'designer_verdicts' not in prompt
    return json.dumps({'checks': [dict(criterion_index=i, verdict='unknown',
        rationale='Development source requires further observation',
        source_files=[case['artifacts'][0]['filename']]) for i in range(len(case['criteria']))]})


def test_snapshot_before_calls_and_immutable_per_control_results(tmp_path, monkeypatch):
    dest = output(tmp_path, monkeypatch)
    calls = []
    def generate(prompt):
        assert (dest / 'manifest.json').exists()
        snapshot = json.loads((dest / 'source-snapshot.json').read_text(encoding='utf-8'))
        manifest = json.loads((dest / 'manifest.json').read_text(encoding='utf-8'))
        key = json.loads((dest / 'designer-key.json').read_text(encoding='utf-8'))
        assert snapshot['sha256'] == manifest['bundle_sha256']
        assert runner.reference_hash(key) == manifest['designer_reference_sha256']
        calls.append(prompt)
        return reply(prompt)
    report = runner.run(dest, 'fake', generate)
    assert len(calls) == 38 and not report['repair_attempts']
    assert report['state'] == 'COMPLETED' and report['final_errors'] == 0
    assert not report['independent_validation'] and not report['professional_confirmation']
    from uuid import UUID
    from agent_core.development_lab_audit import audit
    assert str(UUID(report['run_id'])) == report['run_id']
    assert report['run_id'] == json.loads((dest / 'manifest.json').read_text(encoding='utf-8'))['run_id']
    assert runner.reference_hash(report['designer_reference_snapshot']) == report['designer_reference_sha256']
    assert audit(report)['key_binding'] == 'FROZEN_BEFORE_RUN'
    assert len(list(dest.glob('A.*-first.json'))) == 38
    assert len(list(dest.glob('A.*-final.json'))) == 38
    before = (dest / 'report.json').read_bytes()
    with pytest.raises(FileExistsError):
        runner.run(dest, 'fake', generate)
    assert (dest / 'report.json').read_bytes() == before and len(calls) == 38


def test_only_one_retry_and_first_malformed_output_retained(tmp_path, monkeypatch):
    dest = output(tmp_path, monkeypatch)
    calls = []
    def generate(prompt):
        calls.append(prompt)
        return 'malformed original response' if len(calls) <= 2 else reply(prompt)
    report = runner.run(dest, 'fake', generate)
    assert len(calls) == 39 and len(report['repair_attempts']) == 1
    assert report['initial_errors'] == report['final_errors'] == 1
    assert report['results'][0]['raw_response'] == 'malformed original response'
    assert report['final_results'][0]['error']


def test_interrupt_preserves_completed_results_and_progress(tmp_path, monkeypatch):
    dest = output(tmp_path, monkeypatch)
    calls = []
    def generate(prompt):
        calls.append(prompt)
        if len(calls) == 2:
            raise KeyboardInterrupt
        return reply(prompt)
    with pytest.raises(KeyboardInterrupt):
        runner.run(dest, 'fake', generate)
    report = json.loads((dest / 'interrupted.json').read_text(encoding='utf-8'))
    assert report['state'] == 'INTERRUPTED' and report['completed'] == 1
    assert len(list(dest.glob('A.*-final.json'))) == 1
    assert not (dest / 'report.json').exists()
    events = [json.loads(line) for line in (dest / 'progress.jsonl').read_text(encoding='utf-8').splitlines()]
    assert events[-1]['state'] == 'INTERRUPTED'


def test_repaired_output_is_separate_from_initial_error(tmp_path, monkeypatch):
    dest = output(tmp_path, monkeypatch)
    calls = []
    def generate(prompt):
        calls.append(prompt)
        return 'bad first response' if len(calls) == 1 else reply(prompt)
    report = runner.run(dest, 'fake', generate)
    assert len(calls) == 39 and report['initial_errors'] == 1 and report['final_errors'] == 0
    assert report['results'][0]['error'] and not report['final_results'][0]['error']
    assert len(report['repair_attempts']) == 1
    cid = report['results'][0]['control_id']
    assert json.loads((dest / f'{cid}-first.json').read_text(encoding='utf-8'))['raw_response'] == 'bad first response'
    assert not json.loads((dest / f'{cid}-retry.json').read_text(encoding='utf-8'))['error']


def test_wrong_scope_or_output_rejected_before_model_call(tmp_path, monkeypatch):
    dest = output(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match='under work'):
        runner.run(tmp_path / 'unrestricted', 'fake', reply)
    original = runner.build_bundle()
    original['cases'] = original['cases'][:-1]
    monkeypatch.setattr(runner, 'build_bundle', lambda: original)
    with pytest.raises(ValueError, match='38-control complement'):
        runner.run(dest, 'fake', reply)
    assert not dest.exists()
