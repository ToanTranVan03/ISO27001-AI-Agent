"""Separate development workbench; never writes formal evidence or approvals."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import threading
from uuid import UUID,uuid4
from fastapi import APIRouter,Depends,HTTPException
from backend.team_api import require_user,require_campaign
from agent_core.development_lab import build_bundle,evaluate,compare_designer,designer_reference,reference_hash

router=APIRouter(prefix='/api/assessments/{assessment_id}/enterprise/development-lab',tags=['Development scenarios'])
STORE=Path(__file__).resolve().parents[1]/'work/development-lab'
pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='document-development-lab')
lock=threading.RLock();active={}


def directory(aid):return STORE/str(UUID(str(aid)))


def save(path,doc):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(path)


def worker(path,doc,bundle):
    try:
        for case in bundle['cases']:
            result=evaluate(case,doc['model'])
            with lock:
                doc['results'].append(result);doc['updated_at']=datetime.now(timezone.utc).isoformat();save(path,doc)
        with lock:
            doc['designer_comparison']=compare_designer(doc['results'],doc.get('designer_reference_snapshot'));doc['state']='COMPLETED';save(path,doc)
    except Exception as exc:
        with lock:doc.update(state='FAILED',error=str(exc)[:500]);save(path,doc)
    finally:
        with lock:active.pop(doc['assessment_id'],None)


@router.get('')
def get_lab(assessment_id:UUID,user=Depends(require_user)):
    require_campaign(assessment_id,user)
    bundle=build_bundle()
    with lock:
        files=list(directory(assessment_id).glob('*.json'))
        reports=[json.loads(p.read_text(encoding='utf-8')) for p in files]
        for report in reports:
            if report['state']=='RUNNING' and str(assessment_id) not in active:report['state']='INTERRUPTED'
        reports.sort(key=lambda r:r['created_at'],reverse=True)
    return dict(bundle=bundle,runs=reports,can_start=user.get('role')=='admin')


@router.get('/runs/{run_id}/analysis')
def analyze_lab(assessment_id:UUID,run_id:UUID,user=Depends(require_user)):
    require_campaign(assessment_id,user)
    from agent_core.development_lab_audit import audit
    with lock:
        path=directory(assessment_id)/(str(run_id)+'.json')
        if not path.exists():raise HTTPException(404,'Không tìm thấy lượt lab trong đợt.')
        report=json.loads(path.read_text(encoding='utf-8'))
        if report['state']!='COMPLETED':raise HTTPException(409,'Chờ lượt lab hoàn tất trước khi phân tích.')
        try:return audit(report)
        except ValueError as exc:raise HTTPException(409,str(exc)) from exc


@router.post('/runs',status_code=202)
def start_lab(assessment_id:UUID,user=Depends(require_user)):
    require_campaign(assessment_id,user)
    if user.get('role')!='admin':raise HTTPException(403,'Chỉ admin chạy bộ phát triển; đây không phải chấm thật.')
    aid=str(assessment_id);bundle=build_bundle()
    with lock:
        if aid in active:raise HTTPException(409,'Bộ phát triển đang chạy; theo dõi tiến độ đã lưu.')
        rid=str(uuid4());path=directory(aid)/(rid+'.json')
        doc=dict(run_id=rid,assessment_id=aid,created_at=datetime.now(timezone.utc).isoformat(),
            state='RUNNING',model=os.getenv('OLLAMA_MODEL','qwen2.5:7b'),bundle_sha256=bundle['sha256'],
            is_synthetic=True,independent_validation=False,professional_approval=False,results=[],total=len(bundle['cases']))
        reference=designer_reference()
        doc.update(designer_reference_snapshot=reference,designer_reference_sha256=reference_hash(reference))
        save(path,doc);active[aid]=rid
        try:pool.submit(worker,path,doc,bundle)
        except RuntimeError:
            active.pop(aid,None);doc['state']='FAILED';save(path,doc);raise HTTPException(503,'Worker chưa sẵn sàng.')
    return doc
