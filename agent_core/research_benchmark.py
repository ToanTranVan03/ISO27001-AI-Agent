"""Reproducible synthetic acceptance study; labels never enter agent context."""
import argparse
import hashlib
import json
import tempfile
import time
import statistics
from datetime import datetime, timezone
from pathlib import Path

from agent_core.autonomous import AgentStore, agent_events
from agent_core.simulation import build_enterprise, evaluate_enterprise

ROOT = Path(__file__).resolve().parent.parent


def benchmark_cases():
    # Authored independently of CONTROLS/apply_scenario; not an external blind dataset.
    definitions = [
        ('A.6.1', 'screened', 'HF-004'),
        ('A.6.2', 'terms_signed', 'HF-012'),
        ('A.6.3', 'training_passed', 'HF-042'),
        ('A.6.4', 'disciplinary_informed', 'HF-018'),
        ('A.6.5', 'post_employment_ack', 'HF-025'),
        ('A.6.6', 'nda_signed', 'HF-033'),
        ('A.6.7', 'remote_policy_ack', 'HF-028'),
        ('A.6.8', 'reporting_trained', 'HF-049'),
    ]
    cases = []
    for cid, field, pid in definitions:
        for label, value in [('violation', False), ('unknown', None), ('clean', True)]:
            cases.append({'id': f'{cid}-{label}', 'patches': [
                {'collection': 'people', 'id': pid, 'fields': {field: value}}],
                'expected': [] if value is True else [[cid, pid, 'missing' if value is None else 'finding']]})
    cases.extend([
        {'id': 'offboarding-open-assets', 'patches': [
            {'collection': 'people', 'id': 'HF-025', 'fields': {'status': 'terminated'}}],
         'expected': [['A.6.5', 'HF-025', 'finding']]},
        {'id': 'offboarding-repaired', 'patches': [
            {'collection': 'people', 'id': 'HF-025', 'fields': {'status': 'terminated'}},
            *[{'collection': 'accounts', 'id': f'HF-025-{system}', 'fields': {'active': False}}
              for system in ['HR', 'Email', 'VPN', 'Nghiệp vụ']],
            {'collection': 'devices', 'id': 'LT-025', 'fields': {'returned': True}}], 'expected': []},
        {'id': 'remote-asset-risk', 'patches': [
            {'collection': 'people', 'id': 'HF-028', 'fields': {'remote': True}},
            {'collection': 'accounts', 'id': 'HF-028-VPN', 'fields': {'mfa': False}},
            {'collection': 'devices', 'id': 'LT-028', 'fields': {'encrypted': False}}],
         'expected': [['A.6.7', 'HF-028', 'finding']]},
        {'id': 'compound-known-and-unknown', 'patches': [
            {'collection': 'people', 'id': 'HF-012', 'fields': {'nda_signed': False, 'terms_signed': False}},
            {'collection': 'people', 'id': 'HF-042', 'fields': {'training_passed': None}}],
         'expected': [['A.6.6', 'HF-012', 'finding'], ['A.6.2', 'HF-012', 'finding'], ['A.6.3', 'HF-042', 'missing']]},
    ])
    return cases


def case_snapshot(case):
    enterprise = build_enterprise()
    if 'assessment_date' in case:
        enterprise['assessment_date'] = case['assessment_date']
    for patch in case['patches']:
        record = next(r for r in enterprise[patch['collection']] if r['id'] == patch['id'])
        record.update(patch['fields'])
    return enterprise


