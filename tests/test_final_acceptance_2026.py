"""Comprehensive acceptance test suite covering E2E lifecycle, RBAC isolation, report consistency and security."""
import csv
from contextlib import contextmanager
from copy import deepcopy
from io import BytesIO, StringIO
from uuid import UUID
import pytest
from fastapi import HTTPException
from openpyxl import load_workbook
from pypdf import PdfReader
from backend import main, remediation
from backend.remediation_document_export import pdf_report, xlsx_report
from backend.remediation_export import csv_report, print_report
from evidence_collectors import source_intake


def test_end_to_end_remediation_with_rejection_rework_resubmit_and_reverify():
    """Covers steps 10-20 of the 21-step E2E flow: GAP -> proposal -> edit -> approve -> assign step ->
    execute -> attach -> submit -> verifier requests more_information -> attach additional evidence ->
    resubmit -> independent review -> reverify accepted -> close."""
    control = dict(
        control_id='A.8.13',
        name='Sao lưu thông tin',
        applicability={'applicable': True, 'reason': 'Dịch vụ cốt lõi'},
        review_token='token-initial',
        conclusion='Non-Compliant',
        human_review_current=False,
        human_review=None,
        pass_criteria=['Có log sao lưu gần nhất', 'Có biên bản diễn tập khôi phục'],
        evidence=[dict(evidence_id='ev-before', sha256_hash='hash-before', is_synthetic=False, source='upload-source://A.8.13/before.txt')],
    )
    doc = remediation.finding(
        control,
        'Chưa có biên bản diễn tập khôi phục định kỳ',
        'Hệ thống lưu trữ chính',
        'Chưa ban hành lịch diễn tập hàng quý',
        'high',
    )
    baseline_copy = deepcopy(doc['baseline'])
    proposal = dict(
        title='Thiết lập và diễn tập khôi phục bản sao lưu',
        problem='Thiếu bằng chứng diễn tập khôi phục',
        possible_causes='Chưa phân công lịch diễn tập',
        objective='Thực hiện diễn tập khôi phục và lưu biên bản có xác nhận',
        rationale='Đảm bảo khả năng phục hồi khi sự cố xảy ra',
        target_location='Cụm máy chủ sao lưu',
        estimated_effort='3 ngày làm việc',
        required_evidence='Log restore và biên bản nghiệm thu khôi phục',
        recheck_method='Đối chiếu mã băm bản sao lưu và biên bản khôi phục',
        clarification_questions=['Mục tiêu RPO/RTO hiện tại của hệ thống là bao nhiêu?'],
        steps='1. Chuẩn bị môi trường restore cô lập\n2. Thực hiện khôi phục và ghi biên bản',
        acceptance='Biên bản diễn tập khôi phục khớp checksum',
        department='Hạ tầng CNTT',
        resources='Máy chủ thử nghiệm khôi phục',
        priority='high',
        tasks=['Chuẩn bị môi trường khôi phục thử nghiệm', 'Thực hiện restore và lập biên bản'],
    )
    doc['actions'].append(remediation.action(proposal, 'OLLAMA_DRAFT_REQUIRES_REVIEW'))
    aid = doc['actions'][0]['action_id']

    # Step 12: Consultant edits and approves plan, assigns primary + collaborator
    doc = remediation.transition(
        doc, aid, 'edit',
        dict(note='Chuyên viên điều chỉnh thời gian dự kiến', estimated_effort='2 ngày làm việc'),
        'consultant-1', 'consultant', control,
    )
    assert doc['actions'][0]['estimated_effort'] == '2 ngày làm việc'

    doc = remediation.transition(
        doc, aid, 'approve',
        dict(note='Phê duyệt kế hoạch và giao việc', assignee='operator-1', collaborator_ids=['collab-1'], due_date='2099-12-31'),
        'consultant-1', 'consultant', control,
    )
    assert doc['actions'][0]['state'] == 'NOT_STARTED'

    # Step 13: Assign sub-task 1 to collaborator
    t1_id = doc['actions'][0]['tasks'][0]['task_id']
    t2_id = doc['actions'][0]['tasks'][1]['task_id']
    doc = remediation.transition(
        doc, aid, 'assign_task',
        dict(note='Giao bước chuẩn bị cho người phối hợp', task_id=t1_id, task_assignee='collab-1'),
        'consultant-1', 'consultant', control,
    )

    # Step 14: Collaborator completes step 1, primary operator completes step 2
    doc = remediation.transition(doc, aid, 'task', dict(note='Đã chuẩn bị môi trường restore', task_id=t1_id, done=True), 'collab-1', 'operator', control)
    doc = remediation.transition(doc, aid, 'task', dict(note='Đã chạy restore lần 1', task_id=t2_id, done=True), 'operator-1', 'operator', control)

    # Step 15-16: Upload first post-remediation evidence, attach, and submit
    control['evidence'].append(dict(evidence_id='ev-after-1', sha256_hash='hash-after-1', is_synthetic=False, source='upload-source://A.8.13/after1.txt'))
    control['review_token'] = 'token-after-1'
    doc = remediation.transition(doc, aid, 'attach', dict(note='Đính kèm log restore lần 1', evidence_id='ev-after-1'), 'operator-1', 'operator', control)

    # Collaborator cannot submit on behalf of primary assignee
    with pytest.raises(PermissionError):
        remediation.transition(doc, aid, 'submit', dict(note='Người phối hợp thử gửi'), 'collab-1', 'operator', control)

    doc = remediation.transition(doc, aid, 'submit', dict(note='Gửi hồ sơ xác minh lần 1'), 'operator-1', 'operator', control)
    assert doc['actions'][0]['state'] == 'AWAITING_VERIFICATION'

    # Step 17-18: Independent verifier requests additional information (more_information)
    doc = remediation.transition(
        doc, aid, 'verify',
        dict(note='Log restore chưa có biên bản xác nhận checksum, yêu cầu bổ sung', outcome='more_information'),
        'verifier-1', 'verifier', control,
    )
    assert doc['actions'][0]['state'] == 'NEEDS_INFORMATION'
    assert len(doc['actions'][0]['verifications']) == 1

    # Step 15-16 (Resubmission): Operator uploads additional evidence, attaches, and resubmits
    control['evidence'].append(dict(evidence_id='ev-after-2', sha256_hash='hash-after-2', is_synthetic=False, source='upload-source://A.8.13/after2.txt'))
    control['review_token'] = 'token-after-2'
    doc = remediation.transition(doc, aid, 'attach', dict(note='Bổ sung biên bản đối chiếu checksum', evidence_id='ev-after-2'), 'operator-1', 'operator', control)
    doc = remediation.transition(doc, aid, 'submit', dict(note='Gửi xác minh lại sau khi bổ sung biên bản'), 'operator-1', 'operator', control)
    assert doc['actions'][0]['state'] == 'AWAITING_VERIFICATION'
    assert doc['actions'][0]['submitted_token'] == 'token-after-2'

    # Step 19-20: Verifier completes criteria review on current token and verifies accepted, then closes
    control.update(
        human_review_current=True,
        human_review=dict(
            conclusion='Compliant',
            evidence_ids=['ev-after-1', 'ev-after-2'],
            reviewed_by='verifier-1',
            reviewed_at='2026-11-22T20:00:00+07:00',
        ),
    )
    doc = remediation.transition(
        doc, aid, 'verify',
        dict(note='Đã đối chiếu đủ log restore và biên bản checksum đạt yêu cầu', outcome='accepted'),
        'verifier-1', 'verifier', control,
    )
    assert doc['actions'][0]['state'] == 'VERIFIED'
    assert len(doc['actions'][0]['verifications']) == 2

    doc = remediation.transition(
        doc, aid, 'close',
        dict(note='Đóng hành động khắc phục sau khi xác minh đạt'),
        'verifier-1', 'verifier', control,
    )
    assert doc['actions'][0]['state'] == 'CLOSED'
    assert doc['baseline'] == baseline_copy
    assert control['conclusion'] == 'Non-Compliant'  # Action completion never silently mutates machine conclusion


