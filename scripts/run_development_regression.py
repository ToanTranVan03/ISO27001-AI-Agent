"""Run the existing 38 development cases without changing formal assessment data."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent_core.a8_assessment import catalog, digest
from agent_core.development_lab import (
    build_bundle, compare_designer, designer_reference, evaluate, reference_hash,
)


def _write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def _validate(bundle, reference):
    scope = json.loads((ROOT / 'docs/56_controls_scope.json').read_text(encoding='utf-8'))
    expected = {c['control_id'] for c in scope} - {c['control_id'] for c in catalog()}
    ids = [c['control_id'] for c in bundle['cases']]
    if len(ids) != 38 or len(set(ids)) != 38 or set(ids) != expected:
        raise ValueError('Development bundle must be exactly the 38-control complement')
    if bundle.get('is_synthetic') is not True or bundle.get('independent_validation') is not False:
        raise ValueError('Development origin and independence must be explicit')
    if 'designer_verdicts' in json.dumps(bundle):
        raise ValueError('Designer key must never enter model source bundle')
    if bundle['sha256'] != digest({k: v for k, v in bundle.items() if k != 'sha256'}):
        raise ValueError('Source bundle hash mismatch')
    if set(reference) != expected or any(
        len(reference[c['control_id']]['designer_verdicts']) != len(c['criteria'])
        for c in bundle['cases']
    ):
        raise ValueError('Designer key does not match development criteria')


def run(output_dir, model, generate=None):
    """Create one immutable run directory; at most two calls per case, errors only."""
    output = Path(output_dir).resolve()
    if not output.is_relative_to((ROOT / 'work/development-lab').resolve()):
        raise ValueError('Output must be a new directory under work/development-lab')
    bundle, reference = build_bundle(), designer_reference()
    _validate(bundle, reference)
    output.mkdir(parents=True, exist_ok=False)
    # Both sources and key are sealed before any call. Only cases go to evaluate.
    _write(output / 'source-snapshot.json', bundle)
    _write(output / 'designer-key.json', reference)
    manifest = dict(protocol='development-regression-v1', run_id=str(uuid4()), model=model,
        started_at=datetime.now(timezone.utc).isoformat(), bundle_sha256=bundle['sha256'],
        designer_reference_sha256=reference_hash(reference), total=38,
        is_synthetic=True, independent_validation=False, professional_confirmation=False,
        policy='One retry of technical errors only; never retry a key mismatch.')
    _write(output / 'manifest.json', manifest)
    first, retries, final = [], [], []
    progress_path = output / 'progress.jsonl'
    with progress_path.open('x', encoding='utf-8') as progress:
        def event(value):
            progress.write(json.dumps(value, ensure_ascii=False) + '\n')
            progress.flush()
            os.fsync(progress.fileno())
        event(dict(state='SNAPSHOT_SEALED', **manifest))
        try:
            for case in bundle['cases']:
                cid = case['control_id']
                event(dict(state='RUNNING', control_id=cid, completed=len(final)))
                initial = evaluate(case, model, generate)
                first.append(initial)
                _write(output / f'{cid}-first.json', initial)
                result = initial
                if initial['error']:
                    event(dict(state='RETRY_TECHNICAL_ERROR', control_id=cid, error=initial['error']))
                    result = evaluate(case, model, generate)
                    retries.append(result)
                    _write(output / f'{cid}-retry.json', result)
                final.append(result)
                _write(output / f'{cid}-final.json', result)
                event(dict(state='CONTROL_FINISHED', control_id=cid, completed=len(final),
                           error=result['error'], status=result['status']))
                print(json.dumps(dict(control_id=cid, completed=len(final), error=result['error'])), flush=True)
        except BaseException as exc:
            _write(output / 'interrupted.json', dict(state='INTERRUPTED',
                completed=len(final), error=type(exc).__name__, results=first,
                repair_attempts=retries, final_results=final))
            event(dict(state='INTERRUPTED', completed=len(final), error=type(exc).__name__))
            raise
        report = dict(**manifest, state='COMPLETED', finished_at=datetime.now(timezone.utc).isoformat(),
            designer_reference_snapshot=reference,
            results=first, repair_attempts=retries, final_results=final,
            initial_errors=sum(bool(r['error']) for r in first),
            final_errors=sum(bool(r['error']) for r in final),
            final_status_counts=dict(Counter(r['status'] or 'ERROR' for r in final)),
            designer_comparison=compare_designer(first, reference),
            designer_comparison_after_retry=compare_designer(final, reference),
            note='Known assistant-authored development data. Key agreement is not independent accuracy, human approval or ISO compliance.')
        _write(output / 'report.json', report)
        event(dict(state='COMPLETED', completed=len(final), final_errors=report['final_errors']))
    return report


def main():
    from dotenv import load_dotenv
    load_dotenv(ROOT / '.env')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--model', default=os.getenv('OLLAMA_MODEL', 'qwen2.5:7b'))
    args = parser.parse_args()
    report = run(args.output_dir, args.model)
    print(json.dumps(dict(state=report['state'], total=report['total'],
                         initial_errors=report['initial_errors'], final_errors=report['final_errors'])))
    return 1 if report['final_errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