def advanced_cases():
    def person_case(identifier, cid, fields, kind, tools):
        return {'id': identifier, 'assessment_date': '2026-10-30',
                'patches': [{'collection': 'people', 'id': 'HF-042', 'fields': fields}],
                'expected': [[cid, 'HF-042', kind]] if kind else [], 'required_tools': tools}
    cases = [
        person_case('training-expired', 'A.6.3', {'training_valid_until': '2026-10-29'}, 'finding', ['inspect_context']),
        person_case('training-renewed', 'A.6.3', {'training_valid_until': '2027-10-30'}, None, ['inspect_context']),
        person_case('training-source-conflict', 'A.6.3', {'lms_training_passed': False}, 'missing', ['inspect_context', 'inspect_evidence']),
        person_case('training-source-resolved', 'A.6.3', {'lms_training_passed': True}, None, ['inspect_context']),
        person_case('role-review-pending', 'A.6.5', {'role': 'Điều phối viên', 'access_review_required': True}, 'finding', ['inspect_context']),
        person_case('role-review-complete', 'A.6.5', {'role': 'Điều phối viên', 'access_review_required': True}, None, ['inspect_context']),
    ]
    for case in cases[-2:]:
        case['patches'].extend({'collection': 'accounts', 'id': f'HF-042-{system}',
                                'fields': {'role_reviewed': case['id'] == 'role-review-complete'}}
                               for system in ['HR', 'Email', 'VPN', 'Nghiệp vụ'])
    for label, approved, expiry, expected in [('pending', False, '2026-10-31', 'finding'),
                                             ('approved', True, '2026-10-31', None),
                                             ('expired', True, '2026-10-29', 'finding')]:
        patches = [{'collection': 'people', 'id': 'HF-025', 'fields': {'status': 'terminated'}},
                   {'collection': 'devices', 'id': 'LT-025', 'fields': {'returned': True}}]
        patches.extend({'collection': 'accounts', 'id': f'HF-025-{system}', 'fields': {'active': False}}
                       for system in ['Email', 'VPN', 'Nghiệp vụ'])
        patches.append({'collection': 'accounts', 'id': 'HF-025-HR', 'fields': {'retention_exception': {
            'account_id': 'HF-025-HR', 'scope': 'offboarding-retention', 'approved': approved,
            'approver': 'IT Manager (giả lập)' if approved else None,
            'reason': 'Đối chiếu bàn giao', 'expires_on': expiry}}})
        cases.append({'id': f'retention-{label}', 'assessment_date': '2026-10-30', 'patches': patches,
                      'expected': [['A.6.5', 'HF-025', expected]] if expected else [], 'required_tools': ['inspect_context']})
    return cases


def predictions(controls):
    return {(c['control_id'], f['person_id'], 'finding') for c in controls for f in c['findings']} | {
        (c['control_id'], pid, 'missing') for c in controls for pid in c['missing_evidence']}


def score(expected, actual):
    expected = {tuple(x) for x in expected}
    return {'exact_match': expected == actual, 'tp': len(expected & actual),
            'fp': len(actual - expected), 'fn': len(expected - actual),
            'unexpected': sorted(actual - expected), 'missed': sorted(expected - actual)}


