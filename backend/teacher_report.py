"""Evidence-bound progress report; no pooling across rubrics or invented human metrics."""
from collections import Counter
from agent_core.a8_assessment import digest
from agent_core.a8_review_analysis import analyze_reviews


def build_report(scope,runs,practice):
    experiments=[];rejected=[]
    for doc in sorted(runs,key=lambda d:d.get('created_at',''),reverse=True):
        report=doc.get('report')
        if doc.get('state')!='finished' or not report:continue
        if digest({k:v for k,v in report.items() if k!='sha256'})!=report.get('sha256'):
            rejected.append(dict(run_id=doc['run_id'],reason='report_hash_mismatch'));continue
        records=report['records']
        if not records or len({r['control_id'] for r in records})!=len(records):
            rejected.append(dict(run_id=doc['run_id'],reason='empty_or_duplicate_controls'));continue
        analysis=analyze_reviews(report,doc.get('reviews',[]),doc['created_by'])
        independent=analysis['complete_independent_reviewers']
        experiments.append(dict(run_id=doc['run_id'],created_at=doc['created_at'],
            mode=report.get('mode','UNKNOWN_LEGACY'),transport=report.get('transport','UNKNOWN_LEGACY'),rubric_version=report.get('rubric_version'),
            catalog_sha256=report.get('catalog_sha256'),report_sha256=report['sha256'],
            metadata_complete=all(report.get(k) for k in ('mode','transport','catalog_sha256','rubric_version')),
            control_count=len(records),capture_count=len({(r['control_id'],r['evidence']['source_sha256']) for r in records}),
            source_coverage=sum(r['evidence'].get('observation_available',bool(r['evidence'].get('artifacts'))) for r in records),
            final_errors=sum(bool(r.get('error')) for r in records),
            first_errors=sum(bool(r.get('attempts') and r['attempts'][0].get('error')) for r in records),
            repaired=sum(bool(r.get('repaired')) for r in records),
            human_progress=analysis['reviewer_progress'],
            complete_independently_declared_reviewers=independent,
            human_comparisons={uid:analysis['independent_reviewer_comparisons'][uid]['per_control'] for uid in independent},
            pending_human_comparison=not bool(independent),
            control_results=[dict(control_id=r['control_id'],machine_status=r['status'],error=r.get('error'),
                evidence_sha256=r['evidence']['source_sha256'],is_synthetic=r['evidence'].get('is_synthetic')) for r in records]))
    payload=dict(protocol='teacher-progress-v1',assessment_id=scope['assessment_id'],
        scope_total=scope['scope_total'],priority_count=scope['priority_count'],
        scope_sha256=scope['sha256'],rubric_sha256=scope['rubric_sha256'],
        soa_fingerprint=scope['soa']['fingerprint'],soa_approval=scope['soa']['approval'],
        acceptance=scope['acceptance'],formal_conclusions=dict(Counter(c['conclusion'] for c in scope['controls'])),
        controls=[dict(control_id=c['control_id'],name=c['name'],priority_a8=c['priority_a8'],
            explicit_source_count=c['explicit_source_count'],machine_conclusion=c['conclusion'],
            human_review_current=c['human_review_current'],next_action=c['next_action']) for c in scope['controls']],
        pending_tasks=scope['acceptance_worklist']['by_stage'],experiments=experiments,rejected_runs=rejected,
        practice_summary=practice,professional_acceptance='NOT_ASSERTED',
        methodological_limits=[
            '56 control là phạm vi đồ án, không phải toàn bộ Annex A/ISMS.',
            '18 probe A.8 là tiêu chí đại diện; có nguồn chưa chứng minh đủ nội dung control.',
            'Mỗi lượt có bảng riêng theo phiên bản rubric/nguồn/engine; không cộng tỷ lệ khác điều kiện.',
            'capture_count chỉ là số cặp control/hash trong một lượt, không chứng minh mẫu độc lập.',
            'Số tài khoản hoặc 54 nhãn giả lập không phải 54 ca kiểm định hay nhãn người thật.',
            'Nhãn đủ và tự khai báo độc lập chưa chứng minh trình độ chuyên gia hoặc độc lập bên ngoài.',
            'Chưa xác nhận tập kiểm định mới và nghiệm thu chuyên môn bằng báo cáo tự sinh.'])
    payload['sha256']=digest(payload)
    return payload
