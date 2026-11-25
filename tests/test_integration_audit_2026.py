"""Integration and synchronization audit suite covering the 5 end-to-end data linkage flows."""
import csv
import json
from contextlib import contextmanager
from copy import deepcopy
from io import BytesIO, StringIO
from types import SimpleNamespace
from uuid import UUID, uuid4
import pytest
from fastapi import HTTPException
from openpyxl import load_workbook
from pypdf import PdfReader
from backend import (
    governance_api,
    remediation,
    remediation_api,
    remediation_notifications,
    team_api,
)
from backend.remediation_document_export import pdf_report, xlsx_report
from backend.remediation_export import csv_report, print_report


def test_flow1_new_client_campaign_context_linkage_and_finding_creation(monkeypatch):
    """Flow 1: Create client A -> campaign A1 -> edit ISMS context (verifying record_id linkage
    between create_client_campaign and PUT /remediation/context) -> sync company name -> create finding."""
    store = {'remediation_records': {}, 'company_name': None}
    user = {'user_id': str(uuid4()), 'role': 'admin'}

    class Cursor:
        def __init__(self):
            self.last_row = None

        def execute(self, sql, args=()):
            self.sql = sql
            if "INSERT INTO remediation_records VALUES(%s,%s,'context',1,%s)" in sql:
                aid, rid, doc = args[0], args[1], args[2].obj
                store['remediation_records'][(str(aid), str(rid))] = ('context', 1, doc)
            elif "SELECT record_id,version,document FROM remediation_records WHERE assessment_id=%s AND kind='context'" in sql:
                aid = str(args[0])
                match = next(
                    (( UUID(rid), v, d) for (a, rid), (k, v, d) in store['remediation_records'].items() if a == aid and k == 'context'),
                    None,
                )
                self.last_row = match
            elif "UPDATE enterprise_company SET metadata=jsonb_set(metadata,'{name}',%s)" in sql:
                store['company_name'] = args[0].obj
            elif "UPDATE remediation_records SET version=version+1,document=%s" in sql:
                doc, aid, rid = args[0].obj, str(args[1]), str(args[2])
                kind, ver, _ = store['remediation_records'][(aid, rid)]
                store['remediation_records'][(aid, rid)] = (kind, ver + 1, doc)

        def fetchone(self):
            return self.last_row

    @contextmanager
    def fake_conn():
        class Conn:
            @contextmanager
            def cursor(self):
                yield Cursor()
        yield Conn()

    cur = Cursor()
    camp_req = team_api.CampaignInput(name='Đợt 1 Khách hàng A', isms_scope='Phạm vi ban đầu của Khách hàng A')
    created = team_api.create_client_campaign(
        cur, str(uuid4()),
        {'name': 'Khách hàng A', 'sector': 'Tài chính', 'contact': 'Liên hệ A', 'locations': 'Hà Nội'},
        camp_req, user,
    )
    aid = UUID(created['assessment_id'])
    assert (str(aid), str(aid)) in store['remediation_records']

    monkeypatch.setattr(remediation_api, 'get_connection', fake_conn)
    monkeypatch.setattr(remediation_api, 'membership', lambda *_: 'consultant')

    # Updating the context initialized by create_client_campaign with expected_version=1 must succeed (version -> 2)
    updated_ctx = remediation_api.context(
        aid,
        remediation_api.Context(
            expected_version=1,
            name='Khách hàng A (Đã cập nhật)',
            sector='Tài chính số',
            isms_scope='Phạm vi ISMS mở rộng toàn bộ cổng thanh toán',
            locations='Hà Nội & TP.HCM',
            departments='CNTT, Vận hành',
            assets_systems='SRV-01, DB-01',
            obligations='Nghị định 13/2023/NĐ-CP',
            risks='Gián đoạn dịch vụ',
            contact='CISO Khách hàng A',
        ),
        user,
    )
    assert updated_ctx['version'] == 2
    assert len(updated_ctx['document']['history']) == 2
    assert store['company_name'] == 'Khách hàng A (Đã cập nhật)'

    # Stale expected_version=1 must now be rejected with 409 Conflict
    with pytest.raises(HTTPException) as exc:
        remediation_api.context(
            aid,
            remediation_api.Context(
                expected_version=1, name='Stale', sector='Stale',
                isms_scope='Stale scope check only', locations='', departments='',
                assets_systems='', obligations='', risks='', contact='',
            ),
            user,
        )
    assert exc.value.status_code == 409


