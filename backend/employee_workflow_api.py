"""Campaign-scoped employee workflows; never automatically edit compliance or inventory."""
from datetime import datetime,timezone
from typing import Literal
from uuid import UUID,uuid4
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,ConfigDict,Field,StrictBool
from psycopg.types.json import Jsonb
from backend.database import get_connection
from backend.team_api import require_user
from backend.remediation_api import membership
from backend import employee_workflow as engine

router=APIRouter(prefix='/api/assessments/{assessment_id}/employee-workflows',tags=['Employee participation'])


def initialize():
    with get_connection() as con,con.cursor() as cur:
        cur.execute('''CREATE TABLE IF NOT EXISTS employee_identity_bindings (
            assessment_id UUID NOT NULL,user_id UUID NOT NULL,employee_id TEXT NOT NULL,
            PRIMARY KEY(assessment_id,user_id),UNIQUE(assessment_id,employee_id),
            FOREIGN KEY(assessment_id,user_id) REFERENCES assessment_members(assessment_id,user_id),
            FOREIGN KEY(assessment_id,employee_id) REFERENCES enterprise_sim_people(assessment_id,employee_id))''')
        cur.execute('''CREATE TABLE IF NOT EXISTS employee_workflow_requests (
            request_id UUID PRIMARY KEY,assessment_id UUID NOT NULL REFERENCES assessment_campaigns(assessment_id),
            version INTEGER NOT NULL DEFAULT 1,document JSONB NOT NULL,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())''')


class Input(BaseModel):model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
class Binding(Input):
    user_id:UUID
    employee_id:str=Field(pattern=r'^EMP-\d{3}$')
    note:str=Field(min_length=10,max_length=1000)
class Create(Input):
    kind:Literal['training','nda','mfa','asset_return']
    employee_id:str=Field(pattern=r'^EMP-\d{3}$')
    title:str=Field(min_length=5,max_length=200)
    content:str=Field(min_length=30,max_length=4000)
    policy_version:str=Field(min_length=1,max_length=100)
    target_id:str=Field(default='',max_length=150)
class Event(Input):
    expected_version:int=Field(ge=1)
    command:Literal['respond','observe','review','reopen']
    note:str=Field(min_length=10,max_length=2000)
    answer:str=Field(default='',max_length=3000)
    document_sha256:str|None=None
    acknowledged:StrictBool|None=None
    enrolled:StrictBool|None=None
    enforced:StrictBool|None=None
    receipt_reference:str=Field(default='',max_length=300)
    asset_id:str=Field(default='',max_length=150)
    evidence_ids:list[str]=Field(default_factory=list,max_length=20)
    outcome:Literal['accepted','rework','more_information']|None=None


def visible(doc,user,role):
    if role=='operator' and str(doc['user_id'])!=str(user['user_id']):raise HTTPException(403,'Yêu cầu thuộc nhân viên khác.')


@router.put('/bindings')
def bind(assessment_id:UUID,req:Binding,user=Depends(require_user)):
    membership(assessment_id,user)
    if user['role']!='admin':raise HTTPException(403,'Chỉ quản trị hệ thống gán danh tính; nhân viên không tự nhận danh tính khác.')
    with get_connection() as con,con.cursor() as cur:
        cur.execute('SELECT 1 FROM assessment_members WHERE assessment_id=%s AND user_id=%s',(assessment_id,req.user_id))
        if not cur.fetchone():raise HTTPException(422,'Tài khoản không thuộc đợt.')
        cur.execute('SELECT 1 FROM enterprise_sim_people WHERE assessment_id=%s AND employee_id=%s',(assessment_id,req.employee_id))
        if not cur.fetchone():raise HTTPException(422,'Nhân viên không thuộc đợt.')
        cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('employee-bind:'+str(assessment_id),))
        cur.execute('SELECT user_id,employee_id FROM employee_identity_bindings WHERE assessment_id=%s AND (user_id=%s OR employee_id=%s)',(assessment_id,req.user_id,req.employee_id));existing=cur.fetchall()
        if existing and any(str(r[0])!=str(req.user_id) or r[1]!=req.employee_id for r in existing):raise HTTPException(409,'Danh tính đã gán; không tự đổi hoặc chuyển các yêu cầu cũ.')
        cur.execute('INSERT INTO employee_identity_bindings VALUES(%s,%s,%s) ON CONFLICT DO NOTHING',(assessment_id,req.user_id,req.employee_id))
        cur.execute("INSERT INTO assessment_events(assessment_id,user_id,event_type,details) VALUES(%s,%s,'employee_identity_bound',%s)",(assessment_id,user['user_id'],Jsonb(req.model_dump(mode='json'))))
    return dict(bound=True,employee_id=req.employee_id,user_id=str(req.user_id))


