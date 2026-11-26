from contextlib import contextmanager
from datetime import datetime,timezone
from uuid import UUID
import pytest
from fastapi import HTTPException
from backend import source_search


def test_search_always_filters_tenant_control_and_bounds_results(monkeypatch):
    aid=UUID(int=1);seen=[]
    monkeypatch.setattr(source_search,'require_campaign',lambda a,u:seen.append(a))
    class Cursor:
        def execute(self,sql,args):
            assert 'WHERE assessment_id=%s' in sql and 'control_id=%s' in sql
            assert args==( 'backup','backup',aid,'A.8.13','A.8.13','backup',2)
        def fetchall(self):return [('e'+str(n),'A.8.13','BACKUP','source','hash','<untrusted> text',0.2,datetime.now(timezone.utc)) for n in range(2)]
    @contextmanager
    def connection():
        class Connection:
            @contextmanager
            def cursor(self):yield Cursor()
        yield Connection()
    monkeypatch.setattr(source_search,'get_connection',connection)
    result=source_search.search(aid,'backup','A.8.13',1,{'user_id':'u'})
    assert result['has_more'] and len(result['results'])==1 and seen==[aid]
    assert result['results'][0]['excerpt']=='<untrusted> text'


def test_foreign_tenant_denied_before_read(monkeypatch):
    def denied(*_):raise HTTPException(403,'foreign tenant')
    monkeypatch.setattr(source_search,'require_campaign',denied)
    monkeypatch.setattr(source_search,'get_connection',lambda:pytest.fail('No DB read after denial'))
    with pytest.raises(HTTPException):source_search.search(UUID(int=1),'backup',None,10,{'user_id':'u'})
