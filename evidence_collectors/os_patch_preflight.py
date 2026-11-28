"""Offline checks for an operator-supplied OS patch evidence packet."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path

MAX_ARTIFACT_BYTES = 15 * 1024 * 1024


def instant(value):
    if not isinstance(value, str):
        raise ValueError('Thời điểm phải là chuỗi ISO 8601 có múi giờ.')
    timestamp = datetime.fromisoformat(value)
    if timestamp.utcoffset() is None:
        raise ValueError('Thời điểm thiếu múi giờ.')
    return timestamp


def check_artifact(root, artifact):
    if not isinstance(artifact, dict):
        raise ValueError('Thiếu khai báo tệp gốc.')
    name = artifact.get('file')
    if not isinstance(name, str) or not name or name in {'.', '..'} or any(c in name for c in '/\\:'):
        raise ValueError('Tệp gốc phải nằm cạnh manifest.')
    path = root / name
    if path.is_symlink() or not path.is_file() or path.resolve().parent != root:
        raise ValueError('Không tìm được tệp gốc thường nằm cạnh manifest.')
    with path.open('rb') as stream:
        content = stream.read(MAX_ARTIFACT_BYTES + 1)
    if not content.strip() or len(content) > MAX_ARTIFACT_BYTES:
        raise ValueError('Tệp gốc rỗng hoặc vượt 15 MiB.')
    checksum = hashlib.sha256(content).hexdigest()
    if checksum != artifact.get('sha256'):
        raise ValueError('SHA-256 không khớp tệp gốc.')
    return checksum


def preflight(manifest, root):
    root = root.resolve()
    issues = []
    if not isinstance(manifest, dict):
        return result(['Manifest phải là đối tượng JSON.'])
    sections = {name: manifest.get(name) for name in ('before', 'execution', 'after')}
    if any(not isinstance(value, dict) for value in sections.values()):
        return result(['Cần đủ ba bản ghi before, execution và after.'])
    before, execution, after = sections.values()
    for section, record in sections.items():
        if any(not isinstance(record.get(k), str) or not record[k].strip() for k in ('asset_id', 'os_family', 'patch_id')):
            issues.append(f'{section}: thiếu mã tài sản, họ hệ điều hành hoặc mã bản vá.')
    for field in ('asset_id', 'os_family', 'patch_id'):
        if len({str(record.get(field)) for record in sections.values()}) != 1:
            issues.append(f'Ba bản ghi không khớp {field}.')
    try:
        if not instant(before.get('observed_at')) <= instant(execution.get('approved_at')) <= instant(execution.get('executed_at')) < instant(after.get('observed_at')):
            issues.append('Thứ tự yêu cầu gồm đo trước, duyệt, thực hiện và đo lại.')
    except ValueError as error:
        issues.append(str(error))
    if any(not isinstance(record.get('os_build'), str) or not record['os_build'].strip() for record in (before, after)):
        issues.append('Thiếu build hoặc phiên bản gói OS ở lần đo trước hoặc sau.')
    if before.get('patch_present') is not False or after.get('patch_present') is not True:
        issues.append('Cần quan sát bản vá vắng mặt trước và có mặt sau.')
    if execution.get('status') != 'succeeded':
        issues.append('Biên nhận thực thi chưa ghi thành công.')
    if not isinstance(execution.get('approval_reference'), str) or not execution['approval_reference'].strip():
        issues.append('Thiếu mã phiếu phê duyệt.')
    if after.get('reboot_state') not in ('completed', 'not_required') or after.get('health') != 'ok':
        issues.append('Cần ghi nhận khởi động lại hoặc lý do không cần, cùng tình trạng sau vá.')
    if after.get('reboot_state') == 'not_required' and not str(after.get('reboot_reason') or '').strip():
        issues.append('Thiếu căn cứ cho trạng thái không cần khởi động lại.')
    hashes = []
    for section, record in sections.items():
        try:
            hashes.append(check_artifact(root, record.get('artifact')))
        except (OSError, ValueError) as error:
            issues.append(f'{section}: {error}')
    if len(set(hashes)) != len(hashes):
        issues.append('Nguồn đo trước, biên nhận và nguồn đo sau phải là các tệp nội dung riêng.')
    return result(issues)


def result(issues):
    return {
        'protocol': 'a88-os-patch-preflight-v1',
        'ready_for_review': not issues,
        'issues': issues,
        'status': 'Chờ chuyên viên đối chiếu nội dung gốc' if not issues else 'Cần bổ sung hoặc đối chiếu lại',
    }


def intake_manifest(manifest, origin):
    origin=origin.strip()
    if not 5<=len(origin)<=200:
        raise ValueError('Xuất xứ cần từ 5 đến 200 ký tự.')
    sources=[]
    stages=(('before','Đo trước','observed_at'),('execution','Biên nhận thực thi','executed_at'),
            ('after','Đo lại','observed_at'))
    for stage,label,timestamp in stages:
        record=manifest[stage]
        sources.append({
            'file':record['artifact']['file'],
            'sha256':record['artifact']['sha256'],
            'evidence_type':'EVID_TECH_VULN_CONFIG',
            'origin':origin,
            'observed_at':record[timestamp],
            'note':f'{label} · Máy {record["asset_id"]} · Bản vá {record["patch_id"]}'[:1000],
        })
    return {'control_id':'A.8.8','sources':sources}


def main():
    parser = argparse.ArgumentParser(description='Kiểm tra gói nguồn bản vá A.8.8 trước khi nộp.')
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--intake-output', type=Path, help='Ghi manifest nhập nguồn vào tệp mới.')
    parser.add_argument('--origin', help='Xuất xứ do người nộp khai báo khi xuất manifest.')
    args = parser.parse_args()
    if bool(args.intake_output)!=bool(args.origin):
        parser.error('Dùng --intake-output cùng --origin.')
    try:
        with args.manifest.open(encoding='utf-8-sig') as stream:
            manifest = json.loads(stream.read(65537))
        report = preflight(manifest, args.manifest.resolve().parent)
        if report['ready_for_review'] and args.intake_output:
            content=json.dumps(intake_manifest(manifest,args.origin),ensure_ascii=False,indent=2)
            with args.intake_output.open('x',encoding='utf-8') as stream:
                stream.write(content+'\n')
            report['intake_manifest']=str(args.intake_output)
    except (OSError, ValueError) as error:
        report = result([str(error)])
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['ready_for_review'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
