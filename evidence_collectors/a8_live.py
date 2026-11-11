"""Fixed read-only probes of an isolated lab, distinct from historical replay.

Eighteen representative controls have probes. Five observe existing resources;
thirteen execute bounded active self-tests of container-local applications.
"""
import base64
import csv
import hashlib
import io
import json
import subprocess
from copy import deepcopy
from datetime import datetime, timezone
from evidence_collectors.a8_live_extended import SPECS,evaluate as evaluate_extended

PASSIVE_IDS = ('A.8.3', 'A.8.10', 'A.8.13', 'A.8.15', 'A.8.19')
LIVE_IDS = tuple(sorted((*PASSIVE_IDS,*SPECS),key=lambda cid:int(cid.split('.')[-1])))
LIVE_PROFILES = ('conforming', 'mixed', 'nonconforming', 'incomplete')
VERSION = 'a8-live-v2-active'
DESCRIPTIONS = {
    'A.8.3': [('write_access_rc + resource_stat', 'labworker không ghi được tệp nghiệp vụ (test -w trả 1).'),
              ('access-review.csv', 'Review cho labworker được approved trong 90 ngày; là hồ sơ lab, chưa phải phê duyệt chuyên gia.')],
    'A.8.10': [('retention.conf', 'Cấu hình retention của lab trong 1–30 ngày.'),
               ('object_exists_rc + deletion-receipt', 'Có biên nhận phép kiểm tra và đối tượng đã không còn tồn tại.')],
    'A.8.13': [('backup.dat + backup.sha256', 'Hash nội dung backup khớp seal lúc tạo backup.'),
               ('backup.dat + restored.dat', 'Nội dung đã khôi phục khớp backup.')],
    'A.8.15': [('application.log', 'Ứng dụng lab thực sự ghi ít nhất một sự kiện.'),
               ('application.log + application.sha256 + resource_stat', 'Log khớp seal và không cho group/other ghi; chưa kiểm chứng auditd/SIEM.')],
    'A.8.19': [('install_access_rc', 'labworker không có quyền ghi thư mục cài đặt (test -w trả 1).'),
               ('installed.tsv + approved.tsv', 'Inventory dpkg-query lúc thu khớp danh mục phê duyệt của lab; chưa xác nhận quản trị thay đổi ngoài lab.')],
}


def live_catalog(controls):
    result = deepcopy(controls)
    for c in result:
        cid = c['control_id']
        c['rubric_version'] = VERSION
        if cid in SPECS:
            c['checks']=[s[0] for s in SPECS[cid]]
            c['criteria']=[dict(check=check,raw_source='probe.json: '+source,pass_condition=condition,
                fail_condition='Có quan sát hợp lệ nhưng không thỏa điều kiện lab.',
                missing_condition='Thiếu nguồn, lỗi công cụ hoặc sai định dạng => unknown.',
                verification_kind='container-active-self-test') for check,source,condition in SPECS[cid]]
        c['scope_note'] = ('Phép thử đại diện trên tài nguyên container; không đại diện toàn bộ control/ISMS.'
                           if cid in LIVE_IDS else 'Chưa có probe live cho control này; phải kết luận thiếu bằng chứng.')
        for i, criterion in enumerate(c['criteria'] if cid not in SPECS else []):
            source, condition = DESCRIPTIONS[cid][i] if cid in LIVE_IDS else ('unavailable', 'Chưa triển khai probe live.')
            criterion.update(raw_source=source, pass_condition=condition,
                             verification_kind='live-container-observation' if cid in LIVE_IDS else 'not-implemented')
    return result


def _parse(raw):
    if len(raw) > 200000:
        raise ValueError('Oversize live observation')
    values = {}
    for line in raw.decode('ascii').splitlines():
        key, encoded = line.split('\t')
        if key in values or key not in {'observed_at', 'asset_id', 'write_access_rc', 'resource_stat',
                'access-review.csv', 'retention.conf', 'deletion-receipt', 'object_exists_rc',
                'backup.dat', 'backup.sha256', 'restored.dat', 'application.log', 'application.sha256',
                'install_access_rc', 'install_stat', 'installed.tsv', 'approved.tsv','probe.json'}:
            raise ValueError('Invalid live probe field')
        values[key] = None if encoded == 'MISSING' else base64.b64decode(encoded, validate=True).decode('utf-8')
    return values