def run_case(case, mode):
    enterprise = case_snapshot(case)
    snapshot_hash = hashlib.sha256(json.dumps(enterprise, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    started = time.perf_counter()
    result = {'case_id': case['id'], 'mode': mode, 'snapshot_hash': snapshot_hash,
              'success': False, 'tool_calls': 0, 'model_calls': 0}
    actions = []
    try:
        if mode == 'rules':
            controls = evaluate_enterprise(enterprise)
        else:
            # Isolate every trial so task history cannot leak across cases/modes.
            with tempfile.TemporaryDirectory() as directory:
                report, error = None, None
                for event in agent_events('Kiểm tra bằng chứng và đề xuất xử lý cho HiveFive.', mode,
                                          AgentStore(directory), snapshot=(enterprise, 'RESEARCH', snapshot_hash)):
                    if event['type'] == 'action':
                        actions.append(event)
                    elif event['type'] == 'complete':
                        report = event['report']
                    elif event['type'] == 'error':
                        error = event['message']
                        result['model_calls'] = event.get('metrics', {}).get('model_calls', 0)
                if report is None:
                    raise RuntimeError(error or 'Không có báo cáo hoàn tất')
                controls = report['people_controls']
                result['metrics'] = report['metrics']
        actual = predictions(controls)
        result.update(score(case['expected'], actual), actual=sorted(actual), success=True)
        if mode != 'rules':
            selected = {a['tool'] for a in actions}
            result['required_tools_found'] = set(case.get('required_tools', [])) <= selected
            result['all_choices_valid'] = all(a['tool'] in a['available_tools'] for a in actions)
    except Exception as exc:
        result.update(error=str(exc), exact_match=False)
    result.update(elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
                  tool_calls=len(actions), model_calls=max(result['model_calls'], len(actions)) if mode == 'ai' else 0,
                  decisions=actions)
    return result


def summarize(rows):
    tp = sum(r.get('tp', 0) for r in rows)
    fp = sum(r.get('fp', 0) for r in rows)
    fn = sum(r.get('fn', 0) for r in rows)
    return {'trials': len(rows), 'completed': sum(r['success'] for r in rows),
            'exact_matches': sum(r['exact_match'] for r in rows),
            'precision_completed': tp / (tp + fp) if tp + fp else None,
            'recall_completed': tp / (tp + fn) if tp + fn else None,
            'mean_ms': round(sum(r['elapsed_ms'] for r in rows) / len(rows), 2) if rows else None,
            'median_ms': round(statistics.median(r['elapsed_ms'] for r in rows), 2) if rows else None,
            'stdev_ms': round(statistics.stdev(r['elapsed_ms'] for r in rows), 2) if len(rows) > 1 else None,
            'required_plan_complete': sum(r.get('required_tools_found', False) for r in rows),
            'valid_choices_trials': sum(r.get('all_choices_valid', False) for r in rows),
            'tool_calls': sum(r['tool_calls'] for r in rows), 'model_calls': sum(r['model_calls'] for r in rows)}


def paired_analysis(rows, repeats):
    ids = sorted({r['case_id'] for r in rows})
    by_case = {cid: {mode: summarize([r for r in rows if r['case_id'] == cid and r['mode'] == mode])
                     for mode in ('rules', 'workflow', 'ai')} for cid in ids}
    return {'same_snapshots': all(len({r['snapshot_hash'] for r in rows if r['case_id'] == cid}) == 1 for cid in ids),
            'balanced_trials': all(by_case[cid][mode]['trials'] == repeats for cid in ids for mode in ('rules', 'workflow', 'ai')),
            'by_case': by_case}


def run_study(ai_ids=(), paired=False, repeats=1, progress=False):
    cases = benchmark_cases() + advanced_cases()
    if paired:
        cases = [c for c in cases if c['id'] in ai_ids]
    rows = []
    for repeat in range(repeats):
        # Rotate mode order across repetitions to reduce consistent warmup/order bias.
        modes = ['rules', 'workflow', 'ai']
        modes = modes[repeat % 3:] + modes[:repeat % 3]
        for case in cases:
            for mode in modes:
                if mode == 'ai' and case['id'] not in ai_ids:
                    continue
                row = run_case(case, mode)
                row['repeat'] = repeat + 1
                rows.append(row)
                if progress:
                    print(f"repeat={repeat+1} mode={mode} case={case['id']} success={row['success']} exact={row['exact_match']}", flush=True)
    return {'generated_at': datetime.now(timezone.utc).isoformat(), 'case_count': len(cases),
            'paired': paired, 'repeats': repeats,
            'source_sha256': {name: hashlib.sha256((ROOT / 'agent_core' / name).read_bytes()).hexdigest()
                              for name in ('research_benchmark.py', 'simulation.py', 'autonomous.py', 'evidence_context.py')},
            'paired_analysis': paired_analysis(rows, repeats) if paired else None,
            'dataset_sha256': hashlib.sha256(json.dumps(cases, sort_keys=True).encode()).hexdigest(),
            'cases': cases, 'trials': rows,
            'summary': {mode: summarize([r for r in rows if r['mode'] == mode]) for mode in ('rules', 'workflow', 'ai')},
            'limitations': ['Bộ ca tổng hợp tự xây dựng, chưa đánh giá mù bởi chuyên gia độc lập.',
                           'Ba chế độ dùng chung evaluator: accuracy không chứng minh LLM tốt hơn luật.',
                           'So sánh ghép cặp dùng cùng case_id và snapshot ở ba chế độ; các tập khác nhau không được so trung bình.',
                           'Precision/recall chỉ tính lần chạy hoàn tất; lỗi được báo riêng và exact-match tính lỗi là thất bại.',
                           'Chưa đo token/chi phí, tải đồng thời hoặc khả năng khái quát trên doanh nghiệp thật.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ai', action='store_true', help='Chạy Ollama thật trên 3 ca đại diện')
    parser.add_argument('--paired', action='store_true', help='So sánh cả 3 chế độ trên cùng 8 ca')
    parser.add_argument('--repeats', type=int, default=1)
    parser.add_argument('--output', type=Path, default=ROOT / 'docs' / 'research-results.json')
    args = parser.parse_args()
    if not 1 <= args.repeats <= 10:
        parser.error('--repeats phải từ 1 đến 10')
    ids = ('offboarding-open-assets', 'A.6.3-unknown', 'training-expired', 'training-source-conflict',
           'role-review-pending', 'role-review-complete', 'retention-approved', 'retention-expired') if args.paired else (
           ('offboarding-open-assets', 'A.6.3-unknown', 'offboarding-repaired') if args.ai else ())
    study = run_study(ids, paired=args.paired, repeats=args.repeats, progress=True)
    args.output.write_text(json.dumps(study, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(study['summary'], ensure_ascii=False, indent=2))