def test_all_four_report_formats_are_consistent_and_never_claim_certification():
    """Verifies PDF, XLSX, CSV and HTML exports contain consistent before/after, finding, action, task,
    evidence, verification, risk and dashboard data without claiming ISO certification."""
    action_doc = dict(
        action_id='act-100',
        title='Cấu hình sao lưu và diễn tập khôi phục',
        state='VERIFIED',
        department='CNTT',
        assignee='op-1',
        collaborator_ids=['col-1'],
        due_date='2026-12-15',
        priority='high',
        steps='1. Cấu hình lịch backup\n2. Diễn tập restore',
        acceptance='Có log backup và biên bản restore',
        resources='Server backup',
        proposal_origin='OLLAMA_DRAFT_REQUIRES_REVIEW',
        objective='Bảo đảm khả năng khôi phục dữ liệu',
        possible_causes='Chưa có quy trình diễn tập',
        rationale='Giảm rủi ro mất dữ liệu',
        target_location='Phòng máy chủ',
        estimated_effort='2 ngày',
        required_evidence='Biên bản restore có chữ ký',
        recheck_method='Kiểm tra log và mã SHA256',
        clarification_questions=['Chu kỳ sao lưu đầy đủ là bao lâu?'],
        tasks=[dict(task_id='t-1', title='Cấu hình lịch sao lưu', done=True, assignee='col-1')],
        evidence=[dict(evidence_id='WEB-after-1', sha256_hash='abc123after')],
        verifications=[dict(
            at='2026-11-22T20:10:00+07:00',
            reviewer_id='ver-1',
            outcome='accepted',
            note='Đã xác minh biên bản diễn tập.',
            review_token='tok-after',
            conclusion='Compliant',
            human_review_signature='sig-1',
        )],
    )
    finding_doc = dict(
        finding_id='find-100',
        control_id='A.8.13',
        description='Thiếu diễn tập khôi phục sao lưu',
        location='Hệ thống lưu trữ',
        root_cause='Chưa lập lịch diễn tập',
        risk='high',
        actions=[action_doc],
        baseline=dict(
            conclusion='Non-Compliant',
            review_token='tok-before',
            criteria=['Log sao lưu định kỳ', 'Biên bản test restore'],
            evidence=[dict(evidence_id='WEB-before-1', sha256_hash='def456before')],
        ),
    )
    controls = [dict(
        control_id='A.8.13',
        name='Sao lưu thông tin',
        conclusion='Partially Compliant',
        human_review_current=True,
        human_review={'conclusion': 'Compliant'},
        applicability={'applicable': True},
        latest_evaluation_id=1,
        assessment_state='evaluated',
        evidence=[dict(evidence_id='WEB-after-1', is_synthetic=False, source_quality={'usable': True})],
    )]
    records = [dict(
        record_id='find-100',
        kind='finding',
        version=3,
        document=finding_doc,
        current_conclusion='Partially Compliant',
        current_human_conclusion='Compliant',
        current_review_token='tok-after',
        verification_stale=False,
    )]
    dash = remediation.dashboard(records, controls, '2026-11-22')
    dash['portfolio'] = {'registered_clients': 1, 'visible_campaigns': 1}
    report = dict(
        assessment_id='camp-100',
        protocol='corrective-action-report-v1',
        total_actions=1,
        overdue=0,
        by_state={'VERIFIED': 1},
        certification_claim=False,
        context=[{'document': {'name': 'Công ty Nghiệm Thu ISO', 'isms_scope': 'Khối vận hành CNTT'}}],
        records=records,
        dashboard=dash,
        governance=[dict(
            record_id='risk-100',
            kind='risk',
            version=2,
            document=dict(
                title='Rủi ro mất bản sao lưu',
                control_ids=['A.8.13'],
                status='ACKNOWLEDGED',
                inherent_score=20,
                residual_score=5,
                treatment_plan='Diễn tập khôi phục hàng quý',
                owner_id='op-1',
                due_date='2026-12-31',
                rationale='Ảnh hưởng gián đoạn dịch vụ',
            ),
        )],
    )

    # 1. CSV check
    csv_rows = list(csv.reader(StringIO(csv_report(report).lstrip('\ufeff'))))
    assert csv_rows[1][0] == 'A.8.13'
    assert csv_rows[1][2] == 'Non-Compliant'
    assert csv_rows[1][3] == 'Partially Compliant'
    assert csv_rows[1][4] == 'Compliant'
    assert 'WEB-after-1' in csv_rows[1][11]
    assert csv_rows[1][-3] == 'Bảo đảm khả năng khôi phục dữ liệu'

    # 2. HTML check
    html = print_report(report)
    for token in ('Công ty Nghiệm Thu ISO', 'A.8.13', 'Non-Compliant', 'Partially Compliant', 'Compliant',
                  'WEB-before-1', 'WEB-after-1', 'Bảo đảm khả năng khôi phục dữ liệu', 'Rủi ro mất bản sao lưu',
                  'Không phải chứng nhận ISO'):
        assert token in html

    # 3. XLSX check
    wb = load_workbook(BytesIO(xlsx_report(report)), data_only=False)
    assert wb.sheetnames == ['Summary', 'Findings', 'Actions', 'Tasks', 'Verification', 'Control worklist', 'Risk register', 'Requirements']
    assert wb['Findings']['G2'].value == 'Non-Compliant'
    assert wb['Findings']['H2'].value == 'Partially Compliant'
    assert wb['Findings']['I2'].value == 'Compliant'
    assert wb['Actions']['P2'].value == 'Bảo đảm khả năng khôi phục dữ liệu'
    assert wb['Risk register']['B2'].value == 'Rủi ro mất bản sao lưu'

    # 4. PDF check
    pdf_bytes = pdf_report(report)
    assert pdf_bytes.startswith(b'%PDF-')
    pdf_text = '\n'.join(p.extract_text() for p in PdfReader(BytesIO(pdf_bytes)).pages)
    for token in ('Công ty Nghiệm Thu ISO', 'A.8.13', 'Non-Compliant', 'Partially Compliant', 'Compliant',
                  'WEB-before-1', 'WEB-after-1', 'Bảo đảm khả năng khôi phục dữ liệu', 'Rủi ro mất bản sao lưu',
                  'không phải chứng nhận ISO'):
        assert token in pdf_text


