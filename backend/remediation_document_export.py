"""Downloadable XLSX/PDF views of an already authorized corrective-action report."""
from io import BytesIO
from pathlib import Path
from html import escape
import hashlib
import os
import re
import threading

DISCLAIMER='Báo cáo hỗ trợ đánh giá và khắc phục; không phải chứng nhận ISO. Hoàn tất công việc không tự chứng minh tuân thủ.'
_font_lock=threading.Lock()


def text(value):
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '\ufffd', str(value if value is not None else ''))


def excel_text(value):
    value=text(value)
    if len(value)>32767:raise ValueError('Nội dung vượt giới hạn 32767 ký tự/ô Excel; dùng JSON để giữ toàn bộ dữ liệu.')
    if value.lstrip('\ufeff \t\r\n').startswith(('=','+','-','@')):value="'"+value
    return value


def xlsx_report(report):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment,Font,PatternFill
    from openpyxl.utils import get_column_letter
    workbook=Workbook();workbook.remove(workbook.active)
    def sheet(name,headers,rows):
        ws=workbook.create_sheet(name)
        ws.append([excel_text(h) for h in headers])
        for row in rows:ws.append([v if type(v) in (int,float,bool) else excel_text(v) for v in row])
        ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
        ws.sheet_view.showGridLines=False
        for cell in ws[1]:
            cell.fill=PatternFill('solid',fgColor='103547');cell.font=Font(name='Arial',bold=True,color='FFFFFF')
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.font=Font(name='Arial',size=10,color='17354A')
                cell.alignment=Alignment(vertical='top',wrap_text=True)
                if cell.row%2==0:cell.fill=PatternFill('solid',fgColor='EDF7F6')
        for col in range(1,len(headers)+1):
            maximum=max(len(text(ws.cell(r,col).value).split('\n')[0]) for r in range(1,ws.max_row+1))
            ws.column_dimensions[get_column_letter(col)].width=min(58,max(18,maximum+2))
        ws.row_dimensions[1].height=30
        ws.print_title_rows='1:1';ws.sheet_properties.pageSetUpPr.fitToPage=True
        ws.page_setup.orientation='landscape';ws.page_setup.paperSize=ws.PAPERSIZE_A4
        ws.page_setup.fitToWidth=1;ws.page_setup.fitToHeight=0
        ws.oddFooter.center.text='Page &P / &N'
        return ws
    summary=[['Assessment',report['assessment_id']],['Total actions',report['total_actions']],
        ['Overdue actions',report['overdue']],['Certification claim',False],['Notice',DISCLAIMER]]
    summary.extend(['State: '+str(k),v] for k,v in report.get('by_state',{}).items())
    for context in report.get('context',[]):
        for key in ('name','sector','isms_scope','locations','departments','assets_systems','obligations','risks','contact'):
            summary.append(['Company: '+key,context['document'].get(key,'')])
    sheet('Summary',['Field','Recorded value'],summary)
    findings=[];actions=[];tasks=[];verifications=[]
    for row in report['records']:
        doc=row['document'];fid=row.get('record_id',doc.get('finding_id',''))
        baseline=doc['baseline']
        findings.append([fid,doc['control_id'],doc['description'],doc['location'],doc['root_cause'],doc.get('risk'),
            baseline['conclusion'],row.get('current_conclusion'),row.get('current_human_conclusion'),
            baseline['review_token'],row.get('current_review_token'),row.get('verification_stale',False),
            '\n'.join(text(e.get('evidence_id'))+' | '+text(e.get('sha256_hash')) for e in baseline['evidence']),
            '\n'.join(baseline.get('criteria',[]))])
        for a in doc['actions']:
            aid=a['action_id']
            actions.append([fid,doc['control_id'],aid,a['title'],a['state'],a.get('department'),a.get('assignee'),
                a.get('due_date'),a.get('priority'),a['steps'],a['acceptance'],a.get('resources'),a.get('proposal_origin'),
                '\n'.join(text(e.get('evidence_id'))+' | '+text(e.get('sha256_hash')) for e in a['evidence'])])
            for index,task in enumerate(a['tasks'],1):tasks.append([fid,aid,index,task['task_id'],task['title'],task['done']])
            for v in a['verifications']:verifications.append([fid,aid,v.get('at'),v.get('reviewer_id'),v['outcome'],
                v['note'],v.get('review_token'),v.get('conclusion'),v.get('human_review_signature')])
    sheet('Findings',['Finding ID','Control','Finding','Location','Reported cause','Risk proposed','Initial result','Current machine','Current human','Baseline token','Current token','Verification stale','Initial evidence ID / hash','Criteria'],findings)
    sheet('Actions',['Finding ID','Control','Action ID','Action','Workflow state','Department','Assignee ID','Due date','Priority','Instructions','Acceptance evidence','Resources','Proposal origin','After evidence ID / hash'],actions)
    sheet('Tasks',['Finding ID','Action ID','Sequence','Task ID','Task','Done by executor'],tasks)
    sheet('Verification',['Finding ID','Action ID','Time','Reviewer ID','Outcome','Rationale','Review token','Human conclusion','Review signature'],verifications)
    stream=BytesIO();workbook.save(stream);return stream.getvalue()


