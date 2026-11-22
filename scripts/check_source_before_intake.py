"""Check a supplied file without storing originals, evidence or decisions."""
import argparse
import json
from pathlib import Path
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from evidence_collectors.source_intake import prepare
from evidence_collectors.control_packages import MAX_BYTES
from evidence_collectors.source_quality import text_quality


def check(path,assessment_id,control_id,evidence_type,origin,observed_at=None,note=''):
    path=Path(path)
    report=dict(protocol='source-intake-preflight-v1',checked_at=datetime.now(ZoneInfo('Asia/Bangkok')).isoformat(),
        control_id=control_id,filename=path.name,passed=False,issues=[],
        writes_evidence=False,provenance_verified=False,coverage_verified=False,
        note='Technical preflight only, not evidence intake, independent validation or ISO compliance.')
    try:
        if not path.is_file():raise ValueError('Không tìm thấy tệp nguồn.')
        with path.open('rb') as stream:raw=stream.read(MAX_BYTES+1)
        item=prepare(assessment_id,control_id,path.name,raw,evidence_type,origin,observed_at,note)
        payload=json.loads(item['extracted_text'])
        report.update(passed=True,original_sha256=item['sha256_hash'],
            proposed_evidence_id=item['evidence_id'],bytes=len(raw),
            content_quality=text_quality(payload['content']),
            warnings=['Cần đối chiếu nội dung với từng tiêu chí và xác nhận nguồn gốc.']+
                ([] if observed_at else ['Chưa có thời điểm quan sát nguồn.']))
    except (OSError,ValueError,TypeError) as exc:report['issues'].append(str(exc)[:500])
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('file','assessment-id','control-id','evidence-type','origin','output'):
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--observed-at');parser.add_argument('--note',default='')
    args=parser.parse_args()
    output=Path(args.output)
    if output.exists():parser.error('Output exists; preserve earlier reports')
    report=check(args.file,args.assessment_id,args.control_id,args.evidence_type,args.origin,args.observed_at,args.note)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as stream:json.dump(report,stream,ensure_ascii=False,indent=2)
    print(json.dumps({'passed':report['passed'],'issues':report['issues'],'output':str(output)},ensure_ascii=True))
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
