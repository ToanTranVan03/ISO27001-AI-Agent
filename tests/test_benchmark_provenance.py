from agent_core.benchmark_provenance import recovery_trial
from agent_core.research_benchmark import benchmark_cases


def test_injected_failure_is_retained_and_recovery_is_not_model_success():
    case = next(c for c in benchmark_cases() if c['id'] == 'A.6.3-unknown')
    result = recovery_trial(case)
    assert not result['model_failure']['success']
    assert result['model_failure']['model_calls'] == 1
    assert result['success'] and result['exact_match']
    assert result['fault_injected']
    assert result['mode'] == 'explicit_workflow_recovery'
