import pytest
from backend.office_logic import DEFAULT_STATE, transition
from backend.incident_simulation import scenario_for_finding

def working():
    state,_=transition('/vao-ca',DEFAULT_STATE)
    return transition('/lam-viec',state)[0]

@pytest.mark.parametrize('command',['/lam-viec','/usb-la','/cai-app-la','/nghi','/roi-may','/khoa-may','/mo-khoa','/rut-usb','/go-app','/tan-ca'])
def test_off_shift_cannot_operate(command):
    with pytest.raises(ValueError): transition(command,DEFAULT_STATE)

def test_locked_departure_is_not_a_violation():
    state=working()
    after,event=transition('/roi-may',state)
    assert event=='unattended_screen_unlocked' and after['screen_state']=='unlocked'
    locked,_=transition('/khoa-may',state)
    after,event=transition('/roi-may',locked)
    assert event=='employee_left_locked' and after['screen_state']=='locked'
    assert state['location']=='desk'

def test_break_return_and_shift_end():
    state=working()
    state,_=transition('/nghi',state)
    with pytest.raises(ValueError): transition('/cai-app-la',state)
    state,_=transition('/lam-viec',state)
    assert state['location']=='desk' and state['screen_state']=='unlocked'
    with pytest.raises(ValueError): transition('/tan-ca',state)
    state,_=transition('/khoa-may',state)
    state,event=transition('/tan-ca',state)
    assert state['shift']=='off' and event=='employee_shift_ended'

def test_recovery_never_bypasses_pending_or_containment():
    state={**working(),'network_isolated':True,'device_status':'locked','screen_state':'locked'}
    returned,event=transition('/lam-viec',state)
    assert returned['screen_state']=='locked' and returned['network_isolated']
    with pytest.raises(ValueError): transition('/mo-khoa',state,pending=1)
    after,_=transition('/mo-khoa',state,pending=0)
    assert not after['network_isolated'] and after['device_status']=='available'

def test_risk_survives_normal_actions_and_requires_explicit_cleanup():
    state=working()
    state,_=transition('/usb-la',state)
    state,_=transition('/cai-app-la',state)
    with pytest.raises(ValueError): transition('/usb-la',state)
    state,_=transition('/nghi',state)
    assert state['media_status']=='unregistered' and state['software_status']=='unapproved'
    state,_=transition('/lam-viec',state)
    state,_=transition('/rut-usb',state)
    state,_=transition('/go-app',state)
    state,_=transition('/khoa-may',state)
    with pytest.raises(ValueError): transition('/tan-ca',state,pending=1)
    assert transition('/tan-ca',state,pending=0)[0]['shift']=='off'

def test_actual_employee_target_is_used():
    finding={'control_id':'A.8.19','event_type':'unapproved_software_installed','employee_id':'EMP-044',
             'asset_id':'OFFICE-EMP-044','asset_name':'Workstation 044','department':'Facilities'}
    scenario=scenario_for_finding(finding)
    assert scenario['human_context']['employee_id']=='EMP-044'
    assert scenario['target']['asset_id']=='OFFICE-EMP-044'
    with pytest.raises(ValueError): scenario_for_finding({**finding,'asset_id':'OFFICE-EMP-025'})
