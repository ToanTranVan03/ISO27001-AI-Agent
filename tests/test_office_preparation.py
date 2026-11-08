from copy import deepcopy
import pytest
from backend.office_logic import DEFAULT_STATE,transition,preparation_steps


def test_one_usb_comment_can_enter_shift_before_action_without_mutating_original_state():
    state=deepcopy(DEFAULT_STATE)
    assert preparation_steps('/usb-la',state)==['/di-lam']
    assert state==DEFAULT_STATE
    joined,_=transition('/di-lam',state)
    result,event=transition('/usb-la',joined)
    assert result['location']=='desk' and result['usb_connected']
    assert event=='unapproved_usb_inserted'


def test_return_from_break_uses_normal_work_transition_before_app_command():
    state,_=transition('/di-lam',DEFAULT_STATE)
    state,_=transition('/nghi',state)
    assert preparation_steps('/cai-app-la',state)==['/lam-viec']


@pytest.mark.parametrize('changes,pending',[({'network_isolated':True},0),({'device_status':'locked'},0),({'returned':True},0),({},1)])
def test_preparation_never_bypasses_protection_or_unresolved_events(changes,pending):
    with pytest.raises(ValueError):preparation_steps('/usb-la',{**DEFAULT_STATE,**changes},pending)


def test_preparation_rejects_invalid_final_action_before_creating_any_shift_step():
    state={**DEFAULT_STATE,'usb_connected':True}
    with pytest.raises(ValueError):preparation_steps('/usb-la',state)
    assert state['shift']=='off'
