"""Technical integrity checks, never authenticity or semantic ISO coverage."""
import hashlib
import json
from evidence_collectors.source_quality import evidence_quality


def source_quality(assessment_id,control_id,evidence_id,kind,source,text,checksum):
    source=source if isinstance(source,str) else ''
    quality=evidence_quality(text)
    integrity={'state':'not_verifiable','policy':'source-integrity-v1',
        'note':'Nguồn cũ/connector chưa có kiểm tra bản gốc tự động; cần người phụ trách đối chiếu.'}
    issues=[]
    try:
        if source.startswith('upload-source://'):
            from evidence_collectors.source_intake import original_path
            from evidence_collectors.control_packages import MAX_BYTES
            payload=json.loads(text)
            if (not isinstance(payload,dict) or payload.get('source_kind')!='USER_PROVIDED_WEB_SOURCE' or
                payload.get('control_id')!=control_id or payload.get('original_sha256')!=checksum or
                payload.get('original_preserved') is not True):
                raise ValueError('web_manifest_mismatch')
            expected='WEB-'+hashlib.sha256(f'{assessment_id}:{control_id}:{kind}:{checksum}:{text}'.encode()).hexdigest()[:32]
            if evidence_id!=expected:raise ValueError('extracted_content_identity_mismatch')
            path=original_path(assessment_id,checksum)
            if not path.is_file():raise ValueError('original_missing')
            if path.stat().st_size>MAX_BYTES:raise ValueError('original_size_invalid')
            if hashlib.sha256(path.read_bytes()).hexdigest()!=checksum:raise ValueError('original_hash_mismatch')
            integrity={'state':'verified','policy':'source-integrity-v1','note':'Bản gốc và nội dung lưu khớp hash/định danh; chưa xác nhận nguồn thật hoặc đủ control.'}
        elif source.startswith('a8-capture://'):
            payload=json.loads(text)
            if not isinstance(payload,dict):raise ValueError('capture_manifest_invalid')
            if hashlib.sha256(text.encode()).hexdigest()!=checksum:raise ValueError('capture_content_hash_mismatch')
            expected='A8CAP-'+hashlib.sha256(json.dumps([str(assessment_id),control_id,checksum],ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:40]
            if evidence_id!=expected:raise ValueError('capture_identity_mismatch')
            if (payload.get('assessment_id')!=str(assessment_id) or payload.get('control_id')!=control_id or
                source!='a8-capture://'+str(payload.get('run_id'))+'/'+control_id):
                raise ValueError('capture_scope_mismatch')
            artifacts=payload.get('artifacts')
            if not isinstance(artifacts,list) or not artifacts:raise ValueError('capture_artifacts_missing')
            for artifact in artifacts:
                if (not isinstance(artifact,dict) or not isinstance(artifact.get('content'),str) or
                    hashlib.sha256(artifact['content'].encode()).hexdigest()!=artifact.get('sha256')):
                    raise ValueError('capture_artifact_hash_mismatch')
            integrity={'state':'verified','policy':'source-integrity-v1','note':'Hash gói thu và artifact khớp; chỉ xác minh tính toàn vẹn bản lưu trong lab.'}
    except (ValueError,TypeError,KeyError,OSError) as exc:
        # Never expose filesystem paths or accept unreadable originals as valid.
        issue=str(exc) if isinstance(exc,ValueError) and str(exc) in {
            'web_manifest_mismatch','extracted_content_identity_mismatch','original_missing','original_size_invalid',
            'original_hash_mismatch','capture_manifest_invalid','capture_content_hash_mismatch','capture_identity_mismatch','capture_scope_mismatch',
            'capture_artifacts_missing','capture_artifact_hash_mismatch'} else 'source_integrity_unreadable'
        issues.append(issue)
        integrity={'state':'failed','policy':'source-integrity-v1','note':'Chưa xác minh được tính toàn vẹn bản lưu; cần đối chiếu hoặc nộp lại nguồn.'}
    return {**quality,'usable':quality['usable'] and not issues,'issues':quality['issues']+issues,'integrity':integrity}
