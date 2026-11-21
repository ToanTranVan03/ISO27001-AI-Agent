"""One schema-constrained retry of technical errors; retain every first response."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from dotenv import load_dotenv
from agent_core.development_lab import build_bundle,evaluate,compare_designer


def retry(path):
    path=Path(path).resolve()
    if not path.is_relative_to(ROOT/'work/development-lab'):raise ValueError('Only a separate development-lab report may be retried')
    doc=json.loads(path.read_text(encoding='utf-8'));bundle=build_bundle()
    if doc['state']!='COMPLETED' or doc['bundle_sha256']!=bundle['sha256']:raise ValueError('Unfinished or changed source bundle')
    if 'repair_attempts' in doc:raise ValueError('One retry only; history already exists')
    cases={c['control_id']:c for c in bundle['cases']}
    repairs=[]
    for result in doc['results']:
        if result['error']:
            repairs.append(evaluate(cases[result['control_id']],doc['model']))
            print(json.dumps({'control_id':result['control_id'],'retry_error':repairs[-1]['error']},ensure_ascii=True),flush=True)
    updates={r['control_id']:r for r in repairs}
    doc.update(repair_protocol='schema-constrained-json-v1',repair_at=datetime.now(timezone.utc).isoformat(),repair_attempts=repairs,
        final_results=[updates.get(r['control_id'],r) for r in doc['results']])
    doc['designer_comparison_after_retry']=compare_designer(doc['final_results'],doc.get('designer_reference_snapshot'))
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding='utf-8');temporary.replace(path)
    return doc


if __name__=='__main__':
    load_dotenv(ROOT/'.env')
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report',required=True)
    args=parser.parse_args();result=retry(args.report)
    print(json.dumps({'retried':len(result['repair_attempts']),'final_errors':sum(bool(r['error']) for r in result['final_results'])}))
