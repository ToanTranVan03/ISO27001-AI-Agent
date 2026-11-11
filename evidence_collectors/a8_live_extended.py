"""Interpret raw active-operation transcripts, separate from lab scenario setup."""
import csv
import io
import math
import re
from datetime import datetime

# Check names deliberately describe what is actually tested, not EDR/NTP/VLAN.
SPECS={
 'A.8.1': [('endpoint_record_private','read_rc + resource_mode','labworker không đọc được hồ sơ tệp endpoint.'),
            ('endpoint_file_encryption_verified','decrypt_rc + decrypted_sha256 + original_sha256 + plaintext_copy_exists','Giải mã tệp mẫu đúng hash và không còn bản plaintext phụ; không phải mã hóa ổ đĩa.')],
 'A.8.2': [('privileged_operation_restricted','privileged_write_rc + account','labworker không ghi được cấu hình quản trị; có tài khoản labadmin.'),
            ('privileged_review_current','review_csv','Review labadmin approved trong 90 ngày; bản ghi lab chưa phải phê duyệt người thật.')],
 'A.8.5': [('password_rejection_verified','bad_password + authenticated','Dịch vụ lab từ chối mật khẩu sai và chấp nhận thông tin đúng.'),
            ('second_factor_enforced','no_second_factor + authenticated','Dịch vụ lab từ chối thiếu yếu tố thứ hai và cho phép thông tin đầy đủ; không phải tích hợp IAM production.')],
 'A.8.7': [('test_signature_quarantined','scanner_exit_code + quarantine_files','Scanner lab thực chuyển mẫu vô hại mang chữ ký thử vào quarantine; không phải sản phẩm antivirus.'),
            ('signature_database_fresh','signature_mtime','Cơ sở chữ ký lab được cập nhật không quá 48 giờ.')],
 'A.8.8': [('inventory_scan_enabled','scan_configuration + inventory_rc + inventory','Job scan bật và truy vấn được inventory dpkg thực tại lúc thu.'),
            ('no_critical_lab_advisory_match','inventory + advisory_catalog','Không có package/version đang cài khớp advisory critical tổng hợp của lab; không phải feed CVE thật.')],
 'A.8.9': [('baseline_authorization_present','baseline.ticket','Có mã CAB-LAB hợp lệ trong bản ghi baseline lab.'),
            ('configuration_matches_baseline','baseline.sha256 + current_sha256','Hash cấu hình hiện tại khớp baseline đã đăng ký.')],
 'A.8.12': [('sensitive_transfer_blocked','transaction','Giao dịch TCP mang mẫu LAB-CONFIDENTIAL bị chặn.'),
             ('blocked_transfer_audited','audit_events','Có sự kiện audit blocked gắn hash payload của phép thử.')],
 'A.8.16': [('file_change_detected_within_sla','monitor_configuration + events','Watcher lab phát hiện thay đổi tệp thử trong 5 giây.'),
             ('alert_delivery_receipt_present','delivery_receipts','Sink lab có biên nhận sự kiện; không phải SIEM ngoài container.')],
 'A.8.17': [('time_reference_signature_valid','reference_reply + signature_verify_rc','Client xác minh HMAC/nonce nguồn thời gian ứng dụng lab.'),
             ('application_time_offset_within_policy','offset_ms + round_trip_ms','Độ lệch so với nguồn cùng container không quá 100ms; không chứng minh NTP/OS đồng bộ độc lập.')],
 'A.8.20': [('unapproved_source_denied','unapproved_source','Dịch vụ TCP thực từ chối loopback source chưa cho phép; không phải firewall kernel.'),
             ('approved_network_flow_available','approved_source','Nguồn TCP được phép truy cập thành công dịch vụ lab.')],
 'A.8.22': [('cross_zone_service_denied','employee_to_admin','Client vùng nhân viên bị từ chối dịch vụ quản trị trong gate ứng dụng lab.'),
             ('business_zone_service_available','employee_to_business','Client vùng nhân viên dùng được dịch vụ nghiệp vụ; không chứng minh VLAN/subnet isolation.')],
 'A.8.24': [('strong_tls_handshake_verified','handshake_rc + handshake.tls_version','Handshake xác minh chứng chỉ lab thành công với TLS 1.2/1.3.'),
             ('private_key_access_restricted','key_read_rc + key_mode','labworker không đọc được private key và mode không cấp quyền group/other.')],
 'A.8.32': [('change_bound_to_current_release','approval + current_release_sha256','Bản ghi CAB-LAB gắn đúng hash release; approval do lab dựng, chưa có người thật duyệt.'),
             ('rollback_restores_release','rollback_rc + restored_sha256 + expected_release_sha256','Thao tác copy rollback thực khôi phục đúng nội dung release đã đăng ký.')]
}


