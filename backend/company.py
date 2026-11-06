"""Assessment-scoped corporate inventory; historical benchmark fixtures stay offline."""
import copy
import hashlib
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from psycopg.types.json import Jsonb
from backend.database import get_connection
from agent_core.simulation import build_enterprise, CONTROLS


def canonical_employee(identifier):
    import re
    match = re.fullmatch(r'(?:HF|EMP)-(\d{3})', identifier.upper())
    if not match:
        raise ValueError('Mã nhân viên không hợp lệ.')
    return 'EMP-' + match.group(1)


def initialize_company():
    """Additive only: preserve every existing person, device, relationship and incident."""
    fixture = build_enterprise()
    fields = {f for _, _, checks, _, _ in CONTROLS for f in checks}
    with get_connection() as con, con.cursor() as cur:
        cur.execute('''CREATE TABLE IF NOT EXISTS enterprise_company (
            assessment_id UUID PRIMARY KEY REFERENCES assessment_campaigns(assessment_id),
            metadata JSONB NOT NULL, updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())''')
        cur.execute('''CREATE TABLE IF NOT EXISTS enterprise_company_accounts (
            assessment_id UUID NOT NULL, account_id TEXT NOT NULL, employee_id TEXT NOT NULL,
            system_name TEXT NOT NULL, state JSONB NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY(assessment_id,account_id),
            FOREIGN KEY(assessment_id,employee_id) REFERENCES enterprise_sim_people(assessment_id,employee_id))''')
        cur.execute('''CREATE TABLE IF NOT EXISTS enterprise_company_changes (
            change_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            assessment_id UUID NOT NULL REFERENCES assessment_campaigns(assessment_id),
            employee_id TEXT, action TEXT NOT NULL, before_state JSONB, after_state JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())''')
        cur.execute('ALTER TABLE enterprise_company_changes ADD COLUMN IF NOT EXISTS submitted_by UUID REFERENCES team_users(user_id)')
        cur.execute('''INSERT INTO enterprise_company(assessment_id,metadata)
            SELECT assessment_id,%s FROM assessment_campaigns ON CONFLICT DO NOTHING''',
            (Jsonb({'assessment_date': datetime.now(ZoneInfo('Asia/Bangkok')).date().isoformat(),
                    'policies': fixture['policies'], 'schema_version': 1}),))
        for person in fixture['people']:
            eid = canonical_employee(person['id'])
            profile = {k: person[k] for k in fields}
            profile.update(remote=person['remote'], profile_origin='synthetic_baseline_v1')
            cur.execute('''INSERT INTO enterprise_sim_people
                (assessment_id,employee_id,display_name,department,job_title,employment_status,account_status,state)
                SELECT assessment_id,%s,%s,%s,%s,'active','active',%s FROM assessment_campaigns
                ON CONFLICT DO NOTHING''', (eid, f'Nhân sự mô phỏng {eid[-3:]}', person['department'], person['role'], Jsonb(profile)))
        # Existing staff with incomplete profiles remain incomplete. Do not infer
        # signed contracts or training completion from a preset or model response.
        for system in ('HR', 'Email', 'VPN', 'Nghiệp vụ'):
            cur.execute('''INSERT INTO enterprise_company_accounts
                (assessment_id,account_id,employee_id,system_name,state)
                SELECT assessment_id,employee_id||'-'||%s,employee_id,%s,
                    jsonb_build_object('active',CASE WHEN account_status='active' THEN TRUE
                        WHEN account_status='disabled' THEN FALSE ELSE NULL END,
                        'mfa',NULL,'access','Theo vai trò','origin','migration_v1')
                FROM enterprise_sim_people ON CONFLICT DO NOTHING''', (system, system))
        # Only explicitly named personal accounts with one unambiguous owner.
        # Shared services remain assets; they are not invented personal logins.
        cur.execute('''INSERT INTO enterprise_company_accounts
            (assessment_id,account_id,employee_id,system_name,state)
            SELECT a.assessment_id,'ACCOUNT-'||a.asset_id,MIN(ap.employee_id),a.asset_name,
                jsonb_build_object('active',NULL,'mfa',NULL,'asset_id',a.asset_id,'origin','linked_software_asset')
            FROM enterprise_sim_assets a JOIN enterprise_sim_asset_people ap
                ON ap.assessment_id=a.assessment_id AND ap.asset_id=a.asset_id
            WHERE a.asset_type='software' AND a.asset_name ILIKE '%%tài khoản%%'
            GROUP BY a.assessment_id,a.asset_id,a.asset_name
            HAVING COUNT(DISTINCT ap.employee_id)=1 ON CONFLICT DO NOTHING''')


