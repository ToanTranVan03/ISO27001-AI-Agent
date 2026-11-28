from lab_a8.software_update_demo import run_demo


def test_requires_approval():
    receipt = run_demo(lambda *_: None)
    assert receipt['status'] == 'AWAITING_APPROVAL'
    assert receipt['execution'] is None


def test_approved_update_runs_new_application():
    receipt = run_demo(lambda *_: 'synthetic tester')
    assert receipt['before']['version'] == '1.0.0'
    assert receipt['after']['version'] == '1.1.0'
    assert receipt['after']['sha256'] == receipt['plan']['candidate_sha256']
    assert receipt['status'] == 'VERIFIED_MET'


def test_reports_tool_error_and_false_success_separately():
    def fail(*_):
        raise OSError('synthetic failure')

    assert run_demo(lambda *_: 'test', fail)['status'] == 'EXECUTION_FAILED'
    receipt = run_demo(lambda *_: 'test', lambda *_: None)
    assert receipt['execution']['status'] == 'SUCCEEDED'
    assert receipt['status'] == 'VERIFIED_NOT_MET'


def test_recreated_lab_baseline_has_same_artifact_and_rejects_wrong_hash():
    from lab_a8.software_update_demo import matches_baseline

    first = run_demo(lambda *_: None)
    before = first['before']
    binding = dict(system=before['platform'],baseline_version=before['version'],
                   application=first['plan']['target'],baseline_artifact_sha256=before['sha256'])
    second = run_demo(lambda *_: None)['before']
    assert matches_baseline(binding, second)
    assert not matches_baseline(binding, {**second,'sha256':'0'*64})
