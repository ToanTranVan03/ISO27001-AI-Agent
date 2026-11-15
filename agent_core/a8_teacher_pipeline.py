"""Integrated branch exporter: designer benchmarks and human reviews stay separate."""
import csv
import json
from pathlib import Path
from agent_core.a8_assessment import ROOT, LAB, digest, soa
from agent_core.a8_benchmark import score
from agent_core.a8_review_analysis import analyze_reviews


def load_reports(paths):
    reports=[]
    for path in paths:
        doc=json.loads(Path(path).read_text(encoding='utf-8-sig'))
        items=doc.get('reports') or [doc.get('report',doc)]
        for report in items:
            if digest({k:v for k,v in report.items() if k!='sha256'})!=report.get('sha256'):
                raise ValueError('Report hash mismatch')
            if not report.get('records'):raise ValueError('Empty report')
            reports.append(report)
    if len({r['sha256'] for r in reports})!=len(reports):raise ValueError('Duplicate report input')
    return reports


def build_assessor_ground_truth(path):
    """Load actual exported labels; never manufacture names, declarations or answers."""
    labels=json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if not isinstance(labels,list):raise ValueError('Provide an exported list of reviewer labels')
    required={'reviewer_id','expected','case_id','control_id','report_sha256','evidence_sha256','reviewed_at','rationale'}
    for label in labels:
        if not required<=label.keys():raise ValueError('Review lacks identity/time/report/evidence provenance')
        if label.get('is_simulated') or not str(label.get('label_origin','')).startswith('human-submitted-'):
            raise ValueError('Only actual submitted review exports are accepted as human references')
        if not str(label['rationale']).strip():raise ValueError('Missing reviewer rationale')
    return labels


def evaluate_accuracy_against_assessors(reports,labels):
    report_hashes={r['sha256'] for r in reports}
    if any(l['report_sha256'] not in report_hashes for l in labels):raise ValueError('Labels refer to another report')
    results=[]
    for report in reports:
        bound=[l for l in labels if l['report_sha256']==report['sha256']]
        analysis=analyze_reviews(report,bound,'EXPORT_COORDINATOR_NOT_A_REVIEWER')
        if analysis['rejected_labels']:raise ValueError('Review case/evidence binding invalid')
        results.append(dict(report_sha256=report['sha256'],analysis=analysis,
            note='Each reviewer remains separate. Declaration is not proof of expertise or external independence.'))
    return results


def generate_automated_soa(report):
    result=soa(report)
    result['approval']='DRAFT_NOT_APPROVED'
    suggestions=json.loads((ROOT/'docs/a8_remediation_templates.json').read_text(encoding='utf-8'))
    for entry in result['entries']:
        entry['remediation_suggestion']=suggestions.get(entry['control_id'])
        entry['suggestion_note']='Draft technical option from branch Tuan5, not an ISO mandate, completed action or owner approval.'
        entry['applicable']=None
        entry['applicability_approved']=False
        entry['inclusion_reason']='Pending owner applicability decision; lab scope alone does not approve applicability.'
    return result


def export_all_deliverables(reports,output_dir,labels=None):
    # Compare only replay records against known designer keys; live remains unrated.
    designer=json.loads((LAB/'reference/designer_labels.json').read_text(encoding='utf-8'))
    human=evaluate_accuracy_against_assessors(reports,labels or [])
    payload=dict(protocol='integrated-branches-export-v1',
        input_report_hashes=[r['sha256'] for r in reports],
        source='EXISTING_REPORT_EXPORT_NOT_NEW_INFERENCE',
        designer_comparisons=[dict(report_sha256=r['sha256'],mode=r['mode'],transport=r.get('transport','UNKNOWN_LEGACY'),
            rubric_version=r.get('rubric_version'),comparison=score([r],designer if r.get('transport') in ('files','docker') and
                not any(e['evidence'].get('source_kind')=='external-lab-candidate-unverified' for e in r['records']) else [])) for r in reports],
        human_comparisons=human,soa_drafts=[generate_automated_soa(r) for r in reports],
        note='No pooled accuracy across different engines/rubrics. Missing human labels remain missing. Designer labels are not human judgments.')
    payload['sha256']=digest(payload)
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=False)
    (out/'evaluation.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (out/'per-control.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['report_sha256','mode','transport','control_id','total','rated_designer','correct_designer','designer_accuracy','errors'])
        for group in payload['designer_comparisons']:
            for row in group['comparison']['per_control']:
                w.writerow([group['report_sha256'],group['mode'],group['transport'],row['control_id'],row['total'],row['rated'],row['correct'],row['accuracy'],row['errors']])
    lines=['# Export đánh giá A.8 sau tích hợp hai nhánh','',payload['note'],'',
        'Nguồn là báo cáo đã lưu; không phải lần chạy LLM mới. SoA luôn là dự thảo, chưa có quyết định áp dụng được duyệt.',
        '', '| Report | Engine | Nguồn | Control | Có nhãn thiết kế | Khớp thiết kế | Lỗi |','|---|---|---|---|---|---|---|']
    for group in payload['designer_comparisons']:
        for row in group['comparison']['per_control']:
            lines.append(f"| {group['report_sha256'][:12]} | {group['mode']} | {group['transport']} | {row['control_id']} | {row['rated']} | {row['correct']} | {row['errors']} |")
    lines+=['','Đối chiếu người thật: xem từng người theo report/evidence hash trong JSON. Nhãn trống không được thay bằng kết luận Agent.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return payload
