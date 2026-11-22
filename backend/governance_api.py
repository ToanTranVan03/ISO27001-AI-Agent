"""Versioned risk and source-backed requirement registers; not automatic SoA decisions."""
from uuid import UUID,uuid4
from typing import Literal
from datetime import date
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,ConfigDict,Field,model_validator
from psycopg.types.json import Jsonb
from backend.database import get_connection
from backend.team_api import require_user,require_campaign
from backend.remediation_api import membership
from backend.remediation import now
from evidence_collectors.control_packages import controls

router=APIRouter(prefix='/api/assessments/{assessment_id}/governance',tags=['Risks and requirements'])


def initialize():
    with get_connection() as con,con.cursor() as cur:
        cur.execute('''CREATE TABLE IF NOT EXISTS governance_records (
            assessment_id UUID NOT NULL REFERENCES assessment_campaigns(assessment_id),
            record_id UUID NOT NULL,kind TEXT NOT NULL CHECK(kind IN ('risk','requirement')),
            version INTEGER NOT NULL DEFAULT 1,document JSONB NOT NULL,
            PRIMARY KEY(assessment_id,record_id))''')


class Risk(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    title:str=Field(min_length=5,max_length=300)
    asset:str=Field(min_length=2,max_length=500)
    scenario:str=Field(min_length=10,max_length=3000)
    rationale:str=Field(min_length=10,max_length=3000)
    likelihood:int=Field(ge=1,le=5,strict=True)
    impact:int=Field(ge=1,le=5,strict=True)
    owner_id:UUID
    treatment:Literal['mitigate','avoid','transfer','accept']
    treatment_plan:str=Field(min_length=10,max_length=4000)
    due_date:date
    control_ids:list[str]=Field(min_length=1,max_length=56)
    finding_ids:list[UUID]=Field(default_factory=list,max_length=100)
    residual_likelihood:int|None=Field(default=None,ge=1,le=5,strict=True)
    residual_impact:int|None=Field(default=None,ge=1,le=5,strict=True)
    @model_validator(mode='after')
    def paired(self):
        if (self.residual_likelihood is None)!=(self.residual_impact is None):raise ValueError('Cần cả hai giá trị rủi ro còn lại hoặc để cả hai chưa rõ.')
        return self


class Requirement(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    reference:str=Field(min_length=2,max_length=200)
    title:str=Field(min_length=5,max_length=300)
    description:str=Field(min_length=10,max_length=4000)
    category:Literal['standard','legal','contract','internal','risk_control']
    source_reference:str=Field(min_length=10,max_length=2000)
    source_version:str=Field(min_length=2,max_length=200)
    rights_basis:str=Field(min_length=10,max_length=1000)
    applicability_scope:str=Field(min_length=10,max_length=2000)
    control_ids:list[str]=Field(min_length=1,max_length=56)


class Save(BaseModel):
    model_config=ConfigDict(extra='forbid')
    expected_version:int=Field(ge=0)
    kind:Literal['risk','requirement']
    data:Risk|Requirement
    note:str=Field(min_length=10,max_length=2000)
    @model_validator(mode='after')
    def match_kind(self):
        if (self.kind=='risk')!=isinstance(self.data,Risk):raise ValueError('Loại hồ sơ và dữ liệu không khớp.')
        return self


class Review(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    expected_version:int=Field(ge=1)
    decision:Literal['acknowledge','reject']
    note:str=Field(min_length=30,max_length=3000)


def score(document):
    if 'likelihood' not in document:return document
    result=dict(document)
    result['inherent_score']=document['likelihood']*document['impact']
    result['residual_score']=document['residual_likelihood']*document['residual_impact'] if document.get('residual_likelihood') is not None and document.get('residual_impact') is not None else None
    result['scoring_method']='PROJECT_5x5_NOT_AN_ISO_MANDATE'
    return result


def validate_links(cur,aid,data):
    ids=data['control_ids'];catalog={c['control_id'] for c in controls()}
    if len(ids)!=len(set(ids)) or not set(ids)<=catalog:raise HTTPException(422,'Liên kết control phải duy nhất và nằm trong phạm vi 56 hiện có.')
    if data.get('owner_id'):
        cur.execute('SELECT 1 FROM assessment_members WHERE assessment_id=%s AND user_id=%s',(aid,data['owner_id']))
        if not cur.fetchone():raise HTTPException(422,'Người chịu trách nhiệm không thuộc đợt.')
    for fid in data.get('finding_ids',[]):
        cur.execute('SELECT 1 FROM remediation_records WHERE assessment_id=%s AND record_id=%s AND kind=%s',(aid,fid,'finding'))
        if not cur.fetchone():raise HTTPException(422,'Phát hiện liên kết không thuộc đợt.')


@router.get('')
def listing(assessment_id:UUID,user=Depends(require_user)):
    role=membership(assessment_id,user)
    with get_connection() as con,con.cursor() as cur:
        cur.execute('SELECT record_id,kind,version,document FROM governance_records WHERE assessment_id=%s ORDER BY record_id',(assessment_id,))
        rows=[dict(record_id=str(r[0]),kind=r[1],version=r[2],document=score(r[3])) for r in cur.fetchall()]
    if role=='operator':rows=[r for r in rows if r['kind']=='requirement' or str(r['document'].get('owner_id'))==str(user['user_id'])]
    return dict(records=rows,role=role,user_id=user['user_id'],
        note='Điểm 5×5 là phương pháp đề xuất của dự án, không phải ngưỡng ISO. Ghi nhận yêu cầu/rủi ro không tự áp dụng hoặc loại trừ control, không phê duyệt SoA.')


@router.put('/records/{record_id}')
def save(assessment_id:UUID,record_id:UUID,req:Save,user=Depends(require_user)):
    role=membership(assessment_id,user)
    if role not in ('consultant','business_admin'):raise HTTPException(403,'Chỉ tư vấn/quản trị doanh nghiệp quản lý sổ.')
    data=req.data.model_dump(mode='json')
    with get_connection() as con,con.cursor() as cur:
        cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('register:'+str(assessment_id)+str(record_id),))
        cur.execute('SELECT version,kind,document FROM governance_records WHERE assessment_id=%s AND record_id=%s FOR UPDATE',(assessment_id,record_id))
        old=cur.fetchone()
        if req.expected_version!=(old[0] if old else 0):raise HTTPException(409,'Hồ sơ đã đổi; tải lại phiên bản hiện hành.')
        if old and old[1]!=req.kind:raise HTTPException(422,'Không đổi loại hồ sơ đã lưu.')
        validate_links(cur,assessment_id,data)
        cur.execute('SELECT version FROM remediation_records WHERE assessment_id=%s AND kind=%s',(assessment_id,'context'))
        context=cur.fetchone()
        if not context:raise HTTPException(409,'Lưu bối cảnh/phạm vi ISMS trước khi lập sổ.')
        history=old[2].get('history',[]) if old else []
        history=history+[dict(at=now(),actor=user['user_id'],event='edit' if old else 'create',note=req.note,
            before={k:v for k,v in old[2].items() if k!='history'} if old else None)]
        document=dict(**data,status='DRAFT',last_editor=user['user_id'],context_version=context[0],history=history,
            independently_verified=False,affects_soa_automatically=False)
        if old:cur.execute('UPDATE governance_records SET version=version+1,document=%s WHERE assessment_id=%s AND record_id=%s',(Jsonb(document),assessment_id,record_id))
        else:cur.execute('INSERT INTO governance_records VALUES(%s,%s,%s,1,%s)',(assessment_id,record_id,req.kind,Jsonb(document)))
    return dict(record_id=str(record_id),version=(old[0]+1 if old else 1),document=score(document))


@router.post('/records/{record_id}/review')
def review(assessment_id:UUID,record_id:UUID,req:Review,user=Depends(require_user)):
    role=membership(assessment_id,user)
    if role not in ('consultant','verifier'):raise HTTPException(403,'Cần tư vấn/người xác minh rà hồ sơ.')
    with get_connection() as con,con.cursor() as cur:
        cur.execute('SELECT version,kind,document FROM governance_records WHERE assessment_id=%s AND record_id=%s FOR UPDATE',(assessment_id,record_id))
        row=cur.fetchone()
        if not row:raise HTTPException(404,'Không có hồ sơ trong đợt này.')
        version,kind,doc=row
        if version!=req.expected_version:raise HTTPException(409,'Hồ sơ đã đổi.')
        if str(doc['last_editor'])==str(user['user_id']):raise HTTPException(403,'Cần người khác rà nội dung đã nhập/sửa.')
        cur.execute('SELECT version FROM remediation_records WHERE assessment_id=%s AND kind=%s',(assessment_id,'context'))
        context=cur.fetchone()
        if not context or context[0]!=doc['context_version']:raise HTTPException(409,'Phạm vi/bối cảnh đã đổi; rà và lưu lại hồ sơ trước.')
        if kind=='risk' and req.decision=='acknowledge' and doc.get('residual_likelihood') is None:
            raise HTTPException(422,'Cần ghi cả ước lượng rủi ro còn lại và căn cứ trước khi xác nhận xử lý.')
        doc['status']='ACKNOWLEDGED' if req.decision=='acknowledge' else 'REJECTED'
        doc['history'].append(dict(event=req.decision,actor=user['user_id'],at=now(),note=req.note))
        cur.execute('UPDATE governance_records SET version=version+1,document=%s WHERE assessment_id=%s AND record_id=%s',(Jsonb(doc),assessment_id,record_id))
    return dict(record_id=str(record_id),version=version+1,document=score(doc))
