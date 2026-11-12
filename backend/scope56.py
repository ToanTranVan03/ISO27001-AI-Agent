"""Full 56-control project scope, keeping experiment evidence separate from formal conclusions."""
from collections import Counter
import json
from pathlib import Path
from agent_core.a8_assessment import catalog as a8_catalog, digest
from backend.review_criteria import current as criteria_review_current

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
        row['explicit_source_count']=sum(e.get('is_synthetic') is False or e.get('source','').startswith('a8-capture://') for e in row['evidence'])
        row['review_token']=digest({'control_id':cid,'latest_evaluation_id':row['latest_evaluation_id'],
            'assessment_state':row['assessment_state'],'rubric_sha256':rubric_hash,'snapshot':dossier.get('company_snapshot_hash'),
            'evidence':sorted((e['evidence_id'],e['sha256_hash']) for e in row['evidence'])})
        review=reviews.get(cid)
        row['human_review']=review
        row['human_review_current']=bool(review and review['review_token']==row['review_token'] and row['workflow_status']!='RUNNING'
                                         and criteria_review_current(review,c['pass_criteria']))
        row['criteria_review_required']=c['pass_criteria']
        # Actionable progress; development coverage is not evidence of compliance.
        if row['workflow_status']=='RUNNING':
            action='Theo dõi Agent đang xử lý'
        elif decision is None:
            action='Người phụ trách xác định tính áp dụng và kế hoạch'
        elif not decision['applicable']:
            action='Lưu căn cứ loại trừ để người phụ trách duyệt SoA'
        elif not row['explicit_source_count']:
            action='Thu hồ sơ hoặc bằng chứng cho control'
        elif row['latest_evaluation_id'] is None:
            action='Chạy Agent đánh giá nguồn đã thu'
        elif not row['human_review_current']:
            action='Người đánh giá thẩm định kết luận và bằng chứng hiện hành'
        else:
            action='Rà kế hoạch xử lý và trình duyệt SoA'
        row['next_action']=action
        row['evidence_types_present']=sorted({e.get('evidence_type') for e in row['evidence'] if e.get('evidence_type')})
        row['evidence_types_to_check']=[t for t in row['expected_evidence_types'] if t not in row['evidence_types_present']]
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
            treatment_owner=r['applicability'].get('treatment_owner') if r['applicability'] else None,
            treatment_due=r['applicability'].get('treatment_due') if r['applicability'] else None,
            verification_plan=r['applicability'].get('verification_plan') if r['applicability'] else None,
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
    result['acceptance']=dict(
        total_controls=len(records),rubric_approved=bool(rubric_approval),
        applicability_recorded=sum(r['applicability'] is not None for r in records),
        controls_with_evidence=sum(bool(r['evidence']) for r in records),
        controls_with_submitted_sources=sum(any(e.get('is_synthetic') is False for e in r['evidence']) for r in records),
        controls_with_captured_lab_sources=sum(any(e.get('source','').startswith('a8-capture://') for e in r['evidence']) for r in records),
        controls_with_explicit_sources=sum(r['explicit_source_count']>0 for r in records),
        controls_with_current_human_review=sum(r['human_review_current'] for r in records),
        soa_approved=soa['approval']=='HUMAN_APPROVED_PROJECT_SCOPE',
        note='Nguồn nộp không tự đồng nghĩa đã xác thực. Số control có bằng chứng/thẩm định không phải số control đạt ISO.')
    from backend.acceptance_worklist import build_worklist
    result['acceptance_worklist']=build_worklist(result)
    from backend.acceptance_packet import build_packet
    result['handoff_packet']=build_packet(result)
    result['sha256']=digest(result)
    return result