def _unicode_font():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    configured=os.getenv('REMEDIATION_PDF_FONT')
    candidates=[configured] if configured else [r'C:\Windows\Fonts\arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf']
    path=next((Path(p) for p in candidates if p and Path(p).is_file()),None)
    if path is None:raise ValueError('Thiếu font Unicode cho PDF. Cấu hình REMEDIATION_PDF_FONT tới Arial/DejaVuSans có tiếng Việt.')
    name='Remediation-'+hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:12]
    with _font_lock:
        if name not in pdfmetrics.getRegisteredFontNames():
            font=TTFont(name,str(path))
            if any(ord(c) not in font.face.charToGlyph for c in 'Đđăâêôơưấếộựỹ'):
                raise ValueError('Font PDF đã cấu hình không có đủ ký tự tiếng Việt.')
            pdfmetrics.registerFont(font)
    return name


def pdf_report(report):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
    font=_unicode_font();stream=BytesIO()
    styles={
        'title':ParagraphStyle('title',fontName=font,fontSize=20,leading=26,textColor=colors.HexColor('#065F58'),spaceAfter=16),
        'heading':ParagraphStyle('heading',fontName=font,fontSize=13,leading=18,textColor=colors.HexColor('#103547'),spaceBefore=14,spaceAfter=7,keepWithNext=True),
        'body':ParagraphStyle('body',fontName=font,fontSize=10,leading=15,spaceAfter=7,splitLongWords=True),
        'small':ParagraphStyle('small',fontName=font,fontSize=8,leading=11,textColor=colors.HexColor('#526575'),spaceAfter=6,splitLongWords=True),
    }
    flow=[]
    def paragraph(value,style='body'):
        value=text(value)
        # Chunking also handles unexpectedly large legacy fields without a single oversized flowable.
        for start in range(0,max(1,len(value)),2500):
            flow.append(Paragraph(escape(value[start:start+2500]).replace('\n','<br/>'),styles[style]))
    paragraph('Báo cáo đánh giá và khắc phục','title');paragraph(DISCLAIMER,'small')
    paragraph('Đợt: '+text(report['assessment_id']),'small')
    paragraph(f"Hành động: {report['total_actions']} | Quá hạn cần rà: {report['overdue']}")
    for context in report.get('context',[]):
        doc=context['document'];paragraph(doc.get('name','Doanh nghiệp'),'heading')
        paragraph('Phạm vi ISMS: '+text(doc.get('isms_scope')))
    for row in report['records']:
        doc=row['document'];baseline=doc['baseline']
        paragraph(doc['control_id']+' — '+doc['description'],'heading')
        paragraph('Vị trí: '+text(doc['location']))
        paragraph('Nguyên nhân cần xác nhận: '+text(doc['root_cause']))
        paragraph('Rủi ro đề nghị: '+text(doc.get('risk','unconfirmed')))
        paragraph('Trước khắc phục: '+text(baseline['conclusion'])+'\nMáy hiện tại: '+text(row.get('current_conclusion'))+
                    '\nThẩm định hiện hành: '+text(row.get('current_human_conclusion') or 'Chưa có'))
        paragraph('Baseline: '+text(baseline['review_token']),'small')
        for criterion in baseline.get('criteria',[]):paragraph('Tiêu chí: '+text(criterion),'small')
        for evidence in baseline['evidence']:paragraph('Nguồn ban đầu: '+text(evidence.get('evidence_id'))+' | '+text(evidence.get('sha256_hash')),'small')
        if row.get('verification_stale'):paragraph('CẢNH BÁO: xác minh đã cũ, cần rà trên nguồn và thẩm định hiện hành.')
        for a in doc['actions']:
            paragraph(a['title']+' — '+a['state'],'heading')
            paragraph('Bộ phận: '+text(a.get('department'))+' | Người thực hiện: '+text(a.get('assignee') or 'Chưa giao')+
                ' | Hạn: '+text(a.get('due_date') or 'Chưa ghi')+' | Ưu tiên: '+text(a.get('priority')))
            paragraph(a['steps']);paragraph('Điều kiện nghiệm thu: '+a['acceptance'])
            paragraph('Nguồn lực: '+text(a.get('resources')))
            for index,t in enumerate(a['tasks'],1):paragraph(f"{index}. [{'x' if t['done'] else ' '}] "+t['title'])
            for e in a['evidence']:paragraph('Nguồn sau: '+text(e.get('evidence_id'))+' | '+text(e.get('sha256_hash')),'small')
            for v in a['verifications']:
                paragraph('Xác minh: '+text(v.get('at'))+' | '+text(v.get('reviewer_id'))+' | '+text(v['outcome']))
                paragraph(v['note']);paragraph('Token xác minh: '+text(v.get('review_token')),'small')
        flow.append(Spacer(1,8))
    def footer(canvas,document):
        canvas.saveState();canvas.setFont(font,8);canvas.setFillColor(colors.HexColor('#526575'))
        canvas.drawString(42,25,'Hỗ trợ đánh giá / khắc phục — không phải chứng nhận ISO')
        canvas.drawRightString(A4[0]-42,25,str(document.page));canvas.restoreState()
    SimpleDocTemplate(stream,pagesize=A4,rightMargin=42,leftMargin=42,topMargin=42,bottomMargin=45,
        title='Báo cáo trước và sau khắc phục',author='ISO 27001 project').build(flow,onFirstPage=footer,onLaterPages=footer)
    return stream.getvalue()
