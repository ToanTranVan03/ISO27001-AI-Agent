"""Full 56-control project scope, keeping experiment evidence separate from formal conclusions."""
from collections import Counter
import json
from pathlib import Path
from agent_core.a8_assessment import catalog as a8_catalog, digest

CATALOG=Path(__file__).resolve().parents[1]/'docs'/'56_controls_scope.json'


def build_scope(assessment_id,dossier,studies=None,decisions=None,reviews=None,approvals=None,rubric_approvals=None):
    controls=json.loads(CATALOG.read_text(encoding='utf-8'))
    rubric_file=CATALOG.parent/'compliance_rubrics.json'
    rubric_hash=digest({'controls':controls,'rubrics':json.loads(rubric_file.read_text(encoding='utf-8'))})
    rubric_approval=next((r for r in reversed(rubric_approvals or []) if r['rubric_sha256']==rubric_hash),None)
    priority={c['control_id'] for c in a8_catalog()}
    actual={c['control_id']:c for c in dossier['controls']}
    decisions=decisions or {}
    reviews=reviews or {}
    records=[]
    for c in controls:
        cid=c['control_id'];current=actual.get(cid,{})
        decision=decisions.get(cid)
        group=cid.split('.')[1]
        row=dict(**c,pillar={'6':'Con người','7':'Phần cứng / vật lý','8':'Phần mềm / kỹ thuật'}[group],
            priority_a8=cid in priority,collector_supported=bool(current.get('collector_supported')),
            support_stage='partial_lab' if cid in priority or current.get('collector_supported') else 'document_workflow',
            development_note='Có kiểm tra lab đại diện; chưa bao phủ đầy đủ nội dung control.' if cid in priority or current.get('collector_supported') else 'Có connector thu gói tài liệu/cấu hình/log và luồng thẩm định; chưa có probe tự động chuyên biệt.',
            conclusion=current.get('conclusion','Chưa đánh giá'),assessment_state=current.get('assessment_state','not_evaluated'),
            workflow_status=current.get('workflow_status','NOT_STARTED'),assigned_to=current.get('assigned_to'),
            evidence=current.get('evidence',[]),history=current.get('evaluation_history',[]),
            latest_evaluation_id=current.get('latest_evaluation_id'),
            experiment_results=(studies or {}).get(cid,[]),applicability=decision)
        row['evidence_package_supported']=True
        row['review_token']=digest({'control_id':cid,'latest_evaluation_id':row['latest_evaluation_id'],
            'assessment_state':row['assessment_state'],'rubric_sha256':rubric_hash,'snapshot':dossier.get('company_snapshot_hash'),
            'evidence':sorted((e['evidence_id'],e['sha256_hash']) for e in row['evidence'])})
        review=reviews.get(cid)
        row['human_review']=review
        row['human_review_current']=bool(review and review['review_token']==row['review_token'] and row['workflow_status']!='RUNNING')
        records.append(row)
    soa=dict(title='SoA dự thảo — toàn bộ phạm vi 56 control của đồ án',approval='DRAFT_NOT_APPROVED',
        scope='8 control A.6, 14 control A.7, 34 control A.8; không đồng nghĩa toàn bộ Annex A/ISMS.',
        entries=[dict(control_id=r['control_id'],name=r['name'],pillar=r['pillar'],
            applicable=r['applicability']['applicable'] if r['applicability'] else None,
            applicability_reason=r['applicability']['reason'] if r['applicability'] else 'Chờ người phụ trách xác định; không tự loại trừ control chưa triển khai.',
            applicability_recorded_by=r['applicability'].get('recorded_by') if r['applicability'] else None,
            implementation_status=r['human_review']['conclusion'] if r['human_review_current'] else r['conclusion'],
            machine_conclusion=r['conclusion'],human_review_current=r['human_review_current'],
            human_review=r['human_review'],evidence_ids=[e['evidence_id'] for e in r['evidence']],
            evidence_hashes=[e['sha256_hash'] for e in r['evidence']],assessment_state=r['assessment_state'],
            treatment=r['applicability']['treatment'] if r['applicability'] else 'Chờ xác định kế hoạch xử lý/thu thập bằng chứng.',
            priority_experiment=r['priority_a8'],experiment_is_formal_conclusion=False,
            note='Kết quả ca thử A.8 không tự thay thế đánh giá toàn đợt; chưa tự phê duyệt.') for r in records])
    fingerprint=digest([{'control_id':r['control_id'],'review_token':r['review_token'],
       'applicability':r['applicability'],'human_review':r['human_review']} for r in records])
    approved=next((a for a in reversed(approvals or []) if a['fingerprint']==fingerprint),None)
    pending=[r['control_id'] for r in records if r['applicability'] is None or
             (r['applicability']['applicable'] and not r['human_review_current']) or r['workflow_status']=='RUNNING']
    soa.update(fingerprint=fingerprint,approval='HUMAN_APPROVED_PROJECT_SCOPE' if approved and rubric_approval and not pending else 'DRAFT_NOT_APPROVED',
               human_approval=approved if rubric_approval and not pending else None,pending_controls=pending,approval_ready=not pending and bool(rubric_approval),
               pending_rubric_approval=not bool(rubric_approval),
               approval_note='Chỉ phê duyệt phạm vi 56 control của đồ án; không chứng nhận toàn ISMS.')
    result=dict(assessment_id=str(assessment_id),scope_total=len(records),priority_count=len(priority),rubric_sha256=rubric_hash,rubric_approval=rubric_approval,
        pillars=dict(Counter(r['pillar'] for r in records)),support_summary=dict(Counter(r['support_stage'] for r in records)),
        conclusion_summary=dict(Counter(r['conclusion'] for r in records)),controls=records,soa=soa)
    result['sha256']=digest(result)
    return result
