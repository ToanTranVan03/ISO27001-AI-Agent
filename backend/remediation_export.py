"""Read-only print and Excel-compatible CSV from the same authorized report."""
import csv
from io import StringIO
from html import escape


def csv_report(report):
    stream=StringIO(newline='');writer=csv.writer(stream)
    writer.writerow(['Control','Finding','Baseline','Current machine result','Current human result','Action','State','Department','Assignee','Due','Priority','After evidence','Verification stale'])
    def safe(value):
        text=str(value if value is not None else '')
        return "'"+text if text.lstrip().startswith(('=','+','-','@')) else text
    for row in report['records']:
        doc=row['document']
        for a in doc['actions'] or [{}]:
            writer.writerow([safe(v) for v in [doc['control_id'],doc['description'],doc['baseline']['conclusion'],
                row['current_conclusion'],row['current_human_conclusion'],a.get('title'),a.get('state'),a.get('department'),
                a.get('assignee'),a.get('due_date'),a.get('priority'),'; '.join(e['evidence_id'] for e in a.get('evidence',[])),row['verification_stale']]])
    return '\ufeff'+stream.getvalue()


def print_report(report):
    def e(value):return escape(str(value if value is not None else ''))
    parts=['<!doctype html><html lang="vi"><meta charset="utf-8"><title>Báo cáo trước và sau khắc phục</title>',
        '<style>body{font:14px Arial,sans-serif;max-width:1050px;margin:32px auto;color:#123}h1,h2{color:#065f58}section{border:1px solid #ccd;padding:16px;margin:16px 0;break-inside:avoid}p,li{overflow-wrap:anywhere;white-space:pre-wrap}small{color:#567}@media print{button{display:none}body{margin:0}section{break-inside:auto}h2,h3{break-after:avoid}}@page{size:A4;margin:18mm}</style>',
        '<button onclick="window.print()">In / Lưu PDF bằng trình duyệt</button>',
        '<h1>Đánh giá và khắc phục — báo cáo trước / sau</h1>',
        '<p>Không phải chứng nhận ISO. Hoàn thành công việc không tự chứng minh control tuân thủ.</p>',
        '<p>Đợt: '+e(report['assessment_id'])+' · Hành động: '+e(report['total_actions'])+' · Quá hạn: '+e(report['overdue'])+'</p>']
    for context in report.get('context',[]):
        parts+=['<h2>Doanh nghiệp và phạm vi</h2>','<p>'+e(context['document'].get('name'))+'</p>','<p>'+e(context['document'].get('isms_scope'))+'</p>']
    for row in report['records']:
        doc=row['document'];parts+=['<section><h2>'+e(doc['control_id'])+' — '+e(doc['description'])+'</h2>',
            '<p>Vị trí: '+e(doc['location'])+'<br>Nguyên nhân chưa xác nhận: '+e(doc['root_cause'])+'</p>',
            '<p>Trước: '+e(doc['baseline']['conclusion'])+'<br>Máy hiện tại: '+e(row['current_conclusion'])+'<br>Thẩm định hiện hành: '+e(row['current_human_conclusion'] or 'Chưa có')+'</p>',
            '<small>Baseline: '+e(doc['baseline']['review_token'])+'</small>',
            '<p>Nguồn ban đầu: '+e(', '.join(s['evidence_id'] for s in doc['baseline']['evidence']))+'</p>']
        if row['verification_stale']:parts+=['<p><strong>Xác minh đã cũ — cần rà trên nguồn hiện hành.</strong></p>']
        for a in doc['actions']:
            parts+=['<h3>'+e(a['title'])+' — '+e(a['state'])+'</h3>',
                '<p>Phụ trách: '+e(a.get('assignee') or 'Chưa giao')+' · Hạn: '+e(a.get('due_date') or 'Chưa ghi')+'</p>',
                '<p>'+e(a['steps'])+'</p>','<p>Điều kiện nghiệm thu: '+e(a['acceptance'])+'</p>',
                '<ul>'+''.join('<li>'+('[x] ' if t['done'] else '[ ] ')+e(t['title'])+'</li>' for t in a['tasks'])+'</ul>',
                '<p>Nguồn sau: '+e(', '.join(s['evidence_id'] for s in a['evidence']))+'</p>']
            parts+=['<p>'+e(v['at'])+' · '+e(v['outcome'])+' · '+e(v['note'])+'</p>' for v in a['verifications']]
        parts+=['</section>']
    return ''.join(parts)+'</html>'
