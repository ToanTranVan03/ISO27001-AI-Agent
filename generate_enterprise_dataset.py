"""Generate bounded, deterministic DEVELOPMENT fixtures; never touch the audit DB."""
import argparse
import calendar
import csv
import hashlib
import json
import random
from datetime import date,timedelta
from pathlib import Path

PROTOCOL='synthetic-enterprise-development-v1'
GENERATED_ROOT=Path(__file__).resolve().parent/'work'


def month_at(start,offset):
    year=start.year+(start.month-1+offset)//12;month=(start.month-1+offset)%12+1
    return date(year,month,min(start.day,calendar.monthrange(year,month)[1]))


def generate(root,sizes=(30,100,500),months=12,seed=27001,start='2024-01-01'):
    if not 1<=len(sizes)<=10 or any(not 1<=n<=5000 for n in sizes) or not 1<=months<=60:
        raise ValueError('1–10 enterprises, 1–5000 people each, 1–60 months')
    if sum(sizes)*months>300000:raise ValueError('Dataset exceeds 300000 person-period rows')
    root=Path(root)
    if root.exists():raise ValueError('Output exists; preserve prior data and choose a new directory')
    beginning=date.fromisoformat(start);rng=random.Random(seed);root.mkdir(parents=True)
    manifest=dict(protocol=PROTOCOL,synthetic=True,training_allowed=False,independent_validation=False,seed=seed,start=start,months=months,enterprises=[],files=[])
    def write(relative,rows):
        path=root/relative;path.parent.mkdir(parents=True,exist_ok=True)
        if path.suffix=='.csv':
            with path.open('w',encoding='utf-8',newline='') as out:
                writer=csv.DictWriter(out,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        else:path.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
        manifest['files'].append(dict(path=relative,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size))
    for index,size in enumerate(sizes,1):
        eid=f'SYNTH-{index:03d}';departments=max(3,min(20,(size+16)//17));entry=dict(enterprise_id=eid,employees=size,departments=departments,periods=[])
        write(f'{eid}/profile.json',dict(enterprise_id=eid,synthetic=True,name='SYNTHETIC enterprise '+str(index),employee_count=size,department_count=departments,source='Generated development data; no real signatures or expert labels'))
        for m in range(months):
            observed=month_at(beginning,m);period=observed.strftime('%Y-%m');base=f'{eid}/{period}';people=[];accounts=[];assets=[];screening=[];truth=[]
            for n in range(1,size+1):
                pid=f'EMP-{n:03d}';department=f'DEP-{n%departments+1:02d}'
                terminated=m>=2 and n%11==0;active=not terminated or n%2==0
                scenario=('missing','compliant','noncompliant','partial','stale','conflict')[n%6]
                # A deterministic recovery in later periods preserves earlier files.
                if m>=5 and terminated and n%2==0:active=False
                people.append(dict(enterprise_id=eid,period=period,employee_id=pid,name=f'SYNTHETIC person {n}',department=department,status='terminated' if terminated else 'active',synthetic=True))
                accounts.append(dict(enterprise_id=eid,period=period,account_id=pid+'-EMAIL',employee_id=pid,active=active,synthetic=True))
                assets.append(dict(enterprise_id=eid,period=period,asset_id='DEVICE-'+str(n),employee_id=pid,department=department,asset_type='hardware',encrypted=None if scenario=='missing' else scenario!='noncompliant',synthetic=True))
                truth.append(dict(employee_id=pid,account_not_revoked_after_termination=terminated and active,scenario=scenario,reference_type='generator_design_key_NOT_EXPERT_LABEL'))
                if scenario!='missing':screening.append(dict(enterprise_id=eid,period=period,employee_id=pid,screening_completed=scenario not in ('noncompliant','partial'),observed_at=(observed-timedelta(days=400) if scenario=='stale' else observed).isoformat(),reviewer_record='Not a real signature; synthetic test',synthetic=True))
            write(base+'/people.csv',people);write(base+'/accounts.csv',accounts);write(base+'/assets.csv',assets)
            if screening:write(base+'/screening.csv',screening)
            write(base+'/design-key.json',truth)
            write(base+'/backup-observations.json',dict(enterprise_id=eid,period=period,synthetic=True,backup_completed=True,restore_test_passed=m>=5,observed_at=observed.isoformat(),scope='One generated backup service, not the full ISO control',scenario='partial' if m<5 else 'compliant'))
            write(base+'/conflicting-observations.json',dict(enterprise_id=eid,period=period,synthetic=True,observations=[dict(source='generated-inventory',encrypted=True),dict(source='generated-inspection',encrypted=False)],requires_human_resolution=True))
            entry['periods'].append(dict(period=period,directory=base,observed_at=observed.isoformat()))
        entry['sample_token']=rng.getrandbits(32);manifest['enterprises'].append(entry)
    (root/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    return manifest


def validate(root):
    root=Path(root).resolve();manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('protocol')!=PROTOCOL or manifest.get('synthetic') is not True:raise ValueError('Not a generated development dataset')
    errors=[]
    for item in manifest['files']:
        path=(root/item['path']).resolve()
        if not path.is_relative_to(root) or not path.is_file():errors.append(item['path']+': missing/unsafe');continue
        if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:errors.append(item['path']+': hash mismatch')
    return dict(protocol=PROTOCOL,synthetic=True,files=len(manifest['files']),errors=errors,passed=not errors)


def remove_dataset(root):
    """Only an intact generated folder inside work; never recurse through extra files."""
    root=Path(root).absolute();allowed=GENERATED_ROOT.resolve()
    resolved=root.resolve()
    if resolved==allowed or not resolved.is_relative_to(allowed) or root.is_symlink():raise ValueError('Removal is limited to a generated subdirectory inside work/')
    manifest_path=resolved/'manifest.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    checked=validate(resolved)
    if not checked['passed']:raise ValueError('Changed/missing data; refuse automatic removal')
    expected={resolved/item['path'] for item in manifest['files']}|{manifest_path}
    actual=list(resolved.rglob('*'))
    if any(p.is_symlink() for p in actual) or {p for p in actual if p.is_file()}!=expected:raise ValueError('Unexpected files or links; refuse removal')
    for path in expected:path.unlink()
    for path in sorted((p for p in actual if p.is_dir()),key=lambda p:len(p.parts),reverse=True):path.rmdir()
    resolved.rmdir()
    return dict(removed=True,synthetic=True,files=len(expected),database_affected=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['generate','validate','remove']);parser.add_argument('--output',required=True)
    parser.add_argument('--sizes',default='30,100,500');parser.add_argument('--months',type=int,default=12);parser.add_argument('--seed',type=int,default=27001);parser.add_argument('--start',default='2024-01-01')
    args=parser.parse_args()
    if args.command=='generate':
        doc=generate(args.output,tuple(int(n) for n in args.sizes.split(',')),args.months,args.seed,args.start)
        print(json.dumps(dict(files=len(doc['files']),synthetic=True,independent_validation=False)))
    elif args.command=='remove':print(json.dumps(remove_dataset(args.output)))
    else:
        result=validate(args.output);print(json.dumps(result));raise SystemExit(0 if result['passed'] else 1)


if __name__=='__main__':main()