def project_company(assessment_id, people, accounts, assets, metadata):
    projected_people = []
    for p in people:
        state = copy.deepcopy(p.get('state') or {})
        if state.get('training_status') in {'assigned', 'not_assigned', 'incomplete'}:
            state.update(training_complete=False, training_passed=False)
        # Column values are authoritative for identity and employment state.
        projected_people.append({**state, 'id': p['employee_id'], 'employee_id': p['employee_id'],
            'legacy_id': 'HF-' + p['employee_id'][-3:], 'name': p['display_name'],
            'department': p['department'], 'role': p['job_title'], 'status': p['employment_status'],
            'account_status': p['account_status'], 'remote': state.get('remote')})
    projected_accounts = []
    assets_by_id = {a['asset_id']: a for a in assets}
    for a in accounts:
        state = copy.deepcopy(a['state'])
        linked = assets_by_id.get(state.get('asset_id'))
        if linked:
            account_state = linked['state'].get('account_status')
            if account_state in {'active','disabled'}:
                state['active'] = account_state == 'active'
        owner = next(p for p in people if p['employee_id'] == a['employee_id'])
        if owner['account_status'] == 'disabled':
            state['active'] = False
        projected_accounts.append({**state, 'id': a['account_id'], 'person_id': a['employee_id'], 'system': a['system_name']})
    devices = []
    for asset in assets:
        if asset['asset_type'] != 'hardware':
            continue
        state = copy.deepcopy(asset['state'])
        devices.append({**state, 'id': asset['asset_id'], 'person_id': asset.get('employee_id'),
            'type': asset['asset_name'],
            'encrypted': {'enabled':True,'disabled':False}.get(state.get('encryption_status'), state.get('encrypted')),
            'returned': state.get('returned', False)})
    result = {'name': 'HiveFive', 'assessment_id': str(assessment_id), 'synthetic': True,
        'source': 'postgresql://assessment/company', 'schema_version': 1,
        'assessment_date': metadata['assessment_date'], 'policies': metadata['policies'],
        'lab_config': metadata.get('lab_config', {}),
        'people': projected_people, 'accounts': projected_accounts, 'devices': devices,
        'assets': assets, 'policy_note': 'Chính sách lab, không phải kết luận chứng nhận ISO.'}
    result['snapshot_hash'] = hashlib.sha256(json.dumps(result, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()
    from agent_core.live import ACTIONS
    result['actions'] = [{'id': key, 'name': value} for key, value in ACTIONS.items()]
    return result


def snapshot(assessment_id, cur=None):
    if cur is None:
        with get_connection() as con, con.cursor() as cursor:
            cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            return snapshot(assessment_id, cursor)
    cur.execute('SELECT metadata FROM enterprise_company WHERE assessment_id=%s', (assessment_id,))
    row = cur.fetchone()
    if not row:
        raise ValueError('Đợt đánh giá chưa có doanh nghiệp; khởi động lại API để khởi tạo.')
    metadata = row[0]
    cur.execute('SELECT node_key,scenario,revision FROM enterprise_lab_nodes WHERE assessment_id=%s ORDER BY node_key', (assessment_id,))
    metadata = {**metadata, 'lab_config': {r[0]: {'scenario': r[1], 'revision': r[2]} for r in cur.fetchall()}}
    cur.execute('''SELECT employee_id,display_name,department,job_title,employment_status,account_status,state
        FROM enterprise_sim_people WHERE assessment_id=%s ORDER BY employee_id''', (assessment_id,))
    people = [dict(zip(('employee_id','display_name','department','job_title','employment_status','account_status','state'), r)) for r in cur.fetchall()]
    cur.execute('''SELECT account_id,employee_id,system_name,state FROM enterprise_company_accounts
        WHERE assessment_id=%s ORDER BY account_id''', (assessment_id,))
    accounts = [dict(zip(('account_id','employee_id','system_name','state'), r)) for r in cur.fetchall()]
    cur.execute('''SELECT a.asset_id,a.asset_type,a.asset_name,a.state,
        (SELECT MIN(ap.employee_id) FROM enterprise_sim_asset_people ap WHERE ap.assessment_id=a.assessment_id
         AND ap.asset_id=a.asset_id AND ap.relationship IN ('responsible_employee','affected_employee')),
        COALESCE((SELECT jsonb_agg(jsonb_build_object('employee_id',ap.employee_id,'relationship',ap.relationship)
            ORDER BY ap.employee_id,ap.relationship) FROM enterprise_sim_asset_people ap
            WHERE ap.assessment_id=a.assessment_id AND ap.asset_id=a.asset_id),'[]'::jsonb)
        FROM enterprise_sim_assets a WHERE a.assessment_id=%s ORDER BY a.asset_id''', (assessment_id,))
    assets = [dict(zip(('asset_id','asset_type','asset_name','state','employee_id','relationships'), r)) for r in cur.fetchall()]
    return project_company(assessment_id, people, accounts, assets, metadata)


def change(assessment_id, employee_id, action, cur=None, actor_id=None):
    from agent_core.live import apply_business_change
    eid = canonical_employee(employee_id)
    if cur is None:
        with get_connection() as con, con.cursor() as cursor:
            return change(assessment_id, employee_id, action, cursor, actor_id=actor_id)
    from backend.office_logic import lock_key
    cur.execute('SELECT pg_try_advisory_xact_lock(hashtextextended(%s,0))', (lock_key(assessment_id,eid),))
    if not cur.fetchone()[0]:
        raise ValueError('SOC đang xử lý nhân viên này. Chờ kết quả trước khi thay đổi hồ sơ.')
    # Serialize business events and coordinate with the per-employee SOC guard.
    cur.execute('SELECT metadata FROM enterprise_company WHERE assessment_id=%s FOR UPDATE', (assessment_id,))
    if not cur.fetchone():
        raise ValueError('Không tìm thấy doanh nghiệp.')
    cur.execute('SELECT employee_id FROM enterprise_sim_people WHERE assessment_id=%s AND employee_id=%s FOR UPDATE', (assessment_id,eid))
    cur.fetchall()
    cur.execute('SELECT account_id FROM enterprise_company_accounts WHERE assessment_id=%s AND employee_id=%s ORDER BY account_id FOR UPDATE', (assessment_id,eid))
    cur.fetchall()
    cur.execute('''SELECT asset_id FROM enterprise_sim_assets WHERE assessment_id=%s AND asset_id IN
        (SELECT asset_id FROM enterprise_sim_asset_people WHERE assessment_id=%s AND employee_id=%s)
        ORDER BY asset_id FOR UPDATE''', (assessment_id,assessment_id,eid))
    cur.fetchall()
    data = snapshot(assessment_id, cur)
    before, after = apply_business_change(data, eid, action)
    if before == after:
        return {'changed': False, 'snapshot_hash': data['snapshot_hash'], 'revision': int(data['snapshot_hash'][:12],16)}
    person = after['person']
    state = {k: v for k, v in person.items() if k not in {'id','employee_id','legacy_id','name','department','role','status','account_status'}}
    account_status = 'disabled' if after['accounts'] and all(a.get('active') is False for a in after['accounts']) else ('active' if any(a.get('active') is True for a in after['accounts']) else 'pending')
    if action.startswith('training_'):
        state['training_status'] = 'current' if person.get('training_passed') is True else ('incomplete' if person.get('training_passed') is False else 'not_verified')
        person['training_status'] = state['training_status']
    person['account_status'] = account_status
    cur.execute('''UPDATE enterprise_sim_people SET employment_status=%s,account_status=%s,
        job_title=%s,state=%s,updated_at=NOW() WHERE assessment_id=%s AND employee_id=%s''',
        (person['status'],account_status,person['role'],Jsonb(state),assessment_id,eid))
    for account in after['accounts']:
        value = {k: v for k,v in account.items() if k not in {'id','person_id','system'}}
        cur.execute('UPDATE enterprise_company_accounts SET state=%s,updated_at=NOW() WHERE assessment_id=%s AND account_id=%s', (Jsonb(value),assessment_id,account['id']))
        if value.get('asset_id') and isinstance(value.get('active'),bool):
            cur.execute('UPDATE enterprise_sim_assets SET state=state||%s,updated_at=NOW() WHERE assessment_id=%s AND asset_id=%s',
                (Jsonb({'account_status':'active' if value['active'] else 'disabled'}),assessment_id,value['asset_id']))
    original_devices = {d['id']: d for d in before['devices']}
    for device in after['devices']:
        changes = {k:v for k,v in device.items() if k not in {'id','person_id','type'} and original_devices[device['id']].get(k) != v}
        if changes.get('returned') is True and device['id'].startswith('OFFICE-'):
            changes.update(shift='off',location='reception',screen_state='locked',device_status='locked')
        if isinstance(changes.get('encrypted'),bool):
            changes['encryption_status'] = 'enabled' if changes['encrypted'] else 'disabled'
        if changes:
            cur.execute('UPDATE enterprise_sim_assets SET state=state||%s,updated_at=NOW() WHERE assessment_id=%s AND asset_id=%s', (Jsonb(changes),assessment_id,device['id']))
            device.update(changes)
    if before['assessment_date'] != after['assessment_date']:
        cur.execute("UPDATE enterprise_company SET metadata=jsonb_set(metadata,'{assessment_date}',%s),updated_at=NOW() WHERE assessment_id=%s", (Jsonb(after['assessment_date']),assessment_id))
    cur.execute('''INSERT INTO enterprise_company_changes(assessment_id,employee_id,action,before_state,after_state,submitted_by)
        VALUES(%s,%s,%s,%s,%s,%s) RETURNING change_id''', (assessment_id,eid,action,Jsonb(before),Jsonb(after),actor_id))
    change_id = cur.fetchone()[0]
    updated = snapshot(assessment_id,cur)
    return {'changed': True, 'change_id': change_id, 'snapshot_hash': updated['snapshot_hash'],
            'revision': int(updated['snapshot_hash'][:12],16), 'employee_id': eid}


def apply_scenario(assessment_id, scenario_id, actor_id=None):
    from agent_core.simulation import SCENARIOS
    if scenario_id not in {s['id'] for s in SCENARIOS}:
        raise ValueError('Không tìm thấy tình huống.')
    with get_connection() as con, con.cursor() as cur:
        cur.execute('SELECT metadata FROM enterprise_company WHERE assessment_id=%s FOR UPDATE', (assessment_id,))
        if not cur.fetchone():
            raise ValueError('Không tìm thấy doanh nghiệp.')
        data = snapshot(assessment_id, cur)
        action = {'new-hire': 'nda_missing', 'training': 'training_missing',
                  'phishing': 'report_missing', 'offboarding': 'terminate', 'remote': 'remote_unprotected'}.get(scenario_id)
        if action:
            people = data['people'][-8:] if scenario_id == 'training' else data['people'][-1:]
            for person in people:
                change(assessment_id, person['id'], action, cur, actor_id=actor_id)
        return snapshot(assessment_id, cur)
