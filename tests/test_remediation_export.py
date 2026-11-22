import csv
from io import StringIO
from backend.remediation_export import csv_report,print_report


def test_exports_preserve_baseline_escape_html_and_spreadsheet_formulas():
    baseline={'conclusion':'Non-Compliant','review_token':'before','evidence':[{'evidence_id':'old'}]}
    row=dict(document={'control_id':'A.8.13','description':'=malicious()','location':'<script>alert(1)</script>',
        'root_cause':'Unconfirmed','baseline':baseline,'actions':[]},current_conclusion='Partially Compliant',current_human_conclusion=None,verification_stale=True)
    report=dict(assessment_id='test',total_actions=0,overdue=0,records=[row],context=[])
    csv_text=csv_report(report)
    rows=list(csv.reader(StringIO(csv_text.lstrip('\ufeff'))))
    assert rows[1][1]=="'=malicious()" and rows[1][2]=='Non-Compliant'
    html=print_report(report)
    assert '<script>alert' not in html and '&lt;script&gt;' in html
    assert 'Non-Compliant' in html and 'Partially Compliant' in html and 'window.print()' in html


def test_print_and_csv_include_leadership_dashboard_and_structured_advice():
    baseline={'conclusion':'Non-Compliant','review_token':'before','evidence':[{'evidence_id':'old'}]}
    action={'title':'Triển khai sao lưu','state':'IN_PROGRESS','department':'IT','assignee':'op','due_date':'2026-12-01',
            'priority':'high','steps':'1. Cấu hình backup','acceptance':'Biên bản khôi phục','tasks':[{'title':'Bước 1','done':True,'assignee':'helper'}],
            'evidence':[{'evidence_id':'after-1'}],'verifications':[],'collaborator_ids':['helper'],
            'objective':'Đảm bảo khôi phục dữ liệu','required_evidence':'Log restore','recheck_method':'Đối chiếu SHA256',
            'clarification_questions':['Tần suất RPO hiện tại là bao nhiêu?']}
    row=dict(document={'control_id':'A.8.13','description':'Thiếu diễn tập khôi phục','location':'Server backup',
        'root_cause':'Chưa có lịch định kỳ','risk':'high','baseline':baseline,'actions':[action]},
        current_conclusion='Partially Compliant',current_human_conclusion=None,verification_stale=False)
    report=dict(assessment_id='test',total_actions=1,overdue=0,records=[row],context=[],
        dashboard={'completion_percent':50,'decisions_pending':10,'due_soon':1,'conclusions':{'Partially Compliant':1},
            'risk_proposals':{'high':1},'urgent':[{'control_id':'A.8.13','description':'Thiếu diễn tập khôi phục'}],
            'worklist':[{'control_id':'A.8.13','flags':['remediating'],'required_tasks':['Thực hiện công việc và đính kèm bằng chứng sau']}]},
        governance=[{'kind':'risk','document':{'title':'Mất dữ liệu','status':'ACKNOWLEDGED','control_ids':['A.8.13'],'inherent_score':20,'residual_score':10,'treatment_plan':'Diễn tập định kỳ'}}])
    html=print_report(report)
    assert 'Tổng quan lãnh đạo' in html and 'Đảm bảo khôi phục dữ liệu' in html and 'Tần suất RPO hiện tại là bao nhiêu?' in html and 'Mất dữ liệu' in html
    rows=list(csv.reader(StringIO(csv_report(report).lstrip('\ufeff'))))
    assert rows[0][-3:]==['Objective','Required evidence','Recheck method']
    assert rows[1][-3:]==['Đảm bảo khôi phục dữ liệu','Log restore','Đối chiếu SHA256']
