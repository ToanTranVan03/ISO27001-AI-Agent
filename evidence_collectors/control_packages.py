"""Tenant-bound evidence folder connector for all 56 controls; never generates evidence."""
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
from uuid import UUID
from backend.scope56 import CATALOG
from evidence_collectors.document_parser import extract_document_text

ROOT=Path(__file__).resolve().parents[1]/'data'/'evidence-packages'
MAX_BYTES=15*1024*1024
ALLOWED={'.pdf','.docx','.txt','.md','.csv','.tsv','.json','.conf','.log'}


def controls():return json.loads(CATALOG.read_text(encoding='utf-8'))


def directory(assessment_id,control_id):
    aid=str(UUID(str(assessment_id)))
    if control_id not in {c['control_id'] for c in controls()}:raise ValueError('Ngoài phạm vi 56 control.')
    path=ROOT/aid/control_id
    # A control directory cannot alias another tenant/control through a link.
    if path.resolve()!=ROOT.resolve()/aid/control_id:raise ValueError('Đường dẫn vượt hoặc liên kết sang thư mục bằng chứng khác.')
    return path


def prepare(assessment_id):
    result=[]
    for c in controls():
        path=directory(assessment_id,c['control_id']);path.mkdir(parents=True,exist_ok=True)
        manifest=path/'manifest.json'
        if manifest.is_symlink():raise ValueError('Manifest không được là symlink.')
        if not manifest.exists():
            manifest.write_text(json.dumps({'control_id':c['control_id'],'sources':[]},ensure_ascii=False,indent=2),encoding='utf-8')
        guide=path/'_REQUIRED.md'
        if guide.is_symlink():raise ValueError('Mẫu không được là symlink.')
        if not guide.exists():
            guide.write_text('# '+c['control_id']+' — '+c['name']+'\n\nMẫu yêu cầu, KHÔNG PHẢI bằng chứng. Không tự tạo kết luận đạt.\n\n'+
              '\n'.join('- '+x for x in c['pass_criteria'])+'\n\nLoại được phép: '+', '.join(c['expected_evidence_types'])+
              '\n\nmanifest.json: sources gồm file (tên file trực tiếp), evidence_type, observed_at (ISO có múi giờ nếu biết), origin, note. Đặt tài liệu/cấu hình/log gốc cùng thư mục. Không liệt kê chính manifest hoặc _REQUIRED.md.\n',encoding='utf-8')
        result.append({'control_id':c['control_id'],'directory':str(path)})
    return {'directories':result,'control_count':len(result),'note':'Chỉ tạo mẫu trống; không tạo bằng chứng hoặc kết luận.'}


def inspect(assessment_id,control_id):
    path=directory(assessment_id,control_id)
    c=next(c for c in controls() if c['control_id']==control_id)
    findings=[];items=[]
    manifest=path/'manifest.json'
    if not manifest.exists():return {'control_id':control_id,'items':[],'issues':['Chưa có manifest hoặc tài liệu gốc.']}
    if manifest.is_symlink() or manifest.stat().st_size>100000:raise ValueError('Manifest không hợp lệ.')
    data=json.loads(manifest.read_text(encoding='utf-8'))
    if not isinstance(data,dict):raise ValueError('Manifest phải là object.')
    if data.get('control_id')!=control_id or not isinstance(data.get('sources'),list) or len(data['sources'])>30:raise ValueError('Manifest sai control hoặc quá 30 nguồn.')
    seen=set();total=0
    for source in data['sources']:
        try:
            name=source['file'];kind=source['evidence_type']
            if not isinstance(name,str) or '/' in name or '\\' in name or name.startswith('_') or name=='manifest.json' or Path(name).name!=name:raise ValueError('Tên tệp không hợp lệ.')
            if name in seen:raise ValueError('Nguồn lặp trong manifest.')
            seen.add(name)
            target=path/name
            if not target.resolve().is_relative_to(path.resolve()) or target.is_symlink():raise ValueError('Nguồn vượt phạm vi thư mục.')
            if kind not in c['expected_evidence_types'] or target.suffix.lower() not in ALLOWED:raise ValueError('Loại nguồn không phù hợp control.')
            size=target.stat().st_size;total+=size
            if size>MAX_BYTES or total>30*1024*1024:raise ValueError('Nguồn quá lớn (15MB/file, 30MB/gói).')
            raw=target.read_bytes()
            text=extract_document_text(name,raw) if target.suffix.lower() in ('.pdf','.docx') else raw.decode('utf-8-sig')
            if not text.strip() or len(text)>100000:raise ValueError('Không có văn bản hoặc quá 100000 ký tự.')
            observed=source.get('observed_at')
            if observed:
                date=datetime.fromisoformat(observed)
                if date.tzinfo is None or date>datetime.now(timezone.utc):raise ValueError('Thời điểm quan sát thiếu múi giờ hoặc ở tương lai.')
            payload={'source_kind':'USER_PROVIDED_PACKAGE','control_id':control_id,'file':name,
                'observed_at':observed,'origin':str(source.get('origin','unspecified'))[:200],
                'note':str(source.get('note',''))[:1000],'content':text,'provenance_verified':False}
            content=json.dumps(payload,ensure_ascii=False,sort_keys=True)
            raw_hash=hashlib.sha256(raw).hexdigest()
            identity=f'{assessment_id}:{control_id}:{kind}:{raw_hash}:{content}'
            items.append({'evidence_id':'PKG-'+hashlib.sha256(identity.encode()).hexdigest()[:32],
                'evidence_type':kind,'source':f'package://{control_id}/{name}',
                'extracted_text':content,'sha256_hash':raw_hash,'observed_at':observed})
        except (OSError,KeyError,TypeError,ValueError) as exc:
            findings.append(str(exc)[:200])
    if not data['sources']:findings.append('Gói trống; cần hồ sơ/cấu hình/log do người phụ trách cung cấp.')
    return {'control_id':control_id,'items':items,'issues':findings}


def collect(assessment_id,control_id,user_id):
    from backend.database import get_connection
    from backend.teamwork import log_event
    packet=inspect(assessment_id,control_id)
    inserted=[];reused=[]
    with get_connection() as con,con.cursor() as cur:
        cur.execute('SELECT workflow_status FROM control_progress WHERE assessment_id=%s AND control_id=%s FOR UPDATE',(assessment_id,control_id))
        row=cur.fetchone()
        if not row or row[0]=='RUNNING':raise ValueError('Control không tồn tại hoặc đang đánh giá.')
        for item in packet['items']:
            cur.execute('''INSERT INTO evidence(evidence_id,control_id,evidence_type,source,extracted_text,sha256_hash,
                assessment_id,uploaded_by,is_sample,is_synthetic,evidence_origin)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,FALSE,FALSE,'USER_PROVIDED_PACKAGE')
                ON CONFLICT(evidence_id) DO NOTHING RETURNING evidence_id''',
                (item['evidence_id'],control_id,item['evidence_type'],item['source'],item['extracted_text'],item['sha256_hash'],assessment_id,user_id))
            if cur.fetchone():
                inserted.append(item['evidence_id']);log_event(cur,assessment_id,control_id,user_id,'PACKAGE_EVIDENCE_COLLECTED',{'evidence_id':item['evidence_id']})
            else:reused.append(item['evidence_id'])
    return {'control_id':control_id,'inserted':inserted,'reused':reused,'issues':packet['issues'],
            'note':'Thu nhận nguồn không có nghĩa nguồn đã xác thực hoặc control đã đạt.'}
