from agent_core.people_assessment import build_enterprise,evaluate_enterprise
from agent_core.business_events import apply_business_change


def result(data,cid):
    return next(c for c in evaluate_enterprise(data) if c['control_id']==cid)


def test_people_baseline_and_inventory_relationships():
    data=build_enterprise()
    assert len(data['people'])==50 and len(evaluate_enterprise(data))==8
    assert all(c['status']=='Compliant' for c in evaluate_enterprise(data))
    assert all(a['person_id'] in {p['id'] for p in data['people']} for a in data['accounts'])


def test_unknown_document_or_inventory_is_never_compliant():
    data=build_enterprise();data['people'][0]['nda_signed']=None
    assert result(data,'A.6.6')['status']=='Insufficient Evidence'
    data['accounts']=None
    assert result(data,'A.6.5')['status']=='Insufficient Evidence'


def test_training_event_changes_only_business_records_and_preserves_source_conflict():
    data=build_enterprise();eid=data['people'][0]['id']
    apply_business_change(data,eid,'training_missing')
    assert result(data,'A.6.3')['status']=='Partially Compliant'
    apply_business_change(data,eid,'training_conflict')
    assert eid in result(data,'A.6.3')['missing_evidence']
    apply_business_change(data,eid,'training_complete')
    assert result(data,'A.6.3')['status']=='Compliant'


def test_retention_approval_scope_and_expiry_remain_enforced():
    data=build_enterprise();eid=data['people'][0]['id']
    apply_business_change(data,eid,'terminate')
    apply_business_change(data,eid,'recover_access')
    account=next(a for a in data['accounts'] if a['person_id']==eid and a['system']=='HR')
    account['active']=True
    account['retention_exception']={'account_id':account['id'],'approved':True,'scope':'offboarding-retention',
        'approver':'lab manager','reason':'Limited handover','expires_on':'2026-10-31'}
    assert result(data,'A.6.5')['status']=='Compliant'
    data['assessment_date']='2026-11-01'
    assert result(data,'A.6.5')['status']=='Partially Compliant'
    data['assessment_date']='2026-10-30';account['retention_exception']['approved']='true'
    assert result(data,'A.6.5')['status']=='Partially Compliant'


def test_baseline_does_not_share_mutable_records():
    first=build_enterprise();first['people'][0]['nda_signed']=False
    assert build_enterprise()['people'][0]['nda_signed'] is True
