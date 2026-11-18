"""Read-only source acquisition requests; never evidence or owner decisions."""
def build_requests(packet):
    requests=[]
    for row in packet['controls']:
        if row['excluded_by_recorded_decision']:continue
        reason='replace_unusable_source' if 'source_content_unusable' in row['gaps'] else 'supply_missing_source' if 'explicit_sources_missing' in row['gaps'] else None
        if not reason:continue
        requests.append(dict(control_id=row['control_id'],name=row['name'],owner_role=row['owner_role'],reason=reason,
            expected_evidence_types=row['expected_evidence_types'],
            criteria=[c['criterion'] for c in row['criteria']],
            existing_evidence_ids=[s['evidence_id'] for s in row['sources']],
            assignee=None,due_date=None,status='DRAFT_NOT_ASSIGNED',
            submission_checklist=['Bản gốc có nội dung đọc được, không dùng mẫu yêu cầu làm bằng chứng.',
                'Ghi nguồn cung cấp, đối tượng, kỳ quan sát và giới hạn mẫu.',
                'Giữ cấu hình/log/hồ sơ đúng hoặc sai như thực tế; không sửa để tạo kết luận đạt.',
                'Nộp đúng control và loại nguồn; sau tiếp nhận phải đánh giá và thẩm định lại.']))
    return dict(protocol='source-requests-v1',assessment_id=packet['assessment_id'],
        based_on_packet_sha256=packet['sha256'],requests=requests,
        by_role={role:sum(r['owner_role']==role for r in requests) for role in sorted({r['owner_role'] for r in requests})},
        note='Phiếu yêu cầu dự thảo từ hồ sơ hiện hành; không phải bằng chứng, giao việc đã xác nhận hoặc phê duyệt.')


def markdown(report,role=None):
    rows=[r for r in report['requests'] if role is None or r['owner_role']==role]
    lines=['# Yêu cầu bổ sung nguồn đánh giá tuân thủ','',report['note'],'',
        'Đợt: '+report['assessment_id'],'Hash gói bàn giao: '+report['based_on_packet_sha256'],'',
        'Nhóm nhận đề nghị: '+(role or 'Tất cả nhóm'),'Số control cần nguồn: '+str(len(rows))]
    for r in rows:
        lines+=['','## '+r['control_id']+' — '+r['name'],'',
            'Lý do: '+('Nguồn hiện có không dùng được; cần kiểm tra/nộp lại.' if r['reason']=='replace_unusable_source' else 'Chưa có nguồn ngoài preset.'),
            'Người nhận thực tế: ____________________','Hạn cung cấp: ____________________',
            'Loại nguồn được hỗ trợ: '+', '.join(r['expected_evidence_types']),'',
            'Nội dung cần chứng minh hoặc bác bỏ:',*['- '+c for c in r['criteria']],'',
            'Checklist bàn giao:',*['- [ ] '+c for c in r['submission_checklist']]]
    return '\n'.join(lines)+'\n'
