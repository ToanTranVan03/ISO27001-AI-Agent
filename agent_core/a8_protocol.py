"""Pre-register and seal an A.8 observation pack before running the model.

This makes experiments reproducible; it does not turn known fixtures into held-out
data, verify provenance, or substitute for an independent human evaluator.
"""
import argparse
import json
import os
import hashlib
import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from agent_core import a8_assessment as a8


def recipe():
    return dict(model=os.getenv('OLLAMA_MODEL','qwen2.5:7b'),
                implementation_sha256=a8.implementation_hash(),
                max_model_attempts=2,temperature=0,num_predict=400,num_ctx=4096)


def payload_fingerprint(evidence):
    # A new capture date or asset label does not make a known fixture held-out.
    return a8.digest({'control_id':evidence['control_id'],'sources':sorted(
        (a['artifact'],a['sha256']) for a in evidence['artifacts']
        if a['artifact'] not in ('capture.json','secondary-capture.sha256'))})


def external_capture(profile,root):
    root=Path(root).resolve()
    if not root.is_dir():raise ValueError('External raw dataset directory does not exist')
    if root== (a8.LAB/'raw').resolve():raise ValueError('Use the normal regression source for built-in fixtures')
    # An isolated module instance avoids changing the collector ROOT used by
    # concurrent API jobs. Only trusted project code is loaded, never dataset code.
    spec=importlib.util.spec_from_file_location('_a8_external_collector',a8.ROOT/'evidence_collectors'/'a8_raw.py')
    collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)
    collector.ROOT=root
    controls=a8.catalog()
    evidence=[collector.collect_raw(profile,c) for c in controls]
    if any(not any(a['artifact']!='capture.json' for a in e['artifacts']) for e in evidence):
        raise ValueError('Provide original sources for all 18 controls; empty folders are not a validation set')
    known={payload_fingerprint(a8.collect(p,c)) for p in a8.PROFILES for c in controls}
    overlaps=[e['control_id'] for e in evidence if payload_fingerprint(e) in known]
    for e in evidence:
        e.update(source_kind='external-lab-candidate-unverified',source='external-lab://'+e['control_id'])
    snapshot=dict(profile=profile,transport='files',captured_at=datetime.now(timezone.utc).isoformat(),catalog=controls,evidence=evidence)
    snapshot['sha256']=a8.digest(snapshot)
    return snapshot,overlaps


def prepare(profile,transport,coordinator,objective,raw_root=None):
    overlaps=[]
    if raw_root:
        if transport!='files':raise ValueError('External dataset input requires files transport')
        snapshot,overlaps=external_capture(profile,raw_root)
    else:snapshot=a8.capture(profile,transport)
    plan=dict(protocol_version='sealed-observations-v1',registered_at=datetime.now(timezone.utc).isoformat(),
              coordinator=coordinator,objective=objective,recipe=recipe(),snapshot=snapshot,
              dataset_usage='live-pilot-not-independent-validation' if transport=='live' else 'known-fixture-regression',
              independent_validation=False,human_approval='PENDING',
              reporting_requirements=['first-pass and final accuracy separately','engine errors in denominator',
                                      'per-control results','independent human labels bound to report/evidence hash'])
    if raw_root:
        plan.update(dataset_usage='external-candidate-pending-independent-review',
                    known_fixture_overlap_controls=overlaps,
                    independence_note='Overlap scan is not proof of independence. A person must confirm source, exposure and split before any held-out claim.')
    plan['sha256']=a8.digest(plan)
    return plan


def execute(plan,mode):
    if plan.get('sha256')!=a8.digest({k:v for k,v in plan.items() if k!='sha256'}):
        raise ValueError('Plan was modified after registration')
    if plan['recipe']!=recipe():
        raise ValueError('Implementation/model changed; register a new plan')
    snap=plan['snapshot']
    result=a8.run(snap['profile'],mode,snap['transport'],snapshot=snap)
    return dict(protocol_sha256=plan['sha256'],registered_at=plan['registered_at'],
                dataset_usage=plan['dataset_usage'],independent_validation=False,report=result)


def main():
    from dotenv import load_dotenv
    load_dotenv(a8.ROOT/'.env')
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    prep=commands.add_parser('prepare')
    prep.add_argument('--profile',choices=a8.PROFILES,default='mixed')
    prep.add_argument('--transport',choices=['files','docker','live'],default='files')
    prep.add_argument('--coordinator',required=True)
    prep.add_argument('--objective',required=True)
    prep.add_argument('--output',required=True)
    prep.add_argument('--raw-root',help='Separate lab source directory using profile/control/artifact layout; never model labels')
    execute_parser=commands.add_parser('execute')
    execute_parser.add_argument('--plan',required=True)
    execute_parser.add_argument('--mode',choices=['rules','llm'],required=True)
    execute_parser.add_argument('--output',required=True)
    args=parser.parse_args()
    output=Path(args.output)
    if output.exists():parser.error('Output exists; choose a new path to preserve the original')
    if args.command=='prepare':
        payload=prepare(args.profile,args.transport,args.coordinator,args.objective,args.raw_root)
    else:
        plan=json.loads(Path(args.plan).read_text(encoding='utf-8'))
        payload=execute(plan,args.mode)
    output.parent.mkdir(parents=True,exist_ok=True)
    # Exclusive creation avoids overwriting another measurement.
    with output.open('x',encoding='utf-8') as stream:
        json.dump(payload,stream,ensure_ascii=False,indent=2)
    print(json.dumps({'output':str(output),'independent_validation':False}))


if __name__=='__main__':main()
