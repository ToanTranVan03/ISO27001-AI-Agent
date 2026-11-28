"""Copy captured lab sources into the dossier; never copy a study conclusion."""
import hashlib
import json
from pathlib import Path
from uuid import UUID
from psycopg.types.json import Jsonb
from backend.database import get_connection
from agent_core.a8_assessment import digest

ORIGIN='a8-live-capture-v1'


def capture_reference(assessment_id, control_id, evidence_id, source, checksum, content):
    """Resolve a server-imported observation without treating it as a conclusion."""
    try:
        payload=json.loads(content)
        if not isinstance(payload,dict):return None
        run_id=str(UUID(payload['run_id']))
        report_hash=payload['report_sha256']
        asset=payload['asset_id']
        if not isinstance(asset,str) or not asset.strip():return None
        if not isinstance(report_hash,str) or len(report_hash)!=64 or any(ch not in '0123456789abcdef' for ch in report_hash):return None
        if payload['origin']!=ORIGIN or payload['assessment_id']!=str(assessment_id) or payload['control_id']!=control_id:return None
        if source!=f'a8-capture://{run_id}/{control_id}' or hashlib.sha256(content.encode()).hexdigest()!=checksum:return None
        if evidence_id!='A8CAP-'+digest([str(assessment_id),control_id,checksum])[:40]:return None
    except (ValueError,TypeError,KeyError,AttributeError):
        return None
    reference=dict(run_id=run_id,report_sha256=report_hash,evidence_id=evidence_id,source_sha256=checksum,asset_id=asset)
    if control_id=='A.8.8':
        sample=sample_application(payload)
        if sample:reference['sample_application']=sample
    return reference


def sample_application(payload):
    try:
        artifact,=[a for a in payload['artifacts'] if a['artifact']=='sample-application.json']
        content=artifact['content']
        if hashlib.sha256(content.encode()).hexdigest()!=artifact['sha256']:return None
        packet=json.loads(content)
        observed=packet['observation']
        if packet['schema']!='a88-sample-baseline-v1' or packet['platform_target']!='linux_lab':return None
        if observed['platform']!='Linux' or observed['health']!='ok' or not observed['observed_at']:return None
        return dict(platform_target='linux_lab',system='Linux',application=observed['application'],
                    baseline_version=observed['version'],baseline_artifact_sha256=observed['sha256'],
                    observed_at=observed['observed_at'])
    except (KeyError,TypeError,ValueError,AttributeError):
        return None


def prepare_sources(assessment_id,run_id,doc):
    report=doc.get('report',{})
    if doc.get('state')!='finished' or report.get('transport')!='live':
        raise ValueError('Chỉ nhập nguồn từ lượt live đã hoàn tất; replay không được gắn nhãn live.')
    if report.get('sha256')!=digest({k:v for k,v in report.items() if k!='sha256'}):
        raise ValueError('Report hash không hợp lệ.')
    catalog=json.loads((Path(__file__).resolve().parents[1]/'docs/56_controls_scope.json').read_text(encoding='utf-8'))
    controls={c['control_id']:c for c in catalog}
    packets=[];skipped=[];seen=set()
    for record in report['records']:
        cid=record['control_id'];e=record['evidence']
        if cid not in controls or cid in seen:raise ValueError('Control ngoài phạm vi hoặc trùng.')
        seen.add(cid)
        if not e.get('observation_available',bool(e.get('artifacts'))):skipped.append(cid);continue
        for artifact in e['artifacts']:
            if hashlib.sha256(artifact['content'].encode()).hexdigest()!=artifact['sha256']:
                raise ValueError('Artifact hash không hợp lệ.')
        payload=dict(origin=ORIGIN,assessment_id=str(assessment_id),run_id=str(run_id),report_sha256=report['sha256'],
            control_id=cid,is_synthetic=True,provenance_verified=False,source=e['source'],
            observed_at=e.get('observed_at'),collected_at=e['collected_at'],asset_id=e.get('asset_id'),
            artifacts=e['artifacts'],collection_errors=e.get('collection_errors',[]),
            criteria_scope=record.get('criteria_details',[]),
            note='Bản thu tại thời điểm trong lab có chủ đích; không phải trạng thái production hoặc kết luận đánh giá đầy đủ control.')
        text=json.dumps(payload,ensure_ascii=False,sort_keys=True)
        checksum=hashlib.sha256(text.encode()).hexdigest()
        eid='A8CAP-'+digest([str(assessment_id),cid,checksum])[:40]
        packets.append(dict(control_id=cid,evidence_id=eid,evidence_type=controls[cid]['expected_evidence_types'][0],
            source='a8-capture://'+str(run_id)+'/'+cid,extracted_text=text,sha256_hash=checksum))
    if not packets:raise ValueError('Lượt này không có nguồn quan sát để nhập.')
    return packets,skipped


def import_sources(assessment_id,run_id,doc,actor_id):
    packets,skipped=prepare_sources(assessment_id,run_id,doc)
    inserted=[];reused=[]
    with get_connection() as con,con.cursor() as cur:
        ids=sorted(p['control_id'] for p in packets)
        cur.execute('SELECT control_id,workflow_status FROM control_progress WHERE assessment_id=%s AND control_id=ANY(%s) ORDER BY control_id FOR UPDATE',(assessment_id,ids))
        rows=cur.fetchall()
        if {r[0] for r in rows}!=set(ids):raise ValueError('Control không thuộc đợt đánh giá.')
        if any(r[1]=='RUNNING' for r in rows):raise ValueError('Có control đang đánh giá; chưa nhập nguồn để tránh thay đổi giữa lượt.')
        for packet in packets:
            cur.execute('''INSERT INTO evidence(evidence_id,control_id,evidence_type,source,extracted_text,
                sha256_hash,is_sample,assessment_id,is_synthetic,evidence_origin,uploaded_by)
                VALUES (%s,%s,%s,%s,%s,%s,FALSE,%s,TRUE,%s,%s)
                ON CONFLICT(evidence_id) DO NOTHING RETURNING evidence_id''',
                (packet['evidence_id'],packet['control_id'],packet['evidence_type'],packet['source'],packet['extracted_text'],
                 packet['sha256_hash'],assessment_id,ORIGIN,actor_id))
            added=cur.fetchone()
            (inserted if added else reused).append(packet['evidence_id'])
            if added:
                cur.execute('''INSERT INTO assessment_events(assessment_id,control_id,user_id,event_type,details)
                    VALUES (%s,%s,%s,'A8_CAPTURE_IMPORTED',%s)''',
                    (assessment_id,packet['control_id'],actor_id,Jsonb(dict(evidence_id=packet['evidence_id'],run_id=str(run_id),is_synthetic=True))))
    return dict(inserted=inserted,reused=reused,skipped_controls=skipped,
                note='Chỉ nhập nguồn lab; không nhập kết luận, đáp án hoặc nhãn. Cần đánh giá/thẩm định riêng trong Phạm vi 56.')
