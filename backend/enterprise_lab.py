"""Persistent synthetic organization + lab collectors for Stage 2.

No Docker socket, no shell commands and no scanning external systems. All data
originates in PostgreSQL lab fixtures; every assessment has separate scenarios.
"""
import json
from typing import Any
from psycopg.types.json import Jsonb
from backend.database import get_connection
from backend.enterprise_spec import NODE_SPECS, CONTROL_TO_NODE, PRESETS, make_snapshot


def init_enterprise_lab() -> None:
    """Safe additive migration + idempotent seed for the existing campaign(s)."""
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute('''CREATE TABLE IF NOT EXISTS enterprise_lab_nodes (
                assessment_id UUID NOT NULL REFERENCES assessment_campaigns(assessment_id),
                node_key TEXT NOT NULL,
                scenario TEXT NOT NULL DEFAULT 'partial',
                revision INTEGER NOT NULL DEFAULT 1,
                changed_by UUID REFERENCES team_users(user_id),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (assessment_id, node_key),
                CHECK (scenario IN ('healthy','partial','gap'))
            )''')
            cur.execute("ALTER TABLE evidence ADD COLUMN IF NOT EXISTS is_synthetic BOOLEAN NOT NULL DEFAULT FALSE")
            cur.execute("ALTER TABLE evidence ADD COLUMN IF NOT EXISTS evidence_origin TEXT NOT NULL DEFAULT 'USER_UPLOAD'")
            for key in NODE_SPECS:
                cur.execute('''INSERT INTO enterprise_lab_nodes (assessment_id,node_key)
                               SELECT assessment_id, %s FROM assessment_campaigns
                               ON CONFLICT DO NOTHING''', (key,))


def get_lab_nodes(assessment_id: str) -> list[dict[str, Any]]:
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute('''SELECT node_key,scenario,revision,updated_at
                           FROM enterprise_lab_nodes WHERE assessment_id=%s''', (assessment_id,))
            found = {row[0]: row for row in cur.fetchall()}
    result=[]
    for key, spec in NODE_SPECS.items():
        row = found.get(key)
        if row is None:
            raise ValueError('Lab assessment has not been initialized. Restart the API.')
        result.append({
            'key':key, 'name':spec['title'], 'description':spec['description'],
            'department':spec['department'], 'icon':spec['icon'],
            'controls':spec['controls'], 'tool':spec['tool'],
            'scenario':row[1], 'revision':row[2],
            'facts':spec['values'][row[1]], 'updated_at':row[3].isoformat(),
            'is_synthetic':True,
        })
    return result


def change_scenario(assessment_id: str, node_key: str, scenario: str, user_id: str) -> dict:
    if node_key not in NODE_SPECS or scenario not in PRESETS:
        raise ValueError('Unknown lab node or scenario.')
    controls = NODE_SPECS[node_key]['controls']
    with get_connection() as con:
        with con.cursor() as cur:
            # Serialize changes by row locking. Do not invalidate an active job.
            cur.execute('''SELECT scenario,revision FROM enterprise_lab_nodes
                           WHERE assessment_id=%s AND node_key=%s FOR UPDATE''',
                        (assessment_id,node_key))
            previous = cur.fetchone()
            if not previous:
                raise ValueError('Lab node not initialized.')
            cur.execute('''SELECT control_id,workflow_status FROM control_progress
                           WHERE assessment_id=%s AND control_id=ANY(%s) FOR UPDATE''',
                        (assessment_id, controls))
            progress = cur.fetchall()
            if any(row[1] == 'RUNNING' for row in progress):
                raise RuntimeError('Agent đang chạy control này. Hãy đổi tình huống sau khi job hoàn thành.')
            if scenario == previous[0]:
                return {'node_key':node_key,'scenario':scenario,'revision':previous[1], 'changed':False}
            cur.execute('''UPDATE enterprise_lab_nodes SET scenario=%s,revision=revision+1,
                           changed_by=%s,updated_at=NOW()
                           WHERE assessment_id=%s AND node_key=%s RETURNING revision''',
                        (scenario,user_id,assessment_id,node_key))
            revision = cur.fetchone()[0]
            # Old evaluations remain in history, but are now stale in the progress board.
            cur.execute('''UPDATE control_progress SET workflow_status='NOT_STARTED',
                           compliance_status=NULL,latest_evaluation_id=NULL,
                           assigned_to=NULL,completed_at=NULL,updated_at=NOW()
                           WHERE assessment_id=%s AND control_id=ANY(%s)''',
                        (assessment_id,controls))
            for control_id in controls:
                cur.execute('''INSERT INTO assessment_events
                               (assessment_id,control_id,user_id,event_type,details)
                               VALUES (%s,%s,%s,'LAB_SCENARIO_CHANGED',%s)''',
                            (assessment_id,control_id,user_id,Jsonb({
                                'node_key':node_key,'scenario':scenario,'revision':revision,
                                'is_synthetic':True,
                            })))
    return {'node_key':node_key,'scenario':scenario,'revision':revision,'changed':True}