@router.get('')
def board(assessment_id:UUID,user=Depends(require_user)):
    role=membership(assessment_id,user)
    with get_connection() as con,con.cursor() as cur:
        cur.execute('SELECT user_id,employee_id FROM employee_identity_bindings WHERE assessment_id=%s AND (%s OR user_id=%s)',(assessment_id,role!='operator',user['user_id']))
        bindings=[dict(user_id=str(r[0]),employee_id=r[1]) for r in cur.fetchall()]
        cur.execute("SELECT request_id,version,document FROM employee_workflow_requests WHERE assessment_id=%s AND (%s OR document->>'user_id'=%s) ORDER BY created_at DESC",(assessment_id,role!='operator',str(user['user_id'])))
        rows=[dict(request_id=str(r[0]),version=r[1],document=r[2]) for r in cur.fetchall()]
    if any(r['document']['state']=='REVIEWED' for r in rows):
        from backend.enterprise_api import scope56
        scope=scope56(assessment_id,user);controls={c['control_id']:c for c in scope['controls']}
        for row in rows:
            doc=row['document'];review=doc['reviews'][-1] if doc['reviews'] else None;control=controls[doc['control_id']]
            sources={e['evidence_id']:e for e in control['evidence']}
            row['verification_current']=bool(doc['state']=='REVIEWED' and review and review.get('source_token')==control['review_token'] and
                all(ref['evidence_id'] in sources and sources[ref['evidence_id']]['sha256_hash']==ref['sha256'] and sources[ref['evidence_id']].get('source_quality',{}).get('usable') is not False for ref in review['evidence']))
    return dict(bindings=bindings,requests=rows,role=role,user_id=str(user['user_id']),can_bind=user['role']=='admin',can_create=role=='consultant',
        note='Phản hồi nhân viên, quan sát nguồn và thẩm định là ba bước riêng. Không tự ký NDA, hoàn thành đào tạo/MFA hoặc xác nhận đã trả thiết bị thay người thật; không tự đổi control/SoA.')


