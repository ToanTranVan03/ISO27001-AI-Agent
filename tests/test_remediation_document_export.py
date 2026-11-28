from copy import deepcopy
from io import BytesIO
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from backend.remediation_document_export import xlsx_report,pdf_report


def fixture():
    action=dict(action_id='action-1',title='Rà soát quyền truy cập',state='REWORK',department='CNTT',
        assignee='operator-1',due_date='2026-12-20',priority='high',steps='Đọc cấu hình, rà tài khoản và ghi lại căn cứ.',
        acceptance='Người xác minh độc lập đối chiếu từng tiêu chí.',resources='Chủ sở hữu tài khoản',
        proposal_origin='CONSULTANT_DRAFT',tasks=[dict(task_id='task-1',title='Kiểm kê tài khoản',done=True)],
        evidence=[dict(evidence_id='after-1',sha256_hash='after-hash')],
        verifications=[dict(at='2026-11-22T10:00:00+07:00',reviewer_id='verifier-1',outcome='partial',
            note='Cần bổ sung bằng chứng cho tài khoản đặc quyền.',review_token='after-token',conclusion='Partially Compliant')])
    doc=dict(finding_id='finding-1',control_id='A.8.2',description='Thiếu hồ sơ rà quyền',location='Hệ thống quản trị',
        root_cause='Chưa xác nhận nguyên nhân',risk='unconfirmed',actions=[action],
        baseline=dict(conclusion='Non-Compliant',review_token='before-token',criteria=['Rà quyền theo phạm vi đã xác nhận'],
            evidence=[dict(evidence_id='before-1',sha256_hash='before-hash')]))
    return dict(assessment_id='campaign-1',total_actions=1,overdue=0,by_state={'REWORK':1},
        context=[{'document':{'name':'Tổ chức thử nghiệm','isms_scope':'Một hệ thống và phòng CNTT.'}}],
        records=[dict(record_id='finding-1',document=doc,current_conclusion='Partially Compliant',
            current_human_conclusion='Insufficient Evidence',current_review_token='after-token',verification_stale=True)])


def test_xlsx_preserves_traceable_views_and_neutralizes_formulas_without_mutating():
    report=fixture();report['records'][0]['document']['description']='\ufeff =HYPERLINK("bad")'
    report['records'][0]['document']['actions'][0]['title']='@malicious'
    before=deepcopy(report);raw=xlsx_report(report)
    workbook=load_workbook(BytesIO(raw),data_only=False)
    assert workbook.sheetnames==['Summary','Findings','Actions','Tasks','Verification']
    assert workbook['Findings']['C2'].value.startswith("'")
    assert workbook['Actions']['D2'].value=="'@malicious"
    assert workbook['Findings']['G2'].value=='Non-Compliant'
    assert workbook['Findings']['H2'].value=='Partially Compliant'
    assert 'before-1' in workbook['Findings']['M2'].value
    assert 'after-1' in workbook['Actions']['N2'].value
    assert workbook['Tasks']['F2'].value is True
    assert workbook['Verification']['D2'].value=='verifier-1'
    for sheet in workbook:
        assert sheet.freeze_panes=='A2' and sheet.auto_filter.ref
        assert not any(cell.data_type=='f' for row in sheet for cell in row)
    assert report==before


def test_pdf_has_vietnamese_before_after_evidence_and_verification():
    report=fixture();before=deepcopy(report)
    raw=pdf_report(report);assert raw.startswith(b'%PDF-')
    reader=PdfReader(BytesIO(raw));text='\n'.join(p.extract_text() for p in reader.pages)
    for expected in ('Mã phát hiện: finding-1','Tổ chức thử nghiệm','Non-Compliant','Partially Compliant','before-1','after-1','verifier-1','REWORK','không phải chứng nhận ISO'):
        assert expected in text
    assert report==before


def test_exports_trace_the_selected_a8_capture():
    report=fixture()
    capture=dict(run_id='a8-run-1',report_sha256='a'*64,asset_id='DEBIAN-LAB-01',evidence_id='A8CAP-1')
    report['records'][0]['document']['a8_capture']=capture
    pdf=''.join(p.extract_text() for p in PdfReader(BytesIO(pdf_report(report))).pages)
    workbook=load_workbook(BytesIO(xlsx_report(report)))
    row=[cell.value for cell in workbook['Findings'][2]]
    for value in capture.values():
        assert value in ''.join(pdf.split())
        assert value in row


def test_pdf_handles_escaped_markup_and_long_fields_across_pages():
    report=fixture();doc=report['records'][0]['document']
    doc['description']='<script>test & evidence</script>'
    doc['actions'][0]['steps']='Chuỗi dài cần phân trang. '*1500
    raw=pdf_report(report);reader=PdfReader(BytesIO(raw))
    assert len(reader.pages)>3
    assert '<script>test & evidence</script>' in '\n'.join(p.extract_text() for p in reader.pages)
    assert all(p.mediabox.width>500 for p in reader.pages)


def test_empty_reports_export_without_invented_findings():
    report=dict(assessment_id='empty',total_actions=0,overdue=0,records=[],context=[],by_state={})
    workbook=load_workbook(BytesIO(xlsx_report(report)))
    assert workbook['Findings'].max_row==1 and workbook['Actions'].max_row==1
    assert len(PdfReader(BytesIO(pdf_report(report))).pages)==1


def test_missing_or_incompatible_configured_font_is_explicit(monkeypatch,tmp_path):
    monkeypatch.setenv('REMEDIATION_PDF_FONT',str(tmp_path/'missing.ttf'))
    with pytest.raises(ValueError,match='Unicode'):pdf_report(fixture())


def test_excel_cell_limit_is_not_silently_truncated():
    report=fixture();report['records'][0]['document']['description']='x'*32768
    with pytest.raises(ValueError,match='32767'):xlsx_report(report)
