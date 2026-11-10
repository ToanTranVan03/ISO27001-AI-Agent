"""Scoring is separate from the evidence-only assessor; missing reviews never count as agreement."""
import argparse
import csv
import json
from pathlib import Path
from agent_core.a8_assessment import LAB, PROFILES, STATUSES, run, soa, digest


def score(reports, labels):
    refs={r['case_id']:r for r in labels}
    rows=[]
    for report in reports:
        for r in report['records']:
            reference=refs.get(r['case_id'])
            rows.append(dict(control_id=r['control_id'],case_id=r['case_id'],prediction=r['status'],
                expected=reference['expected'] if reference else None,
                label_origin=reference.get('label_origin') if reference else None,
                correct=(r['status']==reference['expected']) if reference else None,
                error=r['error'],collection_issue_count=len(r.get('evidence',{}).get('collection_errors',[])),duration_ms=r['duration_ms']))
    per=[]
    for cid in dict.fromkeys(r['control_id'] for r in rows):
        subset=[r for r in rows if r['control_id']==cid];rated=[r for r in subset if r['expected'] is not None]
        class_metrics={}
        for label in STATUSES:
            tp=sum(r['expected']==label and r['prediction']==label for r in rated)
            fp=sum(r['expected']!=label and r['prediction']==label for r in rated)
            fn=sum(r['expected']==label and r['prediction']!=label for r in rated)
            precision=tp/(tp+fp) if tp+fp else None
            recall=tp/(tp+fn) if tp+fn else None
            f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None
            class_metrics[label]=dict(precision=precision,recall=recall,f1=f1,support=tp+fn)
        per.append(dict(control_id=cid,total=len(subset),rated=len(rated),class_metrics=class_metrics,
            mean_duration_ms=sum(r['duration_ms'] for r in subset)/len(subset),
            errors=sum(r['error'] is not None for r in subset),collection_issues=sum(r['collection_issue_count'] for r in subset),correct=sum(r['correct'] is True for r in rated),
            accuracy=sum(r['correct'] is True for r in rated)/len(rated) if rated else None,
            confusion={a:{b:sum(r['expected']==a and (r['prediction'] or 'ERROR')==b for r in rated) for b in (*STATUSES,'ERROR')} for a in STATUSES}))
    return dict(per_control=per,cases=rows,reference_kind=sorted({r.get('label_origin','unknown') for r in labels}),
                note='Nhãn designer không phải kết quả người đánh giá độc lập. Lỗi engine tính là không khớp, không loại khỏi mẫu có nhãn.')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--mode',choices=['rules','llm'],default='rules')
    parser.add_argument('--output',required=True)
    parser.add_argument('--transport',choices=['files','docker'],default='files')
    parser.add_argument('--repeats',type=int,default=1)
    parser.add_argument('--profiles',nargs='+',choices=PROFILES,default=list(PROFILES))
    args=parser.parse_args()
    from dotenv import load_dotenv
    load_dotenv()
    if not 1<=args.repeats<=10:parser.error('repeats must be 1..10')
    labels=json.loads((LAB/'reference'/'designer_labels.json').read_text(encoding='utf-8'))
    reports=[]
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    for repeat in range(args.repeats):
        for profile in args.profiles:
            reports.append(run(profile,args.mode,args.transport))
            checkpoint=output.with_name(output.stem+'-checkpoint.json')
            checkpoint.write_text(json.dumps({'state':'partial','reports':reports,'completed_profile_runs':len(reports),'planned_profile_runs':args.repeats*len(args.profiles)},ensure_ascii=False,indent=2),encoding='utf-8')
            print(f'completed repeat={repeat+1} profile={profile}',flush=True)
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    payload=dict(reference_sha256=digest(labels),reference_snapshot=labels,mode=args.mode,transport=args.transport,repeats=args.repeats,profiles=args.profiles,reports=reports,designer_comparison=score(reports,labels),
                 human_comparison=score(reports,[]))
    output.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    output.with_name(output.stem+'-soa.json').write_text(json.dumps(soa(reports[min(1,len(reports)-1)]),ensure_ascii=False,indent=2),encoding='utf-8')
    with output.with_suffix('.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['control_id','total','rated','errors','correct','accuracy'])
        writer.writeheader()
        for row in payload['designer_comparison']['per_control']:
            writer.writerow({k:row[k] for k in writer.fieldnames})
    output.with_name(output.stem+'-checkpoint.json').unlink(missing_ok=True)
    print(json.dumps(dict(mode=args.mode,cases=sum(len(r['records']) for r in reports),errors=sum(bool(x['error']) for r in reports for x in r['records']))))


if __name__=='__main__':main()
