"""Immutable evidence projections from the shared corporate snapshot."""
import hashlib
import json
from psycopg.types.json import Jsonb
from backend.database import get_connection
from backend import company
from agent_core.people_assessment import evaluate_enterprise, CONTROLS

PEOPLE_CONTROLS = {c[0] for c in CONTROLS}


def fresh_progress(assessment_id, rows):
    """Present stale evaluations as needing a new run without deleting history."""
    from backend.enterprise_spec import CONTROL_TO_NODE
    data = company.snapshot(assessment_id)
    ids = [r['latest_evaluation_id'] for r in rows if r.get('latest_evaluation_id')]
    references = {};document_only=set();new_sources=set()
    if ids:
        with get_connection() as con, con.cursor() as cur:
            cur.execute('''SELECT ev.evaluation_id,e.extracted_text,ev.audit_trail,
                EXISTS(SELECT 1 FROM evidence newer WHERE newer.assessment_id=ev.assessment_id
                    AND newer.control_id=ev.control_id AND newer.created_at>ev.created_at)
                FROM evaluations ev LEFT JOIN evidence e
                ON e.assessment_id=ev.assessment_id AND ev.evidence_ids ? e.evidence_id
                WHERE ev.assessment_id=%s AND ev.evaluation_id=ANY(%s)''', (assessment_id,ids))
            for eid, text, trail, has_new_sources in cur.fetchall():
                if any('USER_EVIDENCE_ONLY' in str(t) for t in (trail or [])):document_only.add(eid)
                if has_new_sources:new_sources.add(eid)
                try:
                    payload = json.loads(text)
                    token = payload.get('snapshot_hash') if isinstance(payload,dict) else None
                except (ValueError,TypeError):
                    token = None
                references.setdefault(eid,[]).append(token)
    result = []
    for row in rows:
        used = references.get(row.get('latest_evaluation_id'),[])
        supported = row['control_id'] in PEOPLE_CONTROLS | set(CONTROL_TO_NODE)
        evaluation_id=row.get('latest_evaluation_id')
        stale = bool(evaluation_id and (evaluation_id in new_sources or
            (evaluation_id not in document_only and supported and (not any(used) or any(x and x != data['snapshot_hash'] for x in used)))))
        value = {**row, 'company_snapshot_hash':data['snapshot_hash'],
            'data_freshness':'stale' if stale else ('current' if row.get('latest_evaluation_id') else 'not_evaluated')}
        if stale:
            value.update(historical_compliance_status=row['compliance_status'],
                         historical_workflow_status=row['workflow_status'],compliance_status=None,
                         workflow_status='RUNNING' if row['workflow_status']=='RUNNING' else 'NOT_STARTED')
        result.append(value)
    return result


def collect_people(assessment_id, control_id):
    if control_id not in PEOPLE_CONTROLS:
        return None
    with get_connection() as con, con.cursor() as cur:
        cur.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
        data = company.snapshot(assessment_id, cur)
        evaluation = next(c for c in evaluate_enterprise(data) if c['control_id'] == control_id)
        payload = {'assessment_id': str(assessment_id), 'source_kind': 'SHARED_COMPANY',
            'is_synthetic': True, 'control_id': control_id, 'snapshot_hash': data['snapshot_hash'],
            'entity_refs': {'employees': [p['id'] for p in data['people']],
                'accounts': [a['id'] for a in data['accounts']], 'devices': [d['id'] for d in data['devices']]},
            'facts': evaluation['evidences']}
        content = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        digest = hashlib.sha256(content.encode()).hexdigest()
        eid = 'COMPANY-' + digest[:28].upper()
        cur.execute('''INSERT INTO evidence(evidence_id,control_id,evidence_type,source,
            extracted_text,sha256_hash,is_sample,assessment_id,is_synthetic,evidence_origin)
            VALUES(%s,%s,'SHARED_COMPANY_SNAPSHOT',%s,%s,%s,FALSE,%s,TRUE,'SHARED_COMPANY')
            ON CONFLICT DO NOTHING''', (eid, control_id, f'lab://company/{control_id}/{data["snapshot_hash"]}',content,digest,assessment_id))
    return {'evidence_id': eid, 'status': evaluation['status'], 'confidence': 1.0,
            'rationale': evaluation['rationale'], 'evaluation': evaluation,
            'snapshot_hash': data['snapshot_hash'], 'execution_source': 'shared-company-rules'}


def bind_lab(snapshot, data, node_key):
    payload = json.loads(snapshot['extracted_text'])
    if node_key == 'hr':
        flags = [p.get('screened') for p in data['people']]
        payload['facts']['employees_total'] = len(flags)
        payload['facts']['screening_records'] = sum(x is True for x in flags)
        payload['facts']['unknown_screening_records'] = sum(x is None for x in flags)
    if node_key == 'iam':
        active = [a for a in data['accounts'] if a.get('active') is True]
        payload['facts'].update(active_accounts=len(active), mfa_enabled_accounts=sum(a.get('mfa') is True for a in active),
            unknown_active_accounts=sum(a.get('active') is None for a in data['accounts']),
            unknown_mfa_accounts=sum(a.get('mfa') is None for a in active),
            privileged_accounts=sum(a.get('privileged') is True for a in active),
            privileged_mfa_accounts=sum(a.get('privileged') is True and a.get('mfa') is True for a in active))
    payload.update(snapshot_hash=data['snapshot_hash'], entity_refs={
        'employees': [p['id'] for p in data['people']], 'accounts': [a['id'] for a in data['accounts']],
        'assets': [a['asset_id'] for a in data['assets']]})
    content = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(content.encode()).hexdigest()
    return {**snapshot, 'extracted_text': content, 'sha256_hash': digest,
            'evidence_id': 'LAB-COMPANY-' + digest[:24].upper()}
