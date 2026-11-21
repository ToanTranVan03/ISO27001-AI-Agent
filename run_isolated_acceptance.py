"""Real HTTP/browser writes against a disposable database, never the main campaign."""
import argparse
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict,make_conninfo
import requests

ROOT=Path(__file__).resolve().parent


def validate_database(name,source):
    import re
    if not re.fullmatch(r'iso_acceptance_[a-f0-9]{12}',name) or name==source:
        raise ValueError('Only a newly generated disposable acceptance database is allowed')


def prepare_regression_candidate(directory):
    """Artificial content variants for transport tests; never held-out data."""
    import shutil
    from agent_core import a8_assessment as a8
    from agent_core.a8_protocol import prepare
    root=directory/'candidate-regression-sources'
    shutil.copytree(a8.LAB/'raw/mixed',root/'mixed')
    for path in (root/'mixed').glob('*/*'):
        if not path.is_file() or path.name=='capture.json':continue
        if path.suffix=='.json':
            value=json.loads(path.read_text(encoding='utf-8'))
            if isinstance(value,dict):value['synthetic_test_record']='NOT INDEPENDENT DATA'
            path.write_text(json.dumps(value),encoding='utf-8')
        else:path.write_bytes(path.read_bytes()+b'\nSYNTHETIC TRANSPORT TEST ONLY: NOT INDEPENDENT DATA\n')
    plan=prepare('mixed','files','Synthetic integration test',
        'Modified known development fixture for API/worker transport only; never independent validation',raw_root=root)
    target=directory/'candidate-regression-plan.json'
    target.write_text(json.dumps(plan,ensure_ascii=False),encoding='utf-8')
    return target


def serve():
    options=conninfo_to_dict(os.environ['DATABASE_URL'])
    validate_database(options['dbname'],os.environ['ISO_SOURCE_DBNAME'])
    directory=Path(os.environ['ISO_ISOLATED_DIRECTORY']).resolve()
    if not directory.is_relative_to((ROOT/'work').resolve()):raise ValueError('Test storage outside work/')
    from backend import a8_api
    from evidence_collectors import source_intake,control_packages
    a8_api.STORE=directory/'a8-study'
    source_intake.ORIGINALS=directory/'evidence-originals'
    control_packages.ROOT=directory/'evidence-packages'
    from backend.main import app
    import uvicorn
    uvicorn.run(app,host='127.0.0.1',port=int(os.environ['ISO_ISOLATED_PORT']),access_log=False)


def main():
    from dotenv import load_dotenv
    load_dotenv(ROOT/'.env')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true',help='Create, test and drop only a disposable database')
    parser.add_argument('--output',required=True)
    parser.add_argument('--extended',action='store_true',help='Also exercise real Ollama batch and candidate worker on disposable data')
    args=parser.parse_args()
    if not args.execute:parser.error('--execute is required')
    output=Path(args.output)
    if output.exists():parser.error('Output exists; preserve prior reports')
    source=conninfo_to_dict(os.environ['DATABASE_URL'])
    if source.get('host') not in ('localhost','127.0.0.1','::1'):parser.error('Local PostgreSQL only')
    name='iso_acceptance_'+uuid4().hex[:12];validate_database(name,source['dbname'])
    directory=ROOT/'work'/name;directory.mkdir(parents=True,exist_ok=False)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    env=os.environ.copy();env.update(DATABASE_URL=make_conninfo(**{**source,'dbname':name}),
        INITIAL_ADMIN_USERNAME='release_admin',INITIAL_ADMIN_PASSWORD=secrets.token_urlsafe(24),
        ISO_ASSESSOR_PASSWORD=secrets.token_urlsafe(24),ISO_SOURCE_DBNAME=source['dbname'],
        ISO_ISOLATED_DIRECTORY=str(directory),ISO_ISOLATED_PORT=str(port),ISO_ISOLATED_TEST='1',
        ISO_ISOLATED_DBNAME=name,UI_BASE_URL=f'http://127.0.0.1:{port}')
    report=dict(protocol='isolated-real-write-acceptance-v1',checked_at=datetime.now(ZoneInfo('Asia/Bangkok')).isoformat(),
        database=name,test_data_only=True,human_assessment=False,professional_approval=False,
        api_mocked=False,passed=False,database_dropped=False,main_table_counts_unchanged=False)
    if args.extended:
        env['ISO_ISOLATED_CANDIDATE_PATH']=str(prepare_regression_candidate(directory))
        env['ISO_ISOLATED_ORCHESTRATION_RECEIPT']=str(directory/'orchestration-receipt.json')
        report['extended_orchestration']=dict(batch_engine='real-configured-Ollama',candidate_engine='rules',
            candidate_data='modified-known-fixture-transport-regression-not-independent')
    child=None;created=False
    def counts(connection):
        with connection.cursor() as cur:
            result={}
            for table in ('evidence','evaluations','team_users'):
                cur.execute(sql.SQL('SELECT COUNT(*) FROM {}').format(sql.Identifier(table)))
                result[table]=cur.fetchone()[0]
            return result
    with psycopg.connect(os.environ['DATABASE_URL'],autocommit=True) as admin:
        before=counts(admin)
        try:
            admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)));created=True
            with (directory/'backend.log').open('w',encoding='utf-8') as log:
                child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--serve'],cwd=ROOT,env=env,
                    stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
                for _ in range(90):
                    if child.poll() is not None:raise RuntimeError('Isolated backend exited; see work/ log')
                    try:
                        if requests.get(env['UI_BASE_URL']+'/openapi.json',timeout=1).status_code==200:break
                    except requests.RequestException:pass
                    time.sleep(.5)
                else:raise RuntimeError('Isolated backend startup timed out')
                runner=ROOT/'frontend-react/node_modules/@playwright/test/cli.js'
                specs=['tests/live-isolated.spec.js']+(['tests/live-orchestration.spec.js'] if args.extended else [])
                result=subprocess.run(['node',str(runner),'test',*specs,'--workers=1','--reporter=list','--output',str(directory/'browser-results')],
                    cwd=ROOT/'frontend-react',env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=420 if args.extended else 240)
                (directory/'browser.log').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
                report['browser_exit_code']=result.returncode
                report['passed']=result.returncode==0
                if args.extended and (directory/'orchestration-receipt.json').is_file():
                    report['orchestration_receipt']=json.loads((directory/'orchestration-receipt.json').read_text(encoding='utf-8'))
                with psycopg.connect(env['DATABASE_URL']) as con:report['synthetic_database_counts']=counts(con)
        except Exception as exc:
            report['error']=type(exc).__name__+': '+str(exc)
        finally:
            if child is not None and child.poll() is None:
                if os.name=='nt':
                    subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True,timeout=15)
                else:child.terminate()
                try:child.wait(timeout=10)
                except subprocess.TimeoutExpired:child.kill();child.wait(timeout=10)
            if created:
                validate_database(name,source['dbname'])
                admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))
                report['database_dropped']=True
            report['main_table_counts_unchanged']=counts(admin)==before
    report['passed']=report['passed'] and report['database_dropped'] and report['main_table_counts_unchanged']
    report['note']='Synthetic integration test only. Real requests on a disposable database; no member grades, source validation or professional SoA approval.'
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as stream:json.dump(report,stream,ensure_ascii=False,indent=2)
    print(json.dumps(report,ensure_ascii=True))
    return 0 if report['passed'] else 1


if __name__=='__main__':
    if sys.argv[1:]==['--serve']:serve()
    else:raise SystemExit(main())
