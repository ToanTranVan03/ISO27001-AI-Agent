from lab_a8.mfa_remediation_demo import run_demo



def approve(plan, _before):
    assert plan['target'] == 'labadmin-mfa-demo'
    return 'test operator'


def test_no_approval_does_not_call_tool():
    def unexpected(_path):
        raise AssertionError('Tool must not run')
    result = run_demo(lambda *_: None, unexpected)
    assert result['status'] == 'AWAITING_APPROVAL'
    assert result['execution'] is result['after'] is None


def test_approved_write_and_separate_login_verification():
    result = run_demo(approve)
    assert not result['before']['met']
    assert result['execution']['status'] == 'SUCCEEDED'
    assert result['after']['met']
    assert result['status'] == 'VERIFIED_MET'


def test_tool_error_is_recorded():
    def failing(_path):
        raise OSError('test failure')
    result = run_demo(approve, failing)
    assert result['status'] == 'EXECUTION_FAILED'
    assert result['execution']['error_type'] == 'OSError'
    assert not result['after']['met']


def test_tool_success_does_not_override_failed_readback():
    result = run_demo(approve, lambda _path: None)
    assert result['execution']['status'] == 'SUCCEEDED'
    assert result['status'] == 'VERIFIED_NOT_MET'
    assert not result['after']['met']
