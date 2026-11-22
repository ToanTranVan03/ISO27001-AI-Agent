"""Recipient-bound in-app inbox with optional env-configured SMTP; no hardcoded credentials or compliance changes."""
import logging
import os
import smtplib
import threading
from datetime import date,datetime,timedelta
from email.message import EmailMessage
from uuid import UUID,uuid4
from zoneinfo import ZoneInfo
from fastapi import APIRouter,Depends,HTTPException
from psycopg.types.json import Jsonb
from backend.database import get_connection
from backend.team_api import require_user,require_campaign

router=APIRouter(prefix='/api/assessments/{assessment_id}/remediation/notifications',tags=['Remediation notifications'])
logger=logging.getLogger(__name__)


def smtp_configured():
    return os.getenv('REMEDIATION_SMTP_ENABLED')=='1' and bool(os.getenv('REMEDIATION_SMTP_HOST') and os.getenv('REMEDIATION_SMTP_FROM'))


def send_optional_email(cur,recipient,body):
    """Send email only when REMEDIATION_SMTP_ENABLED=1 and SMTP env vars are provided; never hardcode credentials."""
    if not smtp_configured():return False
    cur.execute('SELECT email FROM team_users WHERE user_id=%s',(recipient,))
    row=cur.fetchone()
    if not row or not row[0]:return False
    msg=EmailMessage()
    msg['Subject']=f"[ISO 27001 Remediation] {body.get('title','Thông báo công việc')}"
    msg['From']=os.environ['REMEDIATION_SMTP_FROM']
    msg['To']=row[0]
    msg.set_content(f"{body.get('title','')}\nControl: {body.get('control_id','')}\nHành động: {body.get('action_title','')}\nTrạng thái: {body.get('state','')}\n{body.get('note','')}")
    host=os.environ['REMEDIATION_SMTP_HOST']
    port=int(os.getenv('REMEDIATION_SMTP_PORT','587'))
    user=os.getenv('REMEDIATION_SMTP_USER')
    password=os.getenv('REMEDIATION_SMTP_PASSWORD')
    use_tls=os.getenv('REMEDIATION_SMTP_TLS','1')!='0'
    try:
        with smtplib.SMTP(host,port,timeout=10) as client:
            if use_tls:client.starttls()
            if user and password:client.login(user,password)
            client.send_message(msg)
        return True
    except Exception:
        logger.exception('Optional SMTP notification delivery failed; in-app notification preserved')
        return False


def initialize():
    with get_connection() as con,con.cursor() as cur:
        cur.execute('''CREATE TABLE IF NOT EXISTS remediation_notifications (
            notification_id UUID PRIMARY KEY,assessment_id UUID NOT NULL,user_id UUID NOT NULL,
            event_type TEXT NOT NULL,body JSONB NOT NULL,dedupe_key TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),read_at TIMESTAMPTZ,
            FOREIGN KEY(assessment_id,user_id) REFERENCES assessment_members(assessment_id,user_id) ON DELETE CASCADE,
            UNIQUE(assessment_id,user_id,dedupe_key))''')
        cur.execute('CREATE INDEX IF NOT EXISTS remediation_notifications_inbox ON remediation_notifications(assessment_id,user_id,created_at DESC)')


def enqueue(cur,aid,recipient,event_type,body,dedupe):
    """Use the caller's transaction; only current campaign members can receive."""
    if not recipient:return False
    cur.execute('''INSERT INTO remediation_notifications(notification_id,assessment_id,user_id,event_type,body,dedupe_key)
        SELECT %s,m.assessment_id,m.user_id,%s,%s,%s FROM assessment_members m
        WHERE m.assessment_id=%s AND m.user_id=%s
        ON CONFLICT(assessment_id,user_id,dedupe_key) DO NOTHING RETURNING notification_id''',
        (str(uuid4()),event_type,Jsonb(body),dedupe,aid,recipient))
    inserted=cur.fetchone() is not None
    if inserted and smtp_configured():send_optional_email(cur,recipient,body)
    return inserted


def notify_event(cur,aid,doc,action_id,command,actor,version):
    action=next((a for a in doc['actions'] if a['action_id']==str(action_id)),None)
    if not action:return 0
    titles={'approve':'Bạn được giao công việc khắc phục','assign_task':'Bạn được phân công bước công việc khắc phục',
            'submit':'Có công việc chờ xác minh','attach':'Có bằng chứng sau khắc phục mới',
            'verify':'Có kết quả xác minh khắc phục','return':'Công việc cần bổ sung và gửi lại',
            'close':'Hành động đã được đóng'}
    if command not in titles:return 0
    if command=='verify' and action.get('verifications'):
        outcome=action['verifications'][-1]['outcome']
        titles['verify']={'accepted':'Hành động đã được xác minh đạt','partial':'Xác minh một phần — cần làm lại','rework':'Xác minh chưa đạt — cần làm lại','more_information':'Xác minh yêu cầu bổ sung'}[outcome]
    if command in ('submit','attach'):
        cur.execute('''SELECT m.user_id FROM assessment_members m JOIN team_users u ON u.user_id=m.user_id
            LEFT JOIN remediation_roles r ON r.assessment_id=m.assessment_id AND r.user_id=m.user_id
            WHERE m.assessment_id=%s AND COALESCE(r.role,CASE WHEN u.role='admin' THEN 'consultant' ELSE 'operator' END)
            IN ('consultant','verifier')''',(aid,))
        recipients=[str(row[0]) for row in cur.fetchall()]
    elif command=='assign_task':
        step_assignees=[t.get('assignee') for t in action.get('tasks',[]) if t.get('assignee')]
        recipients=[action.get('assignee'),*step_assignees]
    else:recipients=[action.get('assignee'),*action.get('collaborator_ids',[])]
    cur.execute("SELECT user_id FROM remediation_roles WHERE assessment_id=%s AND role='business_admin'",(aid,))
    recipients.extend(str(row[0]) for row in cur.fetchall())
    body=dict(title=titles[command],action_title=action['title'],finding_id=doc['finding_id'],
        action_id=str(action_id),control_id=doc['control_id'],state=action['state'],
        note='Thông báo quy trình, không phải kết luận tuân thủ hoặc chứng nhận ISO.')
    return sum(enqueue(cur,aid,r,command,body,f'event:{doc["finding_id"]}:{action_id}:{version}:{command}')
               for r in set(recipients) if r and str(r)!=str(actor))


