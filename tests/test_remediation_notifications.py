from contextlib import contextmanager
from copy import deepcopy
from datetime import date,datetime,timezone
from threading import Event
from uuid import UUID
import pytest
from fastapi import HTTPException
from backend import remediation_notifications as notifications
from backend.remediation_notifications import start as start_worker


def document():
    return {'finding_id':'finding','control_id':'A.8.13','actions':[
        {'action_id':'action','title':'Test restore verification','assignee':'operator','due_date':'2026-11-25','state':'IN_PROGRESS'}]}


def test_deadline_policy_uses_three_day_window_without_rewriting_work():
    doc=document();original=deepcopy(doc)
    assert notifications.due_items(doc,date(2026,11,21))==[]
    soon=notifications.due_items(doc,date(2026,11,22))[0]
    assert soon['event_type']=='due_soon' and soon['recipient']=='operator'
    assert soon['dedupe']==notifications.due_items(doc,date(2026,11,22))[0]['dedupe']
    assert notifications.due_items(doc,date(2026,11,23))[0]['dedupe']!=soon['dedupe']
    assert notifications.due_items(doc,date(2026,11,26))[0]['event_type']=='overdue'
    assert doc==original


@pytest.mark.parametrize('change',[{'state':'CLOSED'},{'state':'VERIFIED'},{'state':'PENDING_APPROVAL'},
                                   {'assignee':None},{'due_date':'invalid'},{'due_date':None}])
def test_no_reminder_for_unassigned_finished_or_malformed_dates(change):
    doc=document();doc['actions'][0].update(change)
    assert notifications.due_items(doc,date(2026,11,26))==[]


def test_events_notify_correct_people_without_self_notifications(monkeypatch):
    sent=[]
    monkeypatch.setattr(notifications,'enqueue',lambda cur,aid,recipient,event,body,key:sent.append((recipient,event,body,key)) or True)
    class Cursor:
        def execute(self,sql,args):assert args==('tenant',)
        def fetchall(self):return [('consultant',),('verifier',),('operator',)]
    doc=document()
    assert notifications.notify_event(Cursor(),'tenant',doc,'action','approve','consultant',2)==1
    assert sent[-1][0:2]==('operator','approve')
    sent.clear()
    notifications.notify_event(Cursor(),'tenant',doc,'action','submit','operator',3)
    assert {r[0] for r in sent}=={'consultant','verifier'}
    assert all(r[2]['finding_id']=='finding' for r in sent)
    keys={r[-1] for r in sent}
    assert len(keys)==1  # dedupe is per recipient in the unique DB constraint
    sent.clear()
    assert notifications.notify_event(Cursor(),'tenant',doc,'missing','approve','consultant',4)==0
    assert notifications.notify_event(Cursor(),'tenant',doc,'action','task','operator',4)==0
    assert not sent


def test_enqueue_is_membership_bound_and_idempotent_insert():
    class Cursor:
        def execute(self,sql,args):
            assert 'FROM assessment_members' in sql and 'ON CONFLICT(assessment_id,user_id,dedupe_key) DO NOTHING' in sql
            assert args[-2:]==('tenant','recipient')
        def fetchone(self):return None  # absent membership or duplicate, neither creates a row
    assert not notifications.enqueue(Cursor(),'tenant','recipient','approve',{'title':'test'},'same-event')
    assert not notifications.enqueue(Cursor(),'tenant',None,'approve',{},'event')


def connection_for(cursor):
    @contextmanager
    def connection():
        class Connection:
            @contextmanager
            def cursor(self):yield cursor
        yield Connection()
    return connection


def test_read_is_bound_to_user_and_campaign_even_for_known_foreign_notification(monkeypatch):
    aid=UUID(int=1);nid=UUID(int=2);user={'user_id':'actor'}
    monkeypatch.setattr(notifications,'require_campaign',lambda a,u:None)
    class Cursor:
        def execute(self,sql,args):
            assert 'assessment_id=%s AND user_id=%s AND notification_id=%s' in sql
            assert args==(aid,'actor',nid)
        def fetchone(self):return None
    monkeypatch.setattr(notifications,'get_connection',connection_for(Cursor()))
    with pytest.raises(HTTPException) as exc:notifications.mark_read(aid,nid,user)
    assert exc.value.status_code==404


def test_worker_can_stop_without_waiting_for_next_scan(monkeypatch):
    started=Event();calls=[]
    monkeypatch.setattr(notifications,'scan_due',lambda:calls.append(1) or started.set())
    stop=start_worker(interval_seconds=300)
    assert started.wait(2)
    stop()
    assert calls==[1]