def test_flow2_and_flow4_remediation_dashboard_and_report_synchronization():
    """Flows 2 & 4: Full remediation lifecycle + human review conclusion synchronization across
    Scope56, Dashboard (conclusions, worklist, completion_percent, remaining_issues) and all 4 export formats."""
    control = dict(
        control_id='A.8.13',
        name='Sao lưu thông tin',
        applicability={'applicable': True, 'reason': 'Hệ thống trọng yếu'},
        review_token='tok-v1',
        conclusion='Partially Compliant',
        latest_evaluation_id=10,
        assessment_state='evaluated',
        human_review_current=False,
        human_review=None,
        pass_criteria=['Có log sao lưu gần nhất', 'Có biên bản kiểm thử khôi phục'],
        evidence=[dict(
            evidence_id='WEB-before',
            sha256_hash='hash-before',
            is_synthetic=False,
            source='upload-source://A.8.13/before.txt',
            source_quality={'usable': True},
        )],
    )
    finding_doc = remediation.finding(
        control, 'Thiếu biên bản diễn tập khôi phục định kỳ', 'Cụm lưu trữ chính', 'Chưa lập lịch diễn tập', 'high'
    )
    finding_doc['actions'].append(remediation.action(dict(
        title='Tổ chức diễn tập khôi phục dữ liệu',
        problem='Chưa có bằng chứng restore test',
        possible_causes='Thiếu quy trình định kỳ',
        objective='Khôi phục thử nghiệm thành công trên máy chủ cô lập',
        rationale='Đảm bảo khả năng phục hồi sau thảm họa',
        target_location='SRV-RESTORE-LAB',
        estimated_effort='2 ngày',
        required_evidence='Biên bản restore test có mã SHA256',
        recheck_method='Đối chiếu hash dữ liệu sau khôi phục',
        clarification_questions=['Chu kỳ diễn tập yêu cầu là hàng quý hay nửa năm?'],
        steps='1. Chuẩn bị máy chủ\n2. Chạy restore và ghi biên bản',
        acceptance='Khôi phục thành công 100%',
        department='Hạ tầng',
        resources='Máy chủ SRV-RESTORE-LAB',
        priority='high',
        tasks=['Chuẩn bị máy chủ cô lập', 'Chạy restore và đối chiếu SHA256'],
    ), 'OLLAMA_DRAFT_REQUIRES_REVIEW'))
    act_id = finding_doc['actions'][0]['action_id']

    # Dashboard BEFORE remediation completion
    records_before = [dict(record_id=finding_doc['finding_id'], kind='finding', version=1, document=deepcopy(finding_doc))]
    dash_before = remediation.dashboard(records_before, [deepcopy(control)], '2026-11-25')
    assert dash_before['completion_percent'] == 0.0
    assert dash_before['conclusions'] == {'Partially Compliant': 1}
    assert len(dash_before['remaining_issues']) == 1
    assert 'needs_review' in dash_before['worklist'][0]['flags']

    # Execute lifecycle: approve -> assign_task -> complete tasks -> attach -> submit -> request more_information -> resubmit -> review -> verify -> close
    finding_doc = remediation.transition(
        finding_doc, act_id, 'approve',
        dict(note='Duyệt kế hoạch khắc phục', assignee='op-main', collaborator_ids=['op-sub'], due_date='2099-12-31'),
        'cons-1', 'consultant', control,
    )
    t1, t2 = [t['task_id'] for t in finding_doc['actions'][0]['tasks']]
    finding_doc = remediation.transition(
        finding_doc, act_id, 'assign_task',
        dict(note='Giao bước 1 cho người phối hợp', task_id=t1, task_assignee='op-sub'),
        'cons-1', 'consultant', control,
    )
    finding_doc = remediation.transition(finding_doc, act_id, 'task', dict(note='Xong bước 1', task_id=t1, done=True), 'op-sub', 'operator', control)
    finding_doc = remediation.transition(finding_doc, act_id, 'task', dict(note='Xong bước 2', task_id=t2, done=True), 'op-main', 'operator', control)

    control['evidence'].append(dict(
        evidence_id='WEB-after',
        sha256_hash='hash-after',
        is_synthetic=False,
        source='upload-source://A.8.13/after.txt',
        source_quality={'usable': True},
    ))
    control['review_token'] = 'tok-v2'
    finding_doc = remediation.transition(finding_doc, act_id, 'attach', dict(note='Đính kèm biên bản mới', evidence_id='WEB-after'), 'op-main', 'operator', control)
    finding_doc = remediation.transition(finding_doc, act_id, 'submit', dict(note='Gửi xác minh'), 'op-main', 'operator', control)

    # Human reviewer signs Compliant criteria review citing WEB-after
    control.update(
        human_review_current=True,
        human_review=dict(
            conclusion='Compliant',
            evidence_ids=['WEB-after'],
            reviewed_by='ver-1',
            reviewed_at='2026-11-25T08:00:00+07:00',
        ),
    )
    finding_doc = remediation.transition(finding_doc, act_id, 'verify', dict(note='Xác minh đạt đủ tiêu chí', outcome='accepted'), 'ver-1', 'verifier', control)
    finding_doc = remediation.transition(finding_doc, act_id, 'close', dict(note='Đóng hành động'), 'ver-1', 'verifier', control)

    # Dashboard AFTER remediation & human review: must reflect Compliant conclusion & 0 remaining issues
    records_after = [dict(
        record_id=finding_doc['finding_id'],
        kind='finding',
        version=8,
        document=finding_doc,
        current_conclusion=control['conclusion'],
        current_human_conclusion=control['human_review']['conclusion'],
        current_review_token=control['review_token'],
        verification_stale=False,
    )]
    dash_after = remediation.dashboard(records_after, [control], '2026-11-25')
    dash_after['portfolio'] = {'registered_clients': 1, 'visible_campaigns': 1}
    assert dash_after['completion_percent'] == 100.0
    assert dash_after['completed'] == 1
    assert dash_after['conclusions'] == {'Compliant': 1}
    assert dash_after['worklist'][0]['conclusion'] == 'Compliant'
    assert dash_after['worklist'][0]['machine_conclusion'] == 'Partially Compliant'
    assert len(dash_after['remaining_issues']) == 0
    assert 'has_verified_action' in dash_after['worklist'][0]['flags']
    assert 'needs_review' not in dash_after['worklist'][0]['flags']

    # Verify report exports match Dashboard & Database records
    report = dict(
        assessment_id='camp-sync-1',
        protocol='corrective-action-report-v1',
        total_actions=1,
        overdue=0,
        by_state={'CLOSED': 1},
        certification_claim=False,
        context=[{'document': {'name': 'Công ty Đồng Bộ', 'isms_scope': 'Hạ tầng sao lưu'}}],
        records=records_after,
        dashboard=dash_after,
        governance=[],
    )
    wb = load_workbook(BytesIO(xlsx_report(report)), data_only=False)
    summary_map = {wb['Summary'][f'A{r}'].value: wb['Summary'][f'B{r}'].value for r in range(2, wb['Summary'].max_row + 1)}
    assert summary_map['Workflow completion percent (not compliance)'] == 100
    assert summary_map['Certification claim'] is False
    assert wb['Findings']['G2'].value == 'Partially Compliant'  # Initial baseline preserved
    assert wb['Findings']['I2'].value == 'Compliant'            # Current human review conclusion
    assert wb['Control worklist']['C2'].value == 'Compliant'    # Worklist synced with effective conclusion

    pdf_text = '\n'.join(p.extract_text() for p in PdfReader(BytesIO(pdf_report(report))).pages)
    assert 'Công ty Đồng Bộ' in pdf_text and '100.0%' in pdf_text and 'Compliant' in pdf_text
    assert 'WEB-before' in pdf_text and 'WEB-after' in pdf_text
    html = print_report(report)
    assert '100.0%' in html and 'Compliant' in html
    csv_rows = list(csv.reader(StringIO(csv_report(report).lstrip('\ufeff'))))
    assert csv_rows[1][2] == 'Partially Compliant' and csv_rows[1][4] == 'Compliant'


