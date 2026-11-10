"""Assessment-bound A.8 lab runs, reviewer labels and draft SoA exports."""
import json
import threading
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from backend.team_api import require_user, require_campaign
from agent_core import a8_assessment as a8
from agent_core.a8_benchmark import score

router=APIRouter(prefix='/api/assessments/{assessment_id}/a8',tags=['A.8 compliance study'])
STORE=Path(__file__).resolve().parents[1]/'data'/'a8-study'
lock=threading.RLock()
pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='a8-study')


def folder(aid):
    return STORE/str(UUID(str(aid)))


def save(path,payload):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    temporary.replace(path)


def read(aid,rid):
    path=folder(aid)/(str(UUID(str(rid)))+'.json')
    if not path.exists():raise HTTPException(404,'Không tìm thấy lượt đánh giá trong đợt này.')
    return json.loads(path.read_text(encoding='utf-8'))


def worker(aid,rid,profile,mode,transport="files"):
    try:
        result=a8.run(profile,mode,transport)
        with lock:
            doc=read(aid,rid);doc.update(state='finished',report=result);save(folder(aid)/(rid+'.json'),doc)
    except Exception as exc:
        with lock:
            doc=read(aid,rid);doc.update(state='failed',error=type(exc).__name__);save(folder(aid)/(rid+'.json'),doc)


def runtime_status():
    try:
        result=subprocess.run(['docker','inspect','iso-a8-lab','--format','{{.State.Status}}'],capture_output=True,text=True,timeout=3)
        return 'running' if result.returncode==0 and result.stdout.strip()=='running' else 'unavailable'
    except (OSError,subprocess.SubprocessError):return 'unavailable'


class RunInput(BaseModel):
    profile: Literal['conforming','mixed','nonconforming','incomplete','stale','conflicting']='mixed'
    mode: Literal['rules','llm']='llm'
    transport: Literal['files','docker']='files'


class ReviewInput(BaseModel):
    model_config=ConfigDict(str_strip_whitespace=True,extra="forbid")
    control_id: str
    expected: Literal['Compliant','Partially Compliant','Non-Compliant','Insufficient Evidence']
    rationale: str=Field(min_length=10,max_length=2000)
    report_sha256: str=Field(min_length=64,max_length=64)


@router.get('/catalog')
def catalog(assessment_id: UUID,user=Depends(require_user)):
    require_campaign(assessment_id,user)
    path=folder(assessment_id)/'settings'/'rubric-approvals.json'
    history=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    current=next((r for r in reversed(history) if r['catalog_sha256']==a8.digest(a8.catalog())),None)
    return {'controls':a8.catalog(),'profiles':a8.PROFILES,'source_kind':'raw-config-logs-or-isolated-docker', 'rubric_approval':current,'lab_runtime':runtime_status()}


@router.get('/runs')
def runs(assessment_id: UUID,user=Depends(require_user)):
    require_campaign(assessment_id,user)
    docs=[json.loads(p.read_text(encoding='utf-8')) for p in sorted(folder(assessment_id).glob('*.json'),reverse=True)]
    return [dict(run_id=d['run_id'],state=d['state'],created_at=d['created_at'],
                 mode=d['mode'] if str(d['created_by'])==str(user['user_id']) else 'blind',
                 profile=d['profile'] if str(d['created_by'])==str(user['user_id']) else 'Ẩn hồ sơ',
                 mine=str(d['created_by'])==str(user['user_id'])) for d in docs]


@router.post('/runs',status_code=202)
def start(assessment_id: UUID,req: RunInput,user=Depends(require_user)):
    require_campaign(assessment_id,user)
    if req.transport=='docker' and runtime_status()!='running':raise HTTPException(503,'Lab Docker chưa chạy. Khởi động docker compose -f docker-compose.a8.yml up -d.')
    with lock:
        for p in folder(assessment_id).glob('*.json'):
            old=json.loads(p.read_text(encoding='utf-8'))
            if old['state']=='running':raise HTTPException(409,'Đợt này đang có lượt đánh giá A.8; hãy theo dõi lượt đang chạy.')
        rid=str(uuid4());aid=str(assessment_id)
        refs=json.loads((a8.LAB/'reference'/'designer_labels.json').read_text(encoding='utf-8'))
        doc=dict(run_id=rid,assessment_id=aid,profile=req.profile,mode=req.mode,state='running',
                 created_at=datetime.now(timezone.utc).isoformat(),created_by=user['user_id'],reviews=[],transport=req.transport,review_protocol='blind-v2',designer_reference=refs,reference_sha256=a8.digest(refs))
        save(folder(aid)/(rid+'.json'),doc)
        try:pool.submit(worker,aid,rid,req.profile,req.mode,req.transport)
        except RuntimeError:
            doc.update(state='failed',error='Worker unavailable');save(folder(aid)/(rid+'.json'),doc)
            raise HTTPException(503,'Không khởi động được worker.')
    return doc