@router.post('',status_code=201)
def create(assessment_id:UUID,req:Create,user=Depends(require_user)):
    if membership(assessment_id,user)!='consultant':raise HTTPException(403,'Chỉ tư vấn giao yêu cầu có phiên bản.')
    with get_connection() as con,con.cursor() as cur:
        cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('employee-work:'+str(assessment_id)+req.employee_id+req.kind+req.target_id,))
        cur.execute('SELECT user_id FROM employee_identity_bindings WHERE assessment_id=%s AND employee_id=%s',(assessment_id,req.employee_id));binding=cur.fetchone()
        if not binding:raise HTTPException(409,'Quản trị cần gán tài khoản đúng nhân viên trước.')
        if req.kind=='mfa':
            cur.execute('SELECT 1 FROM enterprise_company_accounts WHERE assessment_id=%s AND employee_id=%s AND account_id=%s',(assessment_id,req.employee_id,req.target_id))
            if not cur.fetchone():raise HTTPException(422,'Tài khoản đích không thuộc nhân viên/đợt.')
        if req.kind=='asset_return':
            cur.execute("SELECT 1 FROM enterprise_sim_asset_people WHERE assessment_id=%s AND employee_id=%s AND asset_id=%s AND relationship='responsible_employee'",(assessment_id,req.employee_id,req.target_id))
            if not cur.fetchone():raise HTTPException(422,'Thiết bị đích không liên kết với nhân viên/đợt.')
        cur.execute("SELECT request_id,version,document FROM employee_workflow_requests WHERE assessment_id=%s AND document->>'employee_id'=%s AND document->>'kind'=%s AND document->>'target_id'=%s AND document->>'state'<>'SUPERSEDED' ORDER BY created_at DESC LIMIT 1 FOR UPDATE",(assessment_id,req.employee_id,req.kind,req.target_id))
        previous=cur.fetchone()
        if previous and previous[2]['policy_version']==req.policy_version:
            if previous[2]['document_sha256']!=engine.document_hash(req.content):raise HTTPException(409,'Nội dung đổi nhưng phiên bản chưa đổi; cần phiên bản chính sách/tài liệu mới.')
            return dict(request_id=str(previous[0]),version=previous[1],document=previous[2])
        cur.execute("SELECT 1 FROM employee_workflow_requests WHERE assessment_id=%s AND document->>'employee_id'=%s AND document->>'kind'=%s AND document->>'target_id'=%s AND document->>'policy_version'=%s LIMIT 1",(assessment_id,req.employee_id,req.kind,req.target_id,req.policy_version))
        if cur.fetchone():raise HTTPException(409,'Phiên bản này đã được thay thế; không đưa lại bản cũ thành hiện hành.')
        doc=dict(**req.model_dump(),user_id=str(binding[0]),control_id=engine.CONTROL[req.kind],state='WAITING_EMPLOYEE',document_sha256=engine.document_hash(req.content),
            created_by=str(user['user_id']),responses=[],observations=[],reviews=[],history=[],compliance_claim=False)
        rid=str(uuid4())
        if previous:
            old=previous[2];old['superseded_by']=rid;old['history'].append(dict(command='superseded',actor=str(user['user_id']),at=datetime.now(timezone.utc).isoformat(),previous_state=old['state']));old['state']='SUPERSEDED'
            cur.execute('UPDATE employee_workflow_requests SET version=version+1,document=%s WHERE assessment_id=%s AND request_id=%s',(Jsonb(old),assessment_id,previous[0]))
        cur.execute('INSERT INTO employee_workflow_requests(request_id,assessment_id,document) VALUES(%s,%s,%s)',(rid,assessment_id,Jsonb(doc)))
        from backend.remediation_notifications import enqueue
        enqueue(cur,assessment_id,str(binding[0]),'employee_request',dict(title='Có yêu cầu nhân viên cần tự thực hiện',control_id=doc['control_id'],action_title=req.title,state=doc['state'],note='Mở Doanh nghiệp → Nhân viên thực hiện; không chia sẻ tài khoản hoặc nhờ AI xác nhận thay.'),'employee-work:'+rid+':1')
    return dict(request_id=rid,version=1,document=doc)


