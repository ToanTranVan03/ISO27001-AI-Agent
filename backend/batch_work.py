"""Bounded server-side source-only batches; durable progress, no auto approvals."""
import hashlib
import json
import logging
from uuid import uuid4
from psycopg.types.json import Jsonb
from backend.database import get_connection
from backend import shared_work,teamwork

logger=logging.getLogger(__name__)
ACTIVE=('RUNNING','STOP_REQUESTED')


def init_schema(cur):
    cur.execute('''CREATE TABLE IF NOT EXISTS assessment_batches (
        batch_id UUID PRIMARY KEY,assessment_id UUID NOT NULL REFERENCES assessment_campaigns(assessment_id),
        created_by UUID NOT NULL REFERENCES team_users(user_id),status TEXT NOT NULL,
        plan JSONB NOT NULL,results JSONB NOT NULL DEFAULT '[]'::jsonb,
        error TEXT,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())''')
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS one_active_batch_per_assessment ON assessment_batches(assessment_id) WHERE status IN ('RUNNING','STOP_REQUESTED')")
    cur.execute("UPDATE assessment_batches SET status='INTERRUPTED',error='API restarted; review persisted jobs before starting a new batch',updated_at=NOW() WHERE status IN ('RUNNING','STOP_REQUESTED')")


def source_token(control):
    from backend.database import get_rubric
    sources=[(e['evidence_id'],e.get('sha256_hash'),e.get('source_quality',{})) for e in control.get('evidence',[])
             if e.get('is_synthetic') is False or e.get('source','').startswith('a8-capture://')]
    return hashlib.sha256(json.dumps({'sources':sorted(sources,key=lambda e:e[0]),'criteria':control.get('criteria'),
        'rubric':get_rubric(control['control_id'])},sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def plan_controls(report,limit=12,force=False):
    if not 1<=limit<=56:raise ValueError('Giới hạn phải từ 1 đến 56 control.')
    candidates=[c for c in report['controls'] if shared_work.execution_mode(c)=='user_evidence_only'
                and c['shared_state']!='running' and (force or c['shared_state'] in ('stale','failed','not_started'))]
    candidates.sort(key=lambda c:(c['shared_state']!='stale',tuple(map(int,c['control_id'].split('.')[1:]))))
    return [dict(control_id=c['control_id'],source_token=source_token(c)) for c in candidates[:limit]]


def serialize(row):
    return dict(batch_id=str(row[0]),assessment_id=str(row[1]),created_by=str(row[2]),status=row[3],
                plan=row[4],results=row[5],error=row[6],created_at=row[7].isoformat(),updated_at=row[8].isoformat(),
                note='Kết quả thực thi nguồn đã thu, không phải kết luận người đánh giá hoặc phê duyệt SoA.')


def get(assessment_id,batch_id):
    with get_connection() as con,con.cursor() as cur:
        cur.execute('SELECT batch_id,assessment_id,created_by,status,plan,results,error,created_at,updated_at FROM assessment_batches WHERE assessment_id=%s AND batch_id=%s',(assessment_id,batch_id))
        row=cur.fetchone()
    return serialize(row) if row else None


def recent(assessment_id):
    with get_connection() as con,con.cursor() as cur:
        cur.execute('SELECT batch_id,assessment_id,created_by,status,plan,results,error,created_at,updated_at FROM assessment_batches WHERE assessment_id=%s ORDER BY created_at DESC LIMIT 10',(assessment_id,))
        return [serialize(row) for row in cur.fetchall()]


def create(assessment_id,user_id,limit=12,force=False):
    with get_connection() as con,con.cursor() as cur:
        cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('batch:'+assessment_id,))
        cur.execute("SELECT batch_id FROM assessment_batches WHERE assessment_id=%s AND status IN ('RUNNING','STOP_REQUESTED')",(assessment_id,))
        active=cur.fetchone()
        if active:return {'action':'following','batch_id':str(active[0])}
        plan=plan_controls(shared_work.board(assessment_id),limit,force)
        if not plan:raise ValueError('Không có control có nguồn dùng được cần chạy. Có thể chọn đánh giá lại nếu muốn kiểm tra nguồn hiện hành.')
        bid=str(uuid4())
        cur.execute("INSERT INTO assessment_batches(batch_id,assessment_id,created_by,status,plan) VALUES(%s,%s,%s,'RUNNING',%s)",(bid,assessment_id,user_id,Jsonb(plan)))
        teamwork.log_event(cur,assessment_id,None,user_id,'SOURCE_BATCH_STARTED',{'batch_id':bid,'control_ids':[c['control_id'] for c in plan],'force':force})
    return {'action':'started','batch_id':bid}


def stop(assessment_id,batch_id,user_id):
    with get_connection() as con,con.cursor() as cur:
        cur.execute("UPDATE assessment_batches SET status='STOP_REQUESTED',updated_at=NOW() WHERE assessment_id=%s AND batch_id=%s AND status='RUNNING' RETURNING batch_id",(assessment_id,batch_id))
        changed=cur.fetchone()
        if changed:teamwork.log_event(cur,assessment_id,None,user_id,'SOURCE_BATCH_STOP_REQUESTED',{'batch_id':batch_id})
    result=get(assessment_id,batch_id)
    if result is None:raise ValueError('Không có lượt chạy trong đợt này.')
    return result


def persist(assessment_id,batch_id,results,status=None,error=None):
    with get_connection() as con,con.cursor() as cur:
        # A progress update must not erase a concurrent stop request.
        cur.execute('''UPDATE assessment_batches SET results=%s,status=COALESCE(%s,status),error=%s,updated_at=NOW()
            WHERE assessment_id=%s AND batch_id=%s AND status IN ('RUNNING','STOP_REQUESTED')''',
            (Jsonb(results),status,error,assessment_id,batch_id))


def process(assessment_id,batch_id,execute):
    """One claimed worker; each control at most once, recheck sources after job claim."""
    running_job=None
    with get_connection() as lock_con,lock_con.cursor() as lock_cur:
        lock_cur.execute('SELECT pg_try_advisory_lock(hashtext(%s))',('batch-worker:'+batch_id,))
        if not lock_cur.fetchone()[0]:return
        try:
            batch=get(assessment_id,batch_id)
            if not batch or batch['status'] not in ACTIVE:return
            results=list(batch['results']);seen={r['control_id'] for r in results}
            for item in batch['plan']:
                current=get(assessment_id,batch_id)
                if not current or current['status'] not in ACTIVE:return
                if current['status']=='STOP_REQUESTED':persist(assessment_id,batch_id,results,'STOPPED');return
                cid=item['control_id']
                if cid in seen:continue
                rows=shared_work.board(assessment_id)['controls'];control=next((c for c in rows if c['control_id']==cid),None)
                if not control or shared_work.execution_mode(control)!='user_evidence_only' or source_token(control)!=item['source_token']:
                    result=dict(control_id=cid,status='SKIPPED_SOURCE_CHANGED')
                else:
                    try:job=teamwork.claim_job(assessment_id,cid,batch['created_by'])
                    except ValueError:
                        results.append(dict(control_id=cid,status='SKIPPED_BUSY'));persist(assessment_id,batch_id,results);seen.add(cid);continue
                    running_job=job['job_id']
                    fresh=next(c for c in shared_work.board(assessment_id)['controls'] if c['control_id']==cid)
                    if source_token(fresh)!=item['source_token'] or shared_work.execution_mode(fresh)!='user_evidence_only':
                        teamwork.finish_job(running_job,None,'Nguồn đã thay đổi sau khi chốt lượt chạy; chưa gọi Agent.')
                        result=dict(control_id=cid,job_id=running_job,status='SKIPPED_SOURCE_CHANGED')
                    else:
                        execute(running_job,assessment_id,cid,True)
                        finished=teamwork.get_job(running_job)
                        if not finished or finished['status']=='RUNNING':raise RuntimeError('Worker did not persist a terminal job result')
                        result=dict(control_id=cid,job_id=running_job,status=finished['status'],error=finished.get('error_message'),
                            started_at=finished.get('started_at'),finished_at=finished.get('finished_at'),source_token=item['source_token'])
                    running_job=None
                results.append(result);seen.add(cid);persist(assessment_id,batch_id,results)
            current=get(assessment_id,batch_id)
            persist(assessment_id,batch_id,results,'STOPPED' if current and current['status']=='STOP_REQUESTED' else 'COMPLETED')
        except Exception:
            logger.exception('Source batch %s failed',batch_id)
            if running_job:teamwork.finish_job(running_job,None,'Lượt chạy nguồn bị lỗi; xem log API.')
            current=get(assessment_id,batch_id)
            persist(assessment_id,batch_id,current['results'] if current else [],'FAILED','Lượt chạy bị lỗi. Kết quả từng việc đã lưu được giữ nguyên; xem log API.')
        finally:
            lock_cur.execute('SELECT pg_advisory_unlock(hashtext(%s))',('batch-worker:'+batch_id,))