@router.get('/runs/{run_id}')
def result(assessment_id: UUID,run_id: UUID,user=Depends(require_user)):
    require_campaign(assessment_id,user)
    doc=read(assessment_id,run_id)
    if doc.get('report'):
        report=doc['report']
        owner=str(doc['created_by'])==str(user['user_id'])
        mine=[r for r in doc['reviews'] if str(r.get('reviewer_id'))==str(user['user_id'])]
        submitted={r['control_id'] for r in mine}
        if not owner and len(submitted)<len(report['records']):
            return dict(run_id=doc['run_id'],state=doc['state'],mode='blind',profile='Ẩn hồ sơ',
                blind=True,can_review=doc.get('review_protocol')=='blind-v2',
                report_sha256=report['sha256'],submitted_controls=sorted(submitted),
                evidence_pack=[dict(control_id=r['control_id'],name=r['name'],criteria_checks=r['criteria_checks'],criteria_details=r.get('criteria_details',[]),
                  evidence={k:v for k,v in r['evidence'].items() if k!='facts'}) for r in report['records']])

        labels=doc.get('designer_reference') or json.loads((a8.LAB/'reference'/'designer_labels.json').read_text(encoding='utf-8'))
        # Only most recent review per control by a different actor is scored.
        latest={r['case_id']:r for r in (doc['reviews'] if owner else mine)}
        doc['designer_comparison']=score([report],labels)
        doc['human_comparison']=score([report],list(latest.values()))
        doc['reviewer_comparisons']={str(uid):score([report],[r for r in doc['reviews'] if r.get('reviewer_id')==uid]) for uid in {r.get('reviewer_id') for r in doc['reviews']}}
        doc['soa']=a8.soa(report)
        if doc.get('soa_approval_history'):
            approval=doc['soa_approval_history'][-1]
            doc['soa']['approval']='HUMAN_APPROVED_LIMITED_SCOPE'
            doc['soa']['human_approval']=approval
            decisions={d['control_id']:d for d in approval['decisions']}
            for entry in doc['soa']['entries']:
                d=decisions[entry['control_id']]
                entry.update(applicable=d['applicable'],inclusion_reason=d['reason'],required_action=d['treatment'],applicability_approved=True)
    if not doc.get('report') and str(doc['created_by'])!=str(user['user_id']):
        return dict(run_id=doc['run_id'],state=doc['state'],mode='blind',profile='Ẩn hồ sơ',blind=True)
    return doc


@router.post('/runs/{run_id}/reviews')
def review(assessment_id: UUID,run_id: UUID,req: ReviewInput,user=Depends(require_user)):
    require_campaign(assessment_id,user)
    with lock:
        doc=read(assessment_id,run_id)
        if doc['state']!='finished':raise HTTPException(409,'Lượt đánh giá chưa hoàn tất.')
        if str(doc['created_by'])==str(user['user_id']):raise HTTPException(409,'Cần một tài khoản người đánh giá khác người khởi chạy để đối chiếu.')
        if doc.get('review_protocol')!='blind-v2':raise HTTPException(409,'Hãy tạo lượt mới cho giao thức đánh giá mù.')
        if req.report_sha256!=doc['report']['sha256']:raise HTTPException(409,'Bằng chứng đã thay đổi; tải lại gói chấm.')
        if any(r['control_id']==req.control_id and str(r['reviewer_id'])==str(user['user_id']) for r in doc['reviews']):raise HTTPException(409,'Nhãn đã nộp được khóa để bảo đảm đánh giá mù.')
        record=next((r for r in doc['report']['records'] if r['control_id']==req.control_id),None)
        if not record:raise HTTPException(404,'Không thuộc phạm vi lượt này.')
        doc['reviews'].append(dict(case_id=record['case_id'],control_id=req.control_id,expected=req.expected,
            rationale=req.rationale,reviewer_id=user['user_id'],label_origin='human-submitted-blind-v2',
            evidence_sha256=record['evidence']['source_sha256'],report_sha256=doc['report']['sha256'],
            reviewed_at=datetime.now(timezone.utc).isoformat()))
        save(folder(assessment_id)/(str(run_id)+'.json'),doc)
    return {'saved':True}


def recover_interrupted():
    # Single API process worker; restart cannot silently leave a job running forever.
    with lock:
        for path in STORE.glob('*/*.json'):
            doc=json.loads(path.read_text(encoding='utf-8'))
            if doc.get('state')=='running':
                doc.update(state='failed',error='API restarted; run interrupted')
                save(path,doc)


class ApprovalInput(BaseModel):
    model_config=ConfigDict(str_strip_whitespace=True,extra="forbid")
    note: str=Field(min_length=20,max_length=2000)


