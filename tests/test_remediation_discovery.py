from contextlib import contextmanager
from copy import deepcopy
from uuid import UUID
from backend import remediation_api as api,enterprise_api


def test_discovery_uses_current_nonpreset_results_and_is_idempotent(monkeypatch):
    from test_remediation import control
    base=control();base.update(explicit_source_count=1,assessment_state='evaluated')
    preset=deepcopy(base);preset.update(control_id='A.6.2',explicit_source_count=0)
    pending=deepcopy(base);pending.update(control_id='A.6.3',assessment_state='not_evaluated')
    records=[]
    class Cursor:
        def execute(self,sql,args):
            if sql.startswith('INSERT'):records.append(args[-1].obj)
        def fetchone(self):return (1,{'name':'Synthetic test scope'})
        def fetchall(self):return [(r,) for r in records]
        def __enter__(self):return self
        def __exit__(self,*args):pass
    class Connection:
        def cursor(self):return Cursor()
    @contextmanager
    def connect():yield Connection()
    monkeypatch.setattr(api,'get_connection',connect)
    monkeypatch.setattr(api,'membership',lambda *_:'consultant')
    monkeypatch.setattr(enterprise_api,'scope56',lambda *_:{'controls':[base,preset,pending],'rubric_sha256':'rubric'})
    result=api.discover(UUID(int=1),{'user_id':'consultant'})
    assert len(result['inserted'])==1 and len(records)==1
    assert records[0]['control_id']=='A.8.13' and not records[0]['finding_confirmed']
    assert records[0]['actions']==[] and records[0]['risk']=='unconfirmed'
    assert api.discover(UUID(int=1),{'user_id':'consultant'})['inserted']==[]
