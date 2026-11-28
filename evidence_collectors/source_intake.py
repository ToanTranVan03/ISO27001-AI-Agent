"""Web intake of supplied artifacts; no fabricated evidence or authenticity claims."""
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
from uuid import UUID
from evidence_collectors.control_packages import ALLOWED,MAX_BYTES,controls
from evidence_collectors.document_parser import extract_document_text
from evidence_collectors.source_quality import text_quality

ORIGINALS=Path(__file__).resolve().parents[1]/'data'/'evidence-originals'


def prepare(assessment_id,control_id,filename,raw,evidence_type,origin,observed_at=None,note=''):
    aid=str(UUID(str(assessment_id)))
    control=next((c for c in controls() if c['control_id']==control_id),None)
    if control is None or evidence_type not in control['expected_evidence_types']:
        raise ValueError('Control hoặc loại bằng chứng không thuộc phạm vi được hỗ trợ.')
    if not filename or len(filename)>200 or any(c in filename for c in '/\\\x00\r\n') or filename.startswith(('.', '_')):
        raise ValueError('Tên tệp không hợp lệ; chỉ dùng tên tệp trực tiếp.')
    extension=Path(filename).suffix.lower()
    if extension not in ALLOWED:raise ValueError('Định dạng nguồn chưa hỗ trợ.')
    if not raw or len(raw)>MAX_BYTES:raise ValueError('Tệp rỗng hoặc quá 15MB.')
    origin=origin.strip();note=note.strip()
    if not 5<=len(origin)<=200 or len(note)>1000:raise ValueError('Ghi xuất xứ từ 5–200 ký tự; ghi chú tối đa 1000 ký tự.')
    if observed_at:
        try:observed=datetime.fromisoformat(observed_at)
        except (TypeError,ValueError) as exc:raise ValueError('Thời điểm quan sát không hợp lệ.') from exc
        if observed.tzinfo is None or observed>datetime.now(timezone.utc):raise ValueError('Thời điểm quan sát phải có múi giờ và không ở tương lai.')
        observed_at=observed.astimezone(timezone.utc).isoformat()
    text=extract_document_text(filename,raw) if extension in {'.pdf','.docx','.xlsx'} else raw.decode('utf-8-sig')
    if '\x00' in text or len(text)>100000 or not text_quality(text)['usable']:
        raise ValueError('Nguồn không phải văn bản dùng được, quá ít/lặp ký tự hoặc quá 100000 ký tự; kiểm tra nội dung/OCR.')
    if extension=='.json':
        try:json.loads(text)
        except ValueError as exc:raise ValueError('Tệp JSON sai cú pháp.') from exc
    raw_hash=hashlib.sha256(raw).hexdigest()
    payload=dict(source_kind='USER_PROVIDED_WEB_SOURCE',control_id=control_id,file=filename,
        origin=origin,observed_at=observed_at,note=note,content=text,provenance_verified=False,
        original_sha256=raw_hash,original_preserved=True)
    content=json.dumps(payload,ensure_ascii=False,sort_keys=True)
    identity=f'{aid}:{control_id}:{evidence_type}:{raw_hash}:{content}'
    return dict(evidence_id='WEB-'+hashlib.sha256(identity.encode()).hexdigest()[:32],
        evidence_type=evidence_type,source=f'upload-source://{control_id}/{filename}',
        extracted_text=content,sha256_hash=raw_hash,observed_at=observed_at)


def original_path(assessment_id,digest):
    import re
    if not re.fullmatch(r'[0-9a-f]{64}',digest):raise ValueError('Hash nguồn không hợp lệ.')
    aid=str(UUID(str(assessment_id)));path=ORIGINALS/aid/(digest+'.bin')
    if path.resolve()!=ORIGINALS.resolve()/aid/(digest+'.bin'):raise ValueError('Kho bản gốc có liên kết vượt phạm vi.')
    return path


def preserve(assessment_id,raw):
    digest=hashlib.sha256(raw).hexdigest();path=original_path(assessment_id,digest)
    path.parent.mkdir(parents=True,exist_ok=True)
    try:
        with path.open('xb') as out:out.write(raw)
    except FileExistsError:
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Bản gốc trong kho không khớp hash; không ghi đè.')
    return path


def retrieve(assessment_id,control_id,evidence_id):
    from backend.database import get_connection
    with get_connection() as con,con.cursor() as cur:
        cur.execute('''SELECT extracted_text,sha256_hash FROM evidence
            WHERE assessment_id=%s AND control_id=%s AND evidence_id=%s AND source LIKE 'upload-source://%%' ''',
            (assessment_id,control_id,evidence_id))
        row=cur.fetchone()
    if row is None:raise ValueError('Không có bản gốc thuộc control và đợt đánh giá này.')
    payload=json.loads(row[0]);path=original_path(assessment_id,row[1])
    if not path.is_file() or path.stat().st_size>MAX_BYTES or hashlib.sha256(path.read_bytes()).hexdigest()!=row[1]:
        raise ValueError('Bản gốc thiếu hoặc không khớp hash; chưa thể xác minh.')
    return path,payload['file']