def collect_live(profile, control):
    if profile not in LIVE_PROFILES:
        raise ValueError('Live lab supports four profiles; stale/conflicting are replay cases only')
    cid = control['control_id']
    facts = {k: None for k in control['checks']}
    errors, values, artifacts = [], {}, []
    active_observations=False
    if cid not in LIVE_IDS:
        errors.append({'artifact': 'live-probe', 'error': 'live_probe_not_implemented'})
    else:
        try:
            proc = subprocess.run(['docker', 'exec', 'iso-a8-lab', '/bin/sh', '/live_probe.sh', profile, cid],
                                  capture_output=True, timeout=15)
            if proc.returncode:
                raise OSError('Live probe failed')
            values = _parse(proc.stdout)
            for name, content in values.items():
                if content is not None:
                    artifacts.append(dict(artifact=name, content=content,
                                          sha256=hashlib.sha256(content.encode()).hexdigest()))
            observed = datetime.fromisoformat(values['observed_at'])
            if observed.tzinfo is None or not 0 <= (datetime.now(timezone.utc)-observed).total_seconds() <= 120:
                raise ValueError('Invalid live capture time')
            if not values.get('asset_id'):
                raise ValueError('Missing asset identity')

            def text(name):
                value = values.get(name)
                if value is None:
                    raise ValueError('Missing observation: ' + name)
                return value

            def check(fn):
                try:
                    return bool(fn())
                except (ValueError, TypeError, KeyError, IndexError, csv.Error) as exc:
                    errors.append({'artifact': 'live-probe', 'error': str(exc)[:150]})
                    return None

            def denied(name):
                rc = int(text(name))
                if rc not in (0, 1):
                    raise ValueError('Permission probe did not execute successfully')
                return rc == 1

            def reviewed():
                rows = list(csv.DictReader(io.StringIO(text('access-review.csv'))))
                if not rows or not any(r['subject'] == 'labworker' for r in rows):
                    raise ValueError('Missing account review')
                return all(r['decision'] == 'approved' and
                           0 <= (observed-datetime.fromisoformat(r['reviewed_at'])).total_seconds() <= 90*86400
                           for r in rows)

            def digest(name):
                return hashlib.sha256(text(name).encode()).hexdigest()

            def mode(name):
                fields=text(name).split()
                if len(fields)!=3:
                    raise ValueError('Missing or malformed resource stat')
                return int(fields[0],8)

            if cid in SPECS:
                payload=json.loads(text('probe.json'))
                if not isinstance(payload,dict):raise ValueError('Invalid active observation object')
                if (payload.get('schema')!='a8-active-observation-v2' or payload.get('control_id')!=cid or
                        payload.get('observed_at')!=values['observed_at'] or payload.get('asset_id')!=values['asset_id']):
                    raise ValueError('Active observation identity/schema mismatch')
                if not isinstance(payload.get('observations'),dict) or not isinstance(payload.get('collection_errors'),list):
                    raise ValueError('Invalid active observation fields')
                if payload.get('collection_errors'):
                    errors.extend(payload['collection_errors']);first=second=None
                else:
                    active_observations=bool(payload['observations'])
                    (first,second),issues=evaluate_extended(cid,payload['observations'],observed)
                    errors.extend(issues)
            elif cid == 'A.8.3':
                first, second = check(lambda: mode('resource_stat')>=0 and denied('write_access_rc')), check(reviewed)
            elif cid == 'A.8.10':
                first = check(lambda: 1 <= int(text('retention.conf').strip().split('=')[1]) <= 30)
                second = check(lambda: bool(text('deletion-receipt')) and denied('object_exists_rc'))
            elif cid == 'A.8.13':
                first = check(lambda: digest('backup.dat') == text('backup.sha256').strip())
                second = check(lambda: bool(text('backup.dat')) and text('backup.dat') == text('restored.dat'))
            elif cid == 'A.8.15':
                first = check(lambda: 'event=application_start' in text('application.log'))
                second = check(lambda: digest('application.log') == text('application.sha256').strip() and
                               mode('resource_stat') & 0o022 == 0)
            else:
                first = check(lambda: mode('install_stat')>=0 and denied('install_access_rc'))
                second = check(lambda: bool(text('installed.tsv').strip()) and text('installed.tsv') == text('approved.tsv'))
            facts = dict(zip(control['checks'], (first, second)))
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
            errors.append({'artifact': 'live-probe', 'error': type(exc).__name__})
            facts = {k: None for k in control['checks']}
    combined = hashlib.sha256(json.dumps({'control_id':cid,'artifacts':artifacts}, sort_keys=True).encode()).hexdigest()
    return dict(evidence_id='A8LIVE-'+combined[:24], source='live-container://'+cid,
                source_sha256=combined, collected_at=datetime.now(timezone.utc).isoformat(),
                observed_at=values.get('observed_at'), asset_id=values.get('asset_id'),
                control_id=cid, facts=facts, artifacts=artifacts, collection_errors=errors,
                is_synthetic=True, transport='live', source_kind='live-container-observation',
                probe_kind='container-active-self-test' if cid in SPECS else 'read-only-resource-observation',
                observation_available=active_observations if cid in SPECS else any(a['artifact'] not in ('observed_at','asset_id') for a in artifacts),
                freshness_note='Observed now in an isolated, intentionally configured lab; not production evidence.')
