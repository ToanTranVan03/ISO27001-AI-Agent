"""Approved offline update of a disposable sample application for the A.8.8 lab."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import secrets
import subprocess
import sys
import tempfile
import zipfile

from .extended_probe import stamp

TARGET = 'iso-demo-inventory'
BEFORE_VERSION = '1.0.0'
REQUIRED_VERSION = '1.1.0'


def package(path, version):
    entrypoint = 'import json\nprint(json.dumps(' + repr(
        {'application': TARGET, 'version': version, 'health': 'ok'}
    ) + '))\n'
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('__main__.py', entrypoint)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observe(path):
    result = subprocess.run([sys.executable, '-I', str(path)], capture_output=True,
                            text=True, check=True, timeout=5)
    state = json.loads(result.stdout)
    return {
        **state,
        'platform': platform.system(),
        'source': 'lab://a8.8/disposable-python-application',
        'observed_at': stamp(),
        'sha256': sha256(path),
        'met': state['application'] == TARGET and state['version'] == REQUIRED_VERSION
        and state['health'] == 'ok',
    }


def install(active, candidate):
    candidate.replace(active)


def run_demo(approve, change=install):
    with tempfile.TemporaryDirectory(prefix='iso-a88-update-') as directory:
        root = Path(directory)
        active, candidate = root/'app.pyz', root/'update.pyz'
        package(active, BEFORE_VERSION)
        package(candidate, REQUIRED_VERSION)
        before = observe(active)
        plan = {
            'id': secrets.token_hex(8), 'target': TARGET,
            'operation': 'replace_disposable_application',
            'from_version': before['version'], 'to_version': REQUIRED_VERSION,
            'candidate_sha256': sha256(candidate),
            'verification': 'Launch the installed application and compare version, health and artifact hash',
        }
        report = {
            'control_reference': 'A.8.8', 'criterion': 'sample_application_meets_lab_version',
            'environment': 'synthetic application in a disposable local directory',
            'before': before, 'plan': plan, 'approval': None, 'execution': None,
            'after': None, 'status': 'AWAITING_APPROVAL',
        }
        actor = approve(plan.copy(), before.copy())
        if not actor:
            return report
        report['approval'] = {'operator_declared': actor, 'plan_id': plan['id'], 'at': stamp()}
        execution = {'tool': 'lab_a8.software_update_demo.install', 'started_at': stamp()}
        report['execution'] = execution
        try:
            if sha256(candidate) != plan['candidate_sha256'] or sha256(active) != before['sha256']:
                raise ValueError('Artifact changed after planning')
            change(active, candidate)
            execution['status'] = 'SUCCEEDED'
        except Exception as exc:
            execution.update(status='FAILED', error_type=type(exc).__name__)
        execution['finished_at'] = stamp()
        try:
            report['after'] = observe(active)
        except Exception as exc:
            report['verification_error'] = type(exc).__name__
        if execution['status'] == 'FAILED':
            report['status'] = 'EXECUTION_FAILED'
        elif report['after'] is None:
            report['status'] = 'VERIFICATION_UNAVAILABLE'
        elif report['after']['met'] and report['after']['sha256'] == plan['candidate_sha256']:
            report['status'] = 'VERIFIED_MET'
        else:
            report['after']['met'] = False
            report['status'] = 'VERIFIED_NOT_MET'
        return report


def interactive_approval(plan, before):
    print(json.dumps({'before': before, 'plan': plan}, indent=2), flush=True)
    try:
        name = input('Lab operator name (leave empty to decline): ').strip()
        if name and input('Enter APPROVE followed by the plan ID: ').strip() == 'APPROVE ' + plan['id']:
            return name
    except EOFError:
        pass
    return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x', encoding='utf-8') as output:
        receipt = run_demo(interactive_approval)
        output.write(json.dumps(receipt, indent=2) + '\n')
    print(receipt['status'])
