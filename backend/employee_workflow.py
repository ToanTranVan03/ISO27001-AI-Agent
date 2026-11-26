"""Evidence-bound employee participation, adapted to main's identity and control model."""
from copy import deepcopy
import hashlib
import unicodedata

CONTROL={'training':'A.6.3','nda':'A.6.6','mfa':'A.8.5','asset_return':'A.6.5'}


def document_hash(content):return hashlib.sha256(content.encode('utf-8')).hexdigest()


def training_feedback(answer):
    text=''.join(c for c in unicodedata.normalize('NFD',answer.lower().replace('đ','d')) if not unicodedata.combining(c))
    checks={
        'recognize':any(t in text for t in ('gia mao','dang ngo','lua dao','phishing','bat thuong')),
        'safe_response':any(t in text for t in ('khong bam','khong mo','khong nhap','khong truy cap')),
        'report':any(t in text for t in ('bao cao','helpdesk','soc','bao mat','an toan thong tin')),
    }
    questions={'recognize':'Dấu hiệu nào khiến bạn nghi ngờ yêu cầu đó?','safe_response':'Bạn tránh thao tác nào để không lộ thông tin?','report':'Bạn báo cho ai qua kênh nội bộ nào?'}
    return dict(rubric='project-phishing-awareness-v1',checks=checks,
        followup=[questions[k] for k,v in checks.items() if not v],human_review_required=True,
        note='Từ khóa chỉ gợi ý phỏng vấn/đào tạo, không chấm năng lực nhân viên hoặc tự xác nhận control đạt.')


def apply_event(doc,command,payload,actor,role,at):
    result=deepcopy(doc);kind=doc['kind'];owner=str(doc['user_id'])==str(actor)
    if command=='respond':
        if not owner:raise PermissionError('Chỉ đúng nhân viên được gán tài khoản tự phản hồi.')
        if doc['state'] not in ('WAITING_EMPLOYEE','REWORK'):raise ValueError('Không sửa phản hồi đã nộp/đã thẩm định.')
        if kind=='nda' and (payload.get('document_sha256')!=doc['document_sha256'] or payload.get('acknowledged') is not True):
            raise ValueError('Cần đúng hash tài liệu và nhân viên tự xác nhận đã đọc; không phải chữ ký pháp lý.')
        response=dict(answer=payload['answer'],actor=str(actor),at=at)
        if kind=='training':response['feedback']=training_feedback(payload['answer'])
        result.setdefault('responses',[]).append(response)
        result['state']='WAITING_SOURCE' if kind in ('mfa','asset_return') else 'AWAITING_REVIEW'
    elif command=='observe':
        if role not in ('consultant','business_admin','verifier') or owner:raise PermissionError('Cần người phụ trách nguồn khác nhân viên ghi quan sát.')
        if kind not in ('mfa','asset_return') or doc['state'] not in ('WAITING_SOURCE','REWORK'):raise ValueError('Yêu cầu chưa chờ quan sát nguồn.')
        if not payload.get('evidence'):raise ValueError('Cần bằng chứng đúng control, không dùng lời khai thay nguồn.')
        observation=dict(actor=str(actor),at=at,note=payload['note'],evidence=payload['evidence'],source_token=payload.get('source_token'))
        if kind=='mfa':
            if type(payload.get('enrolled')) is not bool or type(payload.get('enforced')) is not bool:raise ValueError('Cần quan sát riêng đăng ký và cưỡng chế MFA.')
            observation.update(enrolled=payload['enrolled'],enforced=payload['enforced'])
        else:
            if not payload.get('receipt_reference') or payload.get('asset_id')!=doc['target_id']:raise ValueError('Cần đúng thiết bị và mã biên nhận bàn giao.')
            observation.update(asset_id=payload['asset_id'],receipt_reference=payload['receipt_reference'])
        result.setdefault('observations',[]).append(observation);result['state']='AWAITING_REVIEW'
    elif command=='reopen':
        if role not in ('consultant','verifier') or owner or (doc.get('observations') and doc['observations'][-1]['actor']==str(actor)):
            raise PermissionError('Cần người thẩm định khác người thực hiện/quan sát mở kiểm tra lại.')
        if doc['state']!='REVIEWED':raise ValueError('Chỉ mở kiểm tra lại hồ sơ đã được thẩm định.')
        result['state']='REWORK'
    elif command=='review':
        if role not in ('consultant','verifier') or owner or (doc.get('observations') and doc['observations'][-1]['actor']==str(actor)):
            raise PermissionError('Người thực hiện/quan sát không tự thẩm định; cần người xác minh riêng.')
        if doc['state']!='AWAITING_REVIEW':raise ValueError('Yêu cầu chưa có phản hồi/quan sát để thẩm định.')
        outcome=payload['outcome']
        if outcome not in ('accepted','rework','more_information'):raise ValueError('Kết quả thẩm định không hợp lệ.')
        if outcome=='accepted':
            if not payload.get('evidence'):raise ValueError('Cần viện dẫn nguồn gốc hiện hành trước khi xác nhận.')
            if kind=='mfa' and not all(doc['observations'][-1].get(k) is True for k in ('enrolled','enforced')):raise ValueError('Đăng ký và cưỡng chế chưa đồng thời được xác minh.')
        result.setdefault('reviews',[]).append(dict(actor=str(actor),at=at,outcome=outcome,note=payload['note'],evidence=payload.get('evidence',[]),source_token=payload.get('source_token')))
        result['state']='REVIEWED' if outcome=='accepted' else 'REWORK'
    else:raise ValueError('Không hỗ trợ sự kiện này.')
    result.setdefault('history',[]).append(dict(command=command,actor=str(actor),at=at,note=payload.get('note','')))
    return result
