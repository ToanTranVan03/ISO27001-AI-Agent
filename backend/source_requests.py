"""Read-only source acquisition requests; never evidence or owner decisions."""
def build_requests(packet):
    requests=[];coverage=[]
    for row in packet['controls']:
        if row['excluded_by_recorded_decision']:continue
        reason=('restore_source_integrity' if 'source_integrity_failed' in row['gaps'] else
                'replace_unusable_source' if 'source_content_unusable' in row['gaps'] else
                'supply_missing_source' if 'explicit_sources_missing' in row['gaps'] else None)
        if not reason:
            if 'human_criteria_review_not_current' in row['gaps'] or 'criteria_unknown' in row['gaps']:
                coverage.append(dict(control_id=row['control_id'],owner_role=row['owner_role'],
                    reason='verify_source_coverage',status='DRAFT_NOT_ASSIGNED',assignee=None,due_date=None,
                    existing_evidence_ids=[s['evidence_id'] for s in row['sources']],
                    criteria=[c['criterion'] for c in row['criteria']],
                    note='Nguồn qua kiểm tra nội dung tối thiểu chưa chứng minh đủ tiêu chí; cần người phụ trách rà phạm vi và viện dẫn.'))
            continue
        requests.append(dict(control_id=row['control_id'],name=row['name'],owner_role=row['owner_role'],reason=reason,
            expected_evidence_types=row['expected_evidence_types'],
            criteria=[c['criterion'] for c in row['criteria']],
            existing_evidence_ids=[s['evidence_id'] for s in row['sources']],
            source_issues=[dict(evidence_id=s['evidence_id'],
                issues=s['source_quality'].get('issues',[]),
                integrity_state=s['source_quality'].get('integrity',{}).get('state','not_verifiable'))
                for s in row['sources'] if s.get('source_quality') and
                (s['source_quality'].get('usable') is False or
                 s['source_quality'].get('integrity',{}).get('state') == 'failed')],
            assignee=None,due_date=None,status='DRAFT_NOT_ASSIGNED',
            submission_checklist=['Bản gốc có nội dung đọc được, không dùng mẫu yêu cầu làm bằng chứng.',
                'Ghi nguồn cung cấp, đối tượng, kỳ quan sát và giới hạn mẫu.',
                'Giữ cấu hình/log/hồ sơ đúng hoặc sai như thực tế; không sửa để tạo kết luận đạt.',
                'Nộp đúng control và loại nguồn; sau tiếp nhận phải đánh giá và thẩm định lại.']))
    return dict(protocol='source-requests-v2',assessment_id=packet['assessment_id'],
        based_on_packet_sha256=packet['sha256'],requests=requests,
        coverage_reviews=coverage,
        by_role={role:sum(r['owner_role']==role for r in requests) for role in sorted({r['owner_role'] for r in requests})},
        note='Phiếu yêu cầu dự thảo từ hồ sơ hiện hành; không phải bằng chứng, giao việc đã xác nhận hoặc phê duyệt.')


def markdown(report,role=None):
    rows=[r for r in report['requests'] if role is None or r['owner_role']==role]
    lines=['# Yêu cầu bổ sung nguồn đánh giá tuân thủ','',report['note'],'',
        'Đợt: '+report['assessment_id'],'Hash gói bàn giao: '+report['based_on_packet_sha256'],'',
        'Nhóm nhận đề nghị: '+(role or 'Tất cả nhóm'),'Số control cần nguồn: '+str(len(rows))]
    for r in rows:
        lines+=['','## '+r['control_id']+' — '+r['name'],'',
            'Lý do: '+({'restore_source_integrity':'Bản lưu thiếu hoặc lệch kiểm tra toàn vẹn; đối chiếu bản gốc và nộp lại đúng nguồn. Không sửa hash để bỏ qua lỗi.',
                'replace_unusable_source':'Nguồn hiện có không dùng được; cần kiểm tra/nộp lại.',
                'supply_missing_source':'Chưa có nguồn ngoài preset.'}[r['reason']]),
            'Người nhận thực tế: ____________________','Hạn cung cấp: ____________________',
            'Loại nguồn được hỗ trợ: '+', '.join(r['expected_evidence_types']),'',
            'Nội dung cần chứng minh hoặc bác bỏ:',*['- '+c for c in r['criteria']],'',
            'Checklist bàn giao:',*['- [ ] '+c for c in r['submission_checklist']]]
        for issue in r.get('source_issues',[]):
            lines+=['- Nguồn cần đối chiếu: '+issue['evidence_id']+'; trạng thái: '+issue['integrity_state']+
                    '; mã lỗi: '+', '.join(issue['issues'])]
    coverage=[r for r in report.get('coverage_reviews',[]) if role is None or r['owner_role']==role]
    if coverage:
        lines+=['','## Rà mức bao phủ nguồn đã có','',
            'Không cộng vào số control thiếu nguồn; không tự xác nhận đủ nội dung hoặc đạt control.']
        for row in coverage:
            lines+=['', '### '+row['control_id'],row['note'],
                'Nguồn hiện có: '+', '.join(row['existing_evidence_ids']),
                *['- [ ] '+c for c in row['criteria']]]
    return '\n'.join(lines)+'\n'