def due_items(doc,today=None):
    """Pure reminder policy; returned items never alter tasks or conclusions."""
    today=today or datetime.now(ZoneInfo('Asia/Bangkok')).date()
    items=[]
    for action in doc.get('actions',[]):
        if action.get('state') in ('PENDING_APPROVAL','VERIFIED','CLOSED') or not action.get('assignee'):continue
        try:due=date.fromisoformat(action.get('due_date') or '')
        except (TypeError,ValueError):continue
        if due>today+timedelta(days=3):continue
        event='overdue' if due<today else 'due_soon'
        items.append(dict(recipient=action['assignee'],event_type=event,
            dedupe=f'due:{doc["finding_id"]}:{action["action_id"]}:{today.isoformat()}',
            body=dict(title='Công việc đã quá hạn — cần rà' if event=='overdue' else 'Công việc sắp đến hạn',
                finding_id=doc['finding_id'],action_id=action['action_id'],control_id=doc['control_id'],
                action_title=action['title'],due_date=due.isoformat(),
                note='Nhắc hạn không tự xác nhận công việc chưa làm/đã làm, không tự gia hạn hoặc đổi kết luận.')))
    return items


def scan_due(today=None):
    inserted=0
    with get_connection() as con,con.cursor() as cur:
        cur.execute("SELECT assessment_id,document FROM remediation_records WHERE kind='finding'")
        rows=cur.fetchall()
        for aid,doc in rows:
            cur.execute("SELECT user_id FROM remediation_roles WHERE assessment_id=%s AND role='business_admin'",(aid,))
            managers=[str(r[0]) for r in cur.fetchall()]
            for item in due_items(doc,today):
                action=next(a for a in doc['actions'] if a['action_id']==item['body']['action_id'])
                for recipient in set([item['recipient'],*managers,*action.get('collaborator_ids',[])]):
                    inserted+=int(enqueue(cur,aid,recipient,item['event_type'],item['body'],item['dedupe']))
    return inserted


def start(interval_seconds=300):
    """Return a shutdown callback; workers never send messages outside the app."""
    if interval_seconds<1:raise ValueError('Reminder interval must be at least one second')
    stopped=threading.Event()
    def loop():
        while not stopped.is_set():
            try:scan_due()
            except Exception:logger.exception('Remediation due reminder scan failed; workflow records were not modified')
            if stopped.wait(interval_seconds):break
    thread=threading.Thread(target=loop,name='remediation-due-reminders',daemon=True)
    thread.start()
    def stop():
        stopped.set();thread.join(timeout=2)
    return stop


@router.get('')
def inbox(assessment_id:UUID,unread_only:bool=False,user=Depends(require_user)):
    require_campaign(assessment_id,user)
    with get_connection() as con,con.cursor() as cur:
        cur.execute('''SELECT notification_id,event_type,body,created_at,read_at FROM remediation_notifications
            WHERE assessment_id=%s AND user_id=%s AND (%s=FALSE OR read_at IS NULL)
            ORDER BY created_at DESC,notification_id LIMIT 200''',(assessment_id,user['user_id'],unread_only))
        items=[dict(notification_id=str(r[0]),event_type=r[1],body=r[2],created_at=r[3].isoformat(),
                    read_at=r[4].isoformat() if r[4] else None) for r in cur.fetchall()]
        cur.execute('SELECT count(*) FROM remediation_notifications WHERE assessment_id=%s AND user_id=%s AND read_at IS NULL',(assessment_id,user['user_id']))
        unread=cur.fetchone()[0]
    return dict(items=items,unread_count=unread,limit=200,
        note='Hộp thư trong ứng dụng. Nhắc hạn quét mỗi 5 phút; không gửi email và không thay kết luận ISO.')


@router.post('/{notification_id}/read')
def mark_read(assessment_id:UUID,notification_id:UUID,user=Depends(require_user)):
    require_campaign(assessment_id,user)
    with get_connection() as con,con.cursor() as cur:
        cur.execute('''UPDATE remediation_notifications SET read_at=COALESCE(read_at,NOW())
            WHERE assessment_id=%s AND user_id=%s AND notification_id=%s RETURNING read_at''',
            (assessment_id,user['user_id'],notification_id))
        row=cur.fetchone()
    if not row:raise HTTPException(404,'Không có thông báo thuộc tài khoản/đợt này.')
    return dict(notification_id=str(notification_id),read_at=row[0].isoformat())