def evaluate(cid,obs,observed):
    """Unknown/malformed source becomes unknown, never a successful fact."""
    errors=[]
    def require(key,kind):
        value=obs[key]
        if type(value) is not kind:raise ValueError('Invalid observation '+key)
        return value
    def rc(key):
        value=require(key,int)
        if value not in ((0,66) if key=='scanner_exit_code' else (0,1)):raise ValueError('Unsuccessful operation '+key)
        return value
    def number(key):
        value=obs[key]
        if type(value) not in (int,float) or not math.isfinite(value):raise ValueError('Invalid numeric observation')
        return value
    def code(key):
        value=require(key,dict)['response']
        if not isinstance(value,str):raise ValueError('Missing application response')
        result=int(value.split()[0])
        if result not in (200,401,403,503):raise ValueError('Unexpected response status')
        return result
    def hash_value(value):
        if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{64}',value):raise ValueError('Invalid hash observation')
        return value
    def hashes(left,right):return hash_value(left)==hash_value(right)
    def review():
        rows=list(csv.DictReader(io.StringIO(require('review_csv',str))))
        if not rows or not any(r['subject']=='labadmin' for r in rows):raise ValueError('Missing privileged review')
        return all(r['decision']=='approved' and 0<=(observed-datetime.fromisoformat(r['reviewed_at'])).total_seconds()<=90*86400 for r in rows)
    def advisory_clear():
        inventory=dict(row.split('\t') for row in require('inventory',str).splitlines())
        if not inventory:raise ValueError('Empty installed inventory')
        catalog=require('advisory_catalog',list)
        if not catalog:raise ValueError('Missing advisory catalog')
        return all(r['severity']!='critical' or inventory.get(r['package'])!=r['affected_version'] for r in catalog)
    def check(fn):
        try:return bool(fn())
        except (KeyError,ValueError,TypeError,IndexError,csv.Error) as exc:
            errors.append(dict(artifact='probe.json',error=str(exc)[:150]));return None
    first=second=lambda:None
    if cid=='A.8.1':
        first=lambda:rc('read_rc')==1
        second=lambda:rc('decrypt_rc')==0 and hashes(obs['decrypted_sha256'],obs['original_sha256']) and require('plaintext_copy_exists',bool) is False
    elif cid=='A.8.2':
        first=lambda:rc('privileged_write_rc')==1 and 'labadmin' in require('account',str)
        second=review
    elif cid=='A.8.5':
        first=lambda:code('bad_password')==401 and code('authenticated')==200
        second=lambda:code('no_second_factor')==403 and code('authenticated')==200
    elif cid=='A.8.7':
        first=lambda:rc('scanner_exit_code')==66 and 'quarantined.txt' in require('quarantine_files',list)
        second=lambda:0<=(observed-datetime.fromisoformat(require('signature_mtime',str))).total_seconds()<=48*3600
    elif cid=='A.8.8':
        first=lambda:require('scan_configuration',dict)['enabled'] is True and rc('inventory_rc')==0 and bool(require('inventory',str).strip())
        second=advisory_clear
    elif cid=='A.8.9':
        first=lambda:bool(re.fullmatch('CAB-LAB-[0-9]+',require('baseline',dict)['ticket']))
        second=lambda:hashes(obs['baseline']['sha256'],obs['current_sha256'])
    elif cid=='A.8.12':
        first=lambda:code('transaction')==403
        second=lambda:any(r['action']=='blocked' and hash_value(r['payload_sha256']) for r in require('audit_events',list))
    elif cid=='A.8.16':
        first=lambda:require('monitor_configuration',dict)['enabled'] is True and any(r['event']=='file_changed' and 0<=r['latency_ms']<=5000 for r in require('events',list))
        second=lambda:any(hash_value(r['receipt_sha256']) for r in require('delivery_receipts',list))
    elif cid=='A.8.17':
        first=lambda:bool(require('reference_reply',dict)['signature']) and rc('signature_verify_rc')==0
        second=lambda:abs(number('offset_ms'))<=100 and 0<=number('round_trip_ms')<=1000
    elif cid=='A.8.20':
        first=lambda:code('unapproved_source')==403
        second=lambda:code('approved_source')==200
    elif cid=='A.8.22':
        first=lambda:code('employee_to_admin')==403
        second=lambda:code('employee_to_business')==200
    elif cid=='A.8.24':
        first=lambda:rc('handshake_rc')==0 and require('handshake',dict)['tls_version'] in ('TLSv1.2','TLSv1.3')
        second=lambda:rc('key_read_rc')==1 and int(require('key_mode',str),8)&0o077==0
    elif cid=='A.8.32':
        first=lambda:bool(re.fullmatch('CAB-LAB-[0-9]+',require('approval',dict)['ticket'])) and hashes(obs['approval']['sha256'],obs['current_release_sha256'])
        second=lambda:rc('rollback_rc')==0 and hashes(obs['restored_sha256'],obs['expected_release_sha256'])
    else:raise ValueError('Unknown extended control')
    return (check(first),check(second)),errors