def test_security_file_path_traversal_and_invalid_filenames_are_blocked():
    """Ensures path traversal, null bytes, hidden files, and non-hex digests cannot escape the originals store."""
    aid = str(UUID(int=1))
    with pytest.raises(ValueError):
        source_intake.original_path(aid, '../../../etc/passwd')
    with pytest.raises(ValueError):
        source_intake.original_path('not-a-uuid', 'a' * 64)
    for bad_name in ('../secret.txt', '..\\secret.txt', '.env', '_hidden.txt', 'bad\x00name.txt'):
        with pytest.raises(ValueError):
            source_intake.prepare(aid, 'A.8.13', bad_name, b'valid content ' * 20, 'EVID_TECH_BACKUP_LOG', 'Valid origin')


def test_health_check_endpoint_reports_status_without_leaking_secrets(monkeypatch):
    """Verifies /api/health returns connected status and returns 503 when database fails without exposing DATABASE_URL."""
    @contextmanager
    def healthy_conn():
        class Conn:
            @contextmanager
            def cursor(self):
                class Cur:
                    def execute(self, sql): assert sql == 'SELECT 1'
                    def fetchone(self): return (1,)
                yield Cur()
        yield Conn()

    monkeypatch.setattr(main.database, 'get_connection', healthy_conn)
    res = main.health_check()
    assert res['status'] == 'ok' and res['database'] == 'connected'
    assert 'DATABASE_URL' not in str(res)

    @contextmanager
    def broken_conn():
        raise RuntimeError('postgresql://secret_user:secret_pass@localhost:5433/db')
        yield

    monkeypatch.setattr(main.database, 'get_connection', broken_conn)
    with pytest.raises(HTTPException) as exc:
        main.health_check()
    assert exc.value.status_code == 503
    assert 'secret_pass' not in str(exc.value.detail)
