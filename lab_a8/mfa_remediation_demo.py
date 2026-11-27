"""Run one approved MFA policy change against a disposable lab authentication service."""
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import tempfile

if __package__:
    from .extended_probe import load, observe_auth, stamp, write_json
else:
    from extended_probe import load, observe_auth, stamp, write_json

TARGET = 'labadmin-mfa-demo'
POLICY = 'LAB-ADMIN-MFA'
SOURCE = 'lab://a8/mfa-disposable/loopback-auth'
CRITERION = 'second_factor_enforced'


def inspect_policy(path):
    config = load(path)
    observed = observe_auth(config)
    return {
        'source': SOURCE,
        'observed_at': stamp(),
        'target': TARGET,
        'policy': POLICY,
        'criterion': CRITERION,
        'policy_requires_second_factor': config['require_otp'],
        'observations': observed,
        'met': config['require_otp'] is True
        and observed['no_second_factor']['response'].startswith('403 ')
        and observed['authenticated']['response'].startswith('200 '),
    }


def apply_policy(path):
    config = load(path)
    config['require_otp'] = True
    replacement = path.with_suffix('.new')
    write_json(replacement, config)
    replacement.replace(path)


def run_demo(approve, change=apply_policy):
    # Every run owns a private temporary store. No caller-supplied target or tool.
    with tempfile.TemporaryDirectory(prefix='iso-a85-mfa-') as directory:
        path = Path(directory) / 'auth.json'
        salt = secrets.token_bytes(16)
        write_json(path, {
            'salt': salt.hex(),
            'password_hash': hashlib.pbkdf2_hmac(
                'sha256', b'lab-only-password', salt, 100000
            ).hex(),
            'require_password': True,
            'require_otp': False,
            'otp_key': secrets.token_hex(20),
        })
        before = inspect_policy(path)
        plan = {
            'id': secrets.token_hex(8),
            'target': TARGET,
            'policy': POLICY,
            'operation': 'require_second_factor',
            'recheck': 'Separate loopback logins with and without a second factor',
        }
        report = {
            'control': 'A.8.5', 'criterion': CRITERION,
            'environment': 'disposable synthetic lab with active authentication probes',
            'before': before, 'plan': plan, 'approval': None,
            'execution': None, 'after': None, 'status': 'AWAITING_APPROVAL',
        }
        approver = approve(plan, before)
        if not approver:
            return report
        report['approval'] = {'operator_declared': approver, 'plan_id': plan['id'], 'at': stamp()}
        execution = {'tool': 'lab_a8.mfa_remediation_demo.apply_policy', 'started_at': stamp()}
        report['execution'] = execution
        try:
            change(path)
            execution['status'] = 'SUCCEEDED'
        except Exception as error:
            execution.update(status='FAILED', error_type=type(error).__name__)
        execution['finished_at'] = stamp()
        try:
            report['after'] = inspect_policy(path)
        except Exception as error:
            report['verification_error'] = type(error).__name__
        if execution['status'] == 'FAILED':
            report['status'] = 'EXECUTION_FAILED'
        elif report['after'] is None:
            report['status'] = 'VERIFICATION_UNAVAILABLE'
        else:
            report['status'] = 'VERIFIED_MET' if report['after']['met'] else 'VERIFIED_NOT_MET'
        return report


def interactive_approval(plan, before):
    print(json.dumps({'before': before, 'plan': plan}, indent=2), flush=True)
    try:
        operator = input('Lab operator name (leave empty to decline): ').strip()
        if operator and input('Enter APPROVE followed by the plan ID: ').strip() == 'APPROVE ' + plan['id']:
            return operator
    except EOFError:
        pass
    return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    with args.output.open('x', encoding='utf-8') as output:
        report = run_demo(interactive_approval)
        output.write(json.dumps(report, indent=2) + '\n')
    print(report['status'])