def collect_lab_snapshot(assessment_id: str, control_id: str) -> dict | None:
    """A stateful collector: READ lab config, WRITE immutable evidence snapshot.

    This is called by the Agent graph. It never reads ground-truth labels or
    claims that synthetic records represent a real corporate service.
    """
    node_key = CONTROL_TO_NODE.get(control_id)
    if node_key is None:
        return None
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute('''SELECT scenario,revision FROM enterprise_lab_nodes
                           WHERE assessment_id=%s AND node_key=%s''',
                        (assessment_id,node_key))
            row = cur.fetchone()
            if not row:
                raise ValueError('Enterprise lab not initialized.')
            snapshot=make_snapshot(assessment_id,node_key,row[0],row[1])
            cur.execute('''INSERT INTO evidence
                           (evidence_id,control_id,evidence_type,source,extracted_text,
                            sha256_hash,is_sample,assessment_id,is_synthetic,evidence_origin)
                           VALUES (%s,%s,%s,%s,%s,%s,FALSE,%s,TRUE,%s)
                           ON CONFLICT (evidence_id) DO NOTHING''',
                        (snapshot['evidence_id'], control_id,snapshot['evidence_type'],
                         snapshot['source'],snapshot['extracted_text'],snapshot['sha256_hash'],
                         assessment_id,snapshot['origin']))
            if cur.rowcount:
                cur.execute('''INSERT INTO assessment_events
                               (assessment_id,control_id,event_type,details)
                               VALUES (%s,%s,'LAB_EVIDENCE_COLLECTED',%s)''',
                            (assessment_id,control_id,Jsonb({
                                'evidence_id':snapshot['evidence_id'],
                                'sha256_hash':snapshot['sha256_hash'],
                                'source':snapshot['source'],
                                'is_synthetic':True,
                            })))
    return {k:snapshot[k] for k in ('evidence_id','control_id','source','sha256_hash')}


def list_lab_evidence(assessment_id: str, control_id: str) -> list[dict]:
    with get_connection() as con:
        with con.cursor() as cur:
            cur.execute('''SELECT evidence_id, source, sha256_hash, created_at, extracted_text
                           FROM evidence WHERE assessment_id=%s AND control_id=%s
                           AND is_synthetic=TRUE ORDER BY created_at DESC LIMIT 30''',
                        (assessment_id,control_id))
            rows=cur.fetchall()
    result=[]
    for row in rows:
        try: payload=json.loads(row[4])
        except (ValueError,TypeError):payload={}
        result.append({'evidence_id':row[0],'source':row[1],
                       'sha256_hash':row[2],'created_at':row[3].isoformat(),
                       'scenario':payload.get('scenario'),'revision':payload.get('revision'),
                       'facts':payload.get('facts',{}),'is_synthetic':True})
    return result