def test_flow3_multi_tenant_and_role_isolation(monkeypatch):
    """Flow 3: Client A vs Client B isolation and operator action filtering in board()."""
    aid_a, aid_b = UUID(int=10), UUID(int=20)
    user_a = {'user_id': 'user-a', 'role': 'assessor'}

    # User A is not a member of campaign B -> require_campaign must raise 403
    monkeypatch.setattr(team_api.teamwork, 'require_member', lambda aid, uid: (_ for _ in ()).throw(PermissionError('Not a member')) if aid == str(aid_b) else None)
    with pytest.raises(HTTPException) as exc:
        team_api.require_campaign(aid_b, user_a)
    assert exc.value.status_code == 403

    # In campaign A, an operator only sees findings/actions assigned to them or where they are a collaborator
    f1 = {'finding_id': 'f1', 'control_id': 'A.8.13', 'actions': [
        {'action_id': 'a1', 'title': 'Mine', 'assignee': 'user-a', 'collaborator_ids': []},
        {'action_id': 'a2', 'title': 'Other', 'assignee': 'user-other', 'collaborator_ids': []},
    ]}
    f2 = {'finding_id': 'f2', 'control_id': 'A.6.1', 'actions': [
        {'action_id': 'a3', 'title': 'Unrelated', 'assignee': 'user-other', 'collaborator_ids': []},
    ]}

    @contextmanager
    def fake_conn():
        class Conn:
            @contextmanager
            def cursor(self):
                class Cur:
                    def execute(self, sql, args=()): self.sql = sql
                    def fetchall(self):
                        if 'FROM remediation_records' in self.sql:
                            return [('f1', 'finding', 1, deepcopy(f1)), ('f2', 'finding', 1, deepcopy(f2))]
                        return [('user-a', 'User A', 'operator')]
                yield Cur()
        yield Conn()

    monkeypatch.setattr(remediation_api, 'get_connection', fake_conn)
    monkeypatch.setattr(remediation_api, 'membership', lambda *_: 'operator')
    board = remediation_api.board(aid_a, user_a)
    assert len(board['records']) == 1
    assert [a['action_id'] for a in board['records'][0]['document']['actions']] == ['a1']