@router.post('/rubric/approval')
def approve_rubric(assessment_id: UUID,req: ApprovalInput,user=Depends(require_user)):
    require_campaign(assessment_id,user)
    if user.get('role')!='admin':raise HTTPException(403,'Chỉ người phụ trách admin ghi nhận phê duyệt phạm vi/rubric.')
    with lock:
        path=folder(assessment_id)/'settings'/'rubric-approvals.json'
        history=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
        record=dict(catalog_sha256=a8.digest(a8.catalog()),approved_by=user['user_id'],note=req.note,
                    approved_at=datetime.now(timezone.utc).isoformat())
        history.append(record);save(path,history)
    return record


class SoADecision(BaseModel):
    model_config=ConfigDict(str_strip_whitespace=True,extra="forbid")
    control_id: str
    applicable: bool
    reason: str=Field(min_length=10,max_length=1000)
    treatment: str=Field(min_length=10,max_length=1000)


class SoAApproval(BaseModel):
    model_config=ConfigDict(str_strip_whitespace=True,extra="forbid")
    decisions: list[SoADecision]=Field(min_length=18,max_length=18)
    note: str=Field(min_length=20,max_length=2000)


@router.post('/runs/{run_id}/soa-approval')
def approve_soa(assessment_id: UUID,run_id: UUID,req: SoAApproval,user=Depends(require_user)):
    require_campaign(assessment_id,user)
    if user.get('role')!='admin':raise HTTPException(403,'Chỉ người phụ trách admin phê duyệt SoA trong phạm vi.')
    with lock:
        doc=read(assessment_id,run_id)
        if doc['state']!='finished':raise HTTPException(409,'Chưa có kết quả hoàn tất.')
        ids={r['control_id'] for r in doc['report']['records']}
        if {r.control_id for r in req.decisions}!=ids:raise HTTPException(422,'Cần quyết định đủ 18 control, không trùng.')
        reviewers={r['reviewer_id'] for r in doc['reviews']}
        if not any({r['control_id'] for r in doc['reviews'] if r['reviewer_id']==uid}==ids for uid in reviewers):
            raise HTTPException(409,'Cần người đánh giá hoàn tất độc lập đủ 18 control trước khi phê duyệt.')
        path=folder(assessment_id)/'settings'/'rubric-approvals.json'
        approvals=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
        if not any(r['catalog_sha256']==doc['report']['catalog_sha256'] for r in approvals):
            raise HTTPException(409,'Rubric của lượt này chưa được phê duyệt.')
        decision=dict(approved_by=user['user_id'],approved_at=datetime.now(timezone.utc).isoformat(),
                      note=req.note,decisions=[r.model_dump() for r in req.decisions],report_sha256=doc['report']['sha256'])
        doc.setdefault('soa_approval_history',[]).append(decision)
        save(folder(assessment_id)/(str(run_id)+'.json'),doc)
    return decision


@router.get('/summary')
def summary(assessment_id: UUID,user=Depends(require_user)):
    require_campaign(assessment_id,user)
    docs=[json.loads(p.read_text(encoding='utf-8')) for p in folder(assessment_id).glob('*.json')]
    # Do not allow a summary/export to bypass the blinded result endpoint.
    visible=[]
    for doc in docs:
        if not doc.get('report'):continue
        mine={r['control_id'] for r in doc['reviews'] if str(r.get('reviewer_id'))==str(user['user_id'])}
        if str(doc['created_by'])==str(user['user_id']) or len(mine)==len(doc['report']['records']):visible.append(doc)
    labels=json.loads((a8.LAB/'reference'/'designer_labels.json').read_text(encoding='utf-8'))
    groups={}
    for doc in visible:
        report=doc['report']
        key=(report.get('rubric_version','legacy'),report.get('catalog_sha256','legacy'),report['mode'],report.get('transport','legacy'),doc.get('reference_sha256','legacy'))
        groups.setdefault(key,[]).append(doc)
    result=[]
    for (version,catalog_hash,mode,transport,reference_hash),cohort in groups.items():
        reports=[d['report'] for d in cohort]
        group_labels=cohort[0].get('designer_reference') or labels
        # Each human label must be paired to its own report, never reused across different runs.
        human=[]
        for doc in cohort:
            eligible=doc['reviews'] if str(doc['created_by'])==str(user['user_id']) else [r for r in doc['reviews'] if str(r['reviewer_id'])==str(user['user_id'])]
            for reviewer in {r['reviewer_id'] for r in eligible}:
                refs=[r for r in eligible if r['reviewer_id']==reviewer and r.get('report_sha256')==doc['report']['sha256']]
                human.append(dict(run_id=doc['run_id'],reviewer_id=reviewer,comparison=score([doc['report']],refs)))
        result.append(dict(rubric_version=version,catalog_sha256=catalog_hash,mode=mode,transport=transport,
                           reference_sha256=reference_hash,run_count=len(cohort),designer=score(reports,group_labels),human_by_run_reviewer=human))
    return {'cohorts':result,'note':'Không trộn engine, transport hoặc rubric. Human được ghép đúng run/hash; các lượt chấm mù chưa hoàn tất không lộ qua tổng hợp.'}
