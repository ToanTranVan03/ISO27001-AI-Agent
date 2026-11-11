"""Additive assessment inventory storage, independent of retired office/SOC demos."""
import json
from pathlib import Path
from psycopg.types.json import Jsonb
from backend.database import get_connection

SEED=Path(__file__).resolve().parents[1]/'lab_company'/'inventory_seed.json'


def initialize_company_inventory():
    seed=json.loads(SEED.read_text(encoding='utf-8'))
    with get_connection() as con,con.cursor() as cur:
        cur.execute('''CREATE TABLE IF NOT EXISTS enterprise_sim_people (
            assessment_id UUID NOT NULL REFERENCES assessment_campaigns(assessment_id) ON DELETE CASCADE,
            employee_id TEXT NOT NULL,display_name TEXT NOT NULL,department TEXT NOT NULL,
            job_title TEXT NOT NULL,employment_status TEXT NOT NULL DEFAULT 'active',
            account_status TEXT NOT NULL DEFAULT 'active',state JSONB NOT NULL DEFAULT '{}'::jsonb,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),PRIMARY KEY(assessment_id,employee_id))''')
        cur.execute('''CREATE TABLE IF NOT EXISTS enterprise_sim_assets (
            assessment_id UUID NOT NULL REFERENCES assessment_campaigns(assessment_id) ON DELETE CASCADE,
            asset_id TEXT NOT NULL,asset_type TEXT NOT NULL,asset_name TEXT NOT NULL,department TEXT NOT NULL,
            state JSONB NOT NULL DEFAULT '{}'::jsonb,updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY(assessment_id,asset_id))''')
        cur.execute('''CREATE TABLE IF NOT EXISTS enterprise_sim_asset_people (
            assessment_id UUID NOT NULL,asset_id TEXT NOT NULL,employee_id TEXT NOT NULL,relationship TEXT NOT NULL,
            PRIMARY KEY(assessment_id,asset_id,employee_id,relationship),
            FOREIGN KEY(assessment_id,asset_id) REFERENCES enterprise_sim_assets(assessment_id,asset_id) ON DELETE CASCADE,
            FOREIGN KEY(assessment_id,employee_id) REFERENCES enterprise_sim_people(assessment_id,employee_id) ON DELETE CASCADE)''')
        for p in seed['people']:
            cur.execute('''INSERT INTO enterprise_sim_people
                (assessment_id,employee_id,display_name,department,job_title,employment_status,account_status,state)
                SELECT assessment_id,%s,%s,%s,%s,%s,%s,%s FROM assessment_campaigns ON CONFLICT DO NOTHING''',
                (p['employee_id'],p['display_name'],p['department'],p['job_title'],p['employment_status'],p['account_status'],Jsonb(p['state'])))
        for a in seed['assets']:
            cur.execute('''INSERT INTO enterprise_sim_assets
                (assessment_id,asset_id,asset_type,asset_name,department,state)
                SELECT assessment_id,%s,%s,%s,%s,%s FROM assessment_campaigns ON CONFLICT DO NOTHING''',
                (a['asset_id'],a['asset_type'],a['asset_name'],a['department'],Jsonb(a['state'])))
        for r in seed['relationships']:
            cur.execute('''INSERT INTO enterprise_sim_asset_people
                (assessment_id,asset_id,employee_id,relationship)
                SELECT assessment_id,%s,%s,%s FROM assessment_campaigns ON CONFLICT DO NOTHING''',
                (r['asset_id'],r['employee_id'],r['relationship']))
    # Expands to the canonical 50-person inventory, preserving all existing rows.
    from backend.company import initialize_company
    initialize_company()
    with get_connection() as con,con.cursor() as cur:
        cur.execute('''INSERT INTO enterprise_sim_assets
            (assessment_id,asset_id,asset_type,asset_name,department,state)
            SELECT assessment_id,'OFFICE-'||employee_id,'hardware','Máy làm việc '||employee_id,department,%s
            FROM enterprise_sim_people ON CONFLICT DO NOTHING''',
            (Jsonb({'device_status':'available','encrypted':None,'returned':False,'is_synthetic':True}),))
        cur.execute('''INSERT INTO enterprise_sim_asset_people
            (assessment_id,asset_id,employee_id,relationship)
            SELECT assessment_id,'OFFICE-'||employee_id,employee_id,'responsible_employee'
            FROM enterprise_sim_people ON CONFLICT DO NOTHING''')