@router.post('/{request_id}/events')
def event(assessment_id:UUID,request_id:UUID,req:Event,user=Depends(require_user)):
    role=membership(assessment_id,user)
    from backend.remediation_api import scope_control
    with get_connection() as con,con.cursor() as cur:
        cur.execute('SELECT version,document FROM employee_workflow_requests WHERE assessment_id=%s AND request_id=%s FOR UPDATE',(assessment_id,request_id));row=cur.fetchone()
        if not row:raise HTTPException(404,'Không có yêu cầu trong đợt.')
        version,doc=row;visible(doc,user,role)
        if version!=req.expected_version:raise HTTPException(409,'Yêu cầu đã đổi; tải lại trước khi nộp.')
        if req.command in ('observe','review') and doc['kind'] in ('mfa','asset_return'):
            if doc['kind']=='mfa':cur.execute('SELECT 1 FROM enterprise_company_accounts WHERE assessment_id=%s AND employee_id=%s AND account_id=%s FOR SHARE',(assessment_id,doc['employee_id'],doc['target_id']))
            else:cur.execute("SELECT 1 FROM enterprise_sim_asset_people WHERE assessment_id=%s AND employee_id=%s AND asset_id=%s AND relationship='responsible_employee' FOR SHARE",(assessment_id,doc['employee_id'],doc['target_id']))
            if not cur.fetchone():raise HTTPException(409,'Quan hệ nhân viên–tài khoản/thiết bị đã đổi; cần rà và lập yêu cầu đúng đích hiện hành.')
        if req.command=='respond' and len(req.answer.strip())<10:raise HTTPException(422,'Cần câu trả lời/căn cứ của chính nhân viên, ít nhất 10 ký tự.')
        payload=req.model_dump(mode='json')
        if req.evidence_ids:
            control,_=scope_control(assessment_id,doc['control_id'],user)
            selected={e['evidence_id']:e for e in control['evidence']}
            if len(set(req.evidence_ids))!=len(req.evidence_ids) or any(eid not in selected or selected[eid].get('source_quality',{}).get('usable') is False or selected[eid].get('is_synthetic') is True for eid in req.evidence_ids):raise HTTPException(422,'Nguồn phải đúng control/đợt, dùng được và không phải preset tự sinh.')
            payload['evidence']=[dict(evidence_id=eid,sha256=selected[eid]['sha256_hash']) for eid in req.evidence_ids]
            payload['source_token']=control['review_token']
        if req.command=='review' and req.outcome=='accepted' and doc['observations']:
            control,_=scope_control(assessment_id,doc['control_id'],user);current={e['evidence_id']:e for e in control['evidence']}
            if doc['observations'][-1].get('source_token')!=control['review_token']:raise HTTPException(409,'Nguồn/tiêu chí đã đổi sau quan sát; cần đọc lại nguồn và ghi quan sát mới.')
            if any(e['evidence_id'] not in current or current[e['evidence_id']]['sha256_hash']!=e['sha256'] or current[e['evidence_id']].get('source_quality',{}).get('usable') is False for e in doc['observations'][-1]['evidence']):raise HTTPException(409,'Nguồn quan sát đã đổi/không còn dùng được; chưa xác nhận đạt.')
        try:updated=engine.apply_event(doc,req.command,payload,user['user_id'],role,datetime.now(timezone.utc).isoformat())
        except PermissionError as exc:raise HTTPException(403,str(exc)) from exc
        except ValueError as exc:raise HTTPException(409,str(exc)) from exc
        cur.execute('UPDATE employee_workflow_requests SET version=version+1,document=%s WHERE assessment_id=%s AND request_id=%s',(Jsonb(updated),assessment_id,request_id))
        from backend.remediation_notifications import enqueue
        if req.command=='review':recipients=[doc['user_id']]
        else:
            cur.execute('''SELECT m.user_id FROM assessment_members m JOIN team_users u ON u.user_id=m.user_id
                LEFT JOIN remediation_roles r ON r.assessment_id=m.assessment_id AND r.user_id=m.user_id
                WHERE m.assessment_id=%s AND COALESCE(r.role,CASE WHEN u.role='admin' THEN 'consultant' ELSE 'operator' END) IN ('consultant','verifier')''',(assessment_id,))
            recipients=[str(r[0]) for r in cur.fetchall()]
        for recipient in recipients:
            if str(recipient)!=str(user['user_id']):enqueue(cur,assessment_id,recipient,'employee_'+req.command,dict(title='Có cập nhật yêu cầu nhân viên',control_id=doc['control_id'],action_title=doc['title'],state=updated['state'],note='Mở Doanh nghiệp → Nhân viên thực hiện; sự kiện chưa tự đổi kết luận control.'),'employee-work:'+str(request_id)+':'+str(version+1))
    return dict(request_id=str(request_id),version=version+1,document=updated)
