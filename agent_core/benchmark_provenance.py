"""Separate real model trials from deliberate model-outage recovery experiments.

Recovery here is an explicit benchmark harness, not an assertion that autonomous.py
silently falls back in production. The AI failure remains a failure in raw results.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from agent_core.research_benchmark import case_snapshot, run_case, summarize


def recovery_trial(case):
    # Inject an unavailable transport, never fabricate a successful model response.
    with patch('agent_core.autonomous.urlopen', side_effect=OSError('benchmark injected model outage')):
        failed = run_case(case, 'ai')
    if failed['success']:
        raise RuntimeError('Fault injection did not reach the model transport')
    recovery = run_case(case, 'workflow')
    return {**recovery, 'mode': 'explicit_workflow_recovery',
            'execution_source': 'workflow-after-injected-model-failure',
            'fault_injected': True, 'model_failure': failed,
            'model_calls': failed['model_calls'],
            'elapsed_ms': round(failed['elapsed_ms'] + recovery['elapsed_ms'], 2)}


def enrich(study):
    for row in study['trials']:
        row['execution_source'] = {'ai': 'ollama-real-no-fallback', 'rules': 'deterministic-evaluator',
                                   'workflow': 'deterministic-workflow'}[row['mode']]
        row['fallback_used'] = False
        row['fault_injected'] = False
    recovery = [recovery_trial(c) for c in study['cases']]
    return {'generated_at': datetime.now(timezone.utc).isoformat(),
            'scope': 'Synthetic people-control evaluator; not a benchmark of every enterprise SOC path.',
            'real_trials': study, 'recovery_trials': recovery,
            'recovery_summary': summarize(recovery),
            'same_recovery_snapshots': all(r['snapshot_hash'] == hashlib.sha256(
                json.dumps(case_snapshot(c), sort_keys=True, ensure_ascii=False).encode()).hexdigest()
                for c, r in zip(study['cases'], recovery)),
            'limitations': ['Recovery is explicit fault injection, not observed production fallback frequency.',
                            'All modes share the evaluator; equal labels do not prove LLM superiority.',
                            'One repetition on eight authored cases; no general accuracy claim.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    study = json.loads(args.input.read_text(encoding='utf-8'))
    result = enrich(study)
    result['input_sha256'] = hashlib.sha256(args.input.read_bytes()).hexdigest()
    result['harness_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
