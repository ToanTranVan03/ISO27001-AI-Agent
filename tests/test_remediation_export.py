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
