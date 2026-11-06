"""Read-only lab dossier; incident cleanup is not a compliance conclusion."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from backend.enterprise_spec import NODE_SPECS, CONTROL_TO_NODE
from backend.database import get_connection


def campaign_evidence(assessment_id):
    """All campaign evidence metadata, including uploads; no cross-campaign samples."""
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute('''SELECT control_id,evidence_id,evidence_type,source,sha256_hash,
                                  created_at,is_synthetic,extracted_text
                           FROM evidence WHERE assessment_id=%s ORDER BY created_at DESC''', (assessment_id,))
            rows = cur.fetchall()
    grouped = {}
    for cid, eid, kind, source, digest, created, synthetic, text in rows:
        payload = {}
        if synthetic:
            try:
                payload = json.loads(text)
                if not isinstance(payload, dict):
                    payload = {}
            except (TypeError, ValueError):
                pass
        grouped.setdefault(cid, []).append({'evidence_id': eid, 'evidence_type': kind,
            'source': source, 'sha256_hash': digest, 'created_at': created.isoformat(),
            'is_synthetic': synthetic, 'revision': payload.get('revision'),
            'facts': payload.get('facts', {}), 'origin': 'lab' if synthetic else 'uploaded_or_imported'})
    return grouped


def newer_evidence(evidence, evaluation):
    try:
        return datetime.fromisoformat(evidence['created_at']) > datetime.fromisoformat(evaluation['created_at'])
    except (KeyError, TypeError, ValueError):
        # Unknown freshness must not be silently presented as current.
        return True


def build_dossier(assessment_id, board, evidence_by_control, history_by_control=None):
    records = []
    for item in board:
        cid = item['control_id']
        node = NODE_SPECS.get(CONTROL_TO_NODE.get(cid), {})
        evaluated = bool(item.get('latest_evaluation_id'))
        history = (history_by_control or {}).get(cid, [])
        latest = next((h for h in history if h['evaluation_id'] == item.get('latest_evaluation_id')), None)
        stale = bool(latest and any(newer_evidence(e, latest) for e in evidence_by_control.get(cid, [])))
        records.append({**item, 'collector_supported': bool(node),
            'source': node.get('title'), 'criteria': node.get('values', {}).get('healthy', {}),
            'evidence': evidence_by_control.get(cid, []),
            'evaluation_history': (history_by_control or {}).get(cid, []),
            'historical_conclusion': item.get('compliance_status') if evaluated else None,
            'conclusion': 'Cần tái đánh giá' if stale else (item.get('compliance_status') if evaluated else 'Chưa đánh giá'),
            'assessment_state': 'stale' if stale else ('evaluated' if evaluated else 'not_evaluated')})
    payload = {'assessment_id': str(assessment_id), 'is_synthetic': True,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'supported_collectors': sorted(CONTROL_TO_NODE), 'controls': records,
        'summary': dict(Counter(r['conclusion'] for r in records)),
        'limitations': ['Không suy ra tuân thủ từ việc xử lý sự cố.',
          'Chưa có SoA được phê duyệt; chưa đánh giá toàn bộ ISMS.',
          'Metadata bao gồm bằng chứng của đợt đánh giá; không xác thực nội dung tài liệu chỉ từ hash.',
          'Tiêu chí lab là chính sách dự án, không phải nguyên văn tiêu chuẩn.']}
    payload['sha256'] = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()
    return payload