def test_flow5_error_recovery_atomicity_and_duplicate_protection(monkeypatch):
    """Flow 5: Verifies failed transitions or bad AI responses do not partially mutate state,
    and governance register self-review is blocked."""
    control = dict(
        control_id='A.8.13', applicability=None, review_token='tok-1', conclusion='Non-Compliant',
        human_review_current=False, human_review=None, pass_criteria=['Check backup'],
        evidence=[dict(evidence_id='ev-1', sha256_hash='h1')],
    )
    doc = remediation.finding(control, 'Backup gap', 'Server', 'Cause', 'high')
    doc['actions'].append(remediation.action(dict(
        title='Fix backup', steps='Step 1 and Step 2', acceptance='Pass', department='IT',
        resources='Admin', tasks=['Task 1', 'Task 2'],
    ), 'CONSULTANT_DRAFT'))
    aid = doc['actions'][0]['action_id']
    doc = remediation.transition(doc, aid, 'approve', dict(note='Approved plan', assignee='op-1', due_date='2099-12-31'), 'cons-1', 'consultant', control)
    snapshot_before_errors = deepcopy(doc)

    # 1. Out-of-order task completion fails without mutating doc
    with pytest.raises(ValueError):
        remediation.transition(doc, aid, 'task', dict(note='Try task 2 first', task_id=doc['actions'][0]['tasks'][1]['task_id'], done=True), 'op-1', 'operator', control)
    assert doc == snapshot_before_errors

    # 2. Premature submit fails without mutating doc
    with pytest.raises(ValueError):
        remediation.transition(doc, aid, 'submit', dict(note='Try premature submit'), 'op-1', 'operator', control)
    assert doc == snapshot_before_errors

    # 3. Governance register self-review is blocked with 403
    @contextmanager
    def gov_conn():
        class Conn:
            @contextmanager
            def cursor(self):
                class Cur:
                    def execute(self, sql, args=()): pass
                    def fetchone(self):
                        return (1, 'risk', {'last_editor': 'same-user', 'context_version': 1, 'history': []})
                yield Cur()
        yield Conn()

    monkeypatch.setattr(governance_api, 'get_connection', gov_conn)
    monkeypatch.setattr(governance_api, 'membership', lambda *_: 'consultant')
    with pytest.raises(HTTPException) as exc:
        governance_api.review(
            UUID(int=1), UUID(int=2),
            governance_api.Review(expected_version=1, decision='acknowledge', note='Self review attempt must be blocked by backend'),
            {'user_id': 'same-user'},
        )
    assert exc.value.status_code == 403
