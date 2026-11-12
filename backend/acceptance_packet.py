"""Read-only handoff from a scope snapshot; never invent evidence or approvals."""
from agent_core.a8_assessment import digest


def build_packet(scope):
    rows = []
    for control in scope['controls']:
        decision = control['applicability']
        excluded = decision is not None and decision['applicable'] is False
        review = control['human_review'] if control['human_review_current'] else None
        reviewed = {item['criterion_index']: item for item in review['criteria_reviews']} if review else {}
        checks = []
        for index, text in enumerate(control['pass_criteria']):
            item = reviewed.get(index)
            checks.append(dict(criterion_index=index, criterion=text,
                verified_verdict=item['verdict'] if item else 'not_reviewed',
                verified_evidence_ids=item['evidence_ids'] if item else [],
                request=None if excluded or item and item['verdict'] == 'met' else
                    f'Cung cấp nguồn có nội dung chứng minh hoặc bác bỏ: {text}. Ghi đối tượng, kỳ kiểm tra, người sở hữu và giới hạn mẫu.'))
        gaps = []
        if decision is None: gaps.append('applicability_not_decided')
        if not excluded:
            if not control['explicit_source_count']: gaps.append('explicit_sources_missing')
            if control['assessment_state'] != 'evaluated': gaps.append('evaluation_not_current')
            if not review: gaps.append('human_criteria_review_not_current')
            if any(c['verified_verdict'] == 'unknown' for c in checks): gaps.append('criteria_unknown')
            if any(c['verified_verdict'] == 'not_met' for c in checks): gaps.append('criteria_not_met')
        rows.append(dict(control_id=control['control_id'],name=control['name'],
            owner_role={'A.6':'Nhân sự / người phụ trách ATTT', 'A.7':'Hành chính / an ninh vật lý',
                        'A.8':'IT / vận hành / ATTT'}[control['control_id'][:3]],
            priority_a8=control['priority_a8'],applicability=decision,
            excluded_by_recorded_decision=excluded,criteria=checks,
            expected_evidence_types=control['expected_evidence_types'],
            missing_evidence_types=control['evidence_types_to_check'],
            sources=[dict(evidence_id=e['evidence_id'],sha256=e['sha256_hash'],
                source=e.get('source'),is_synthetic=e.get('is_synthetic'),
                evidence_type=e.get('evidence_type')) for e in control['evidence']],
            machine_conclusion=control['conclusion'],
            current_human_conclusion=review['conclusion'] if review else None,
            review_token=control['review_token'],gaps=gaps,
            treatment_proposal=dict(status='DRAFT_REQUIRES_OWNER',
                action='Giữ căn cứ loại trừ để người phụ trách rà SoA.' if excluded else
                    'Thu nguồn cho các yêu cầu tiêu chí; xử lý điểm không đạt, đánh giá lại và thẩm định trên snapshot mới.' if gaps else
                    'Duy trì biện pháp, xác định kỳ rà soát và trình người phụ trách duyệt.',
                assignee=None,due_date=None,approved=False,
                recorded_treatment=decision['treatment'] if decision else None),
            recorded_follow_up=dict(owner=decision.get('treatment_owner') if decision else None,
                due_date=decision.get('treatment_due') if decision else None,
                verification_plan=decision.get('verification_plan') if decision else None)))
    packet = dict(protocol='week5-handoff-v1',assessment_id=scope['assessment_id'],
        rubric_sha256=scope['rubric_sha256'],soa_fingerprint=scope['soa']['fingerprint'],
        formal_soa_approval=scope['soa']['approval'],controls=rows,
        technical_scope_total=scope['scope_total'],
        professional_acceptance='NOT_ASSERTED',
        external_requirements=[
            'Người có trách nhiệm xác nhận rubric và mức bao phủ từng control.',
            'Giảng viên xác nhận tư cách người đánh giá và phương pháp đối chiếu.',
            'Thu nhãn thật cùng nguồn đã chốt; không dùng AI chấm thay con người.',
            'Xác nhận tập kiểm định chưa dùng phát triển; dò trùng không chứng minh độc lập.',
            'Kiểm tra UI có đăng nhập; ghi người thực hiện và kết quả thực tế.',
            'Người có thẩm quyền rà tính áp dụng, kế hoạch xử lý và phê duyệt SoA.'],
        note='Dự thảo giao việc từ snapshot, không phải hồ sơ bằng chứng hoặc biên bản nghiệm thu. Loại nguồn có mặt không chứng minh đủ nội dung. Đề xuất không được ghi vào quyết định áp dụng/phê duyệt.')
    packet['sha256'] = digest(packet)
    return packet
