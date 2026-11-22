from copy import deepcopy
import pytest
from backend.remediation import finding,action,transition


def control():
    return dict(control_id='A.8.13',applicability=None,review_token='before',conclusion='Non-Compliant',
        human_review_current=False,human_review=None,pass_criteria=['Restore and verify backup'],
        evidence=[dict(evidence_id='old',sha256_hash='old-hash')])


def case():
    c=control();d=finding(c,'Restore verification failed in test scope','test service','Pending investigation','unconfirmed')
    proposal=dict(title='Restore a test backup',steps='Obtain backup and compare restored contents',acceptance='Restored contents verified by reviewer',
        department='IT',resources='Isolated restore target',tasks=['Restore backup','Verify restored hash'])
    original=deepcopy(proposal);d['actions']=[action(proposal,'CONSULTANT_DRAFT')]
    assert proposal==original
    return c,d,d['actions'][0]['action_id']


def move(d,aid,command,c,actor='consultant',role='consultant',**payload):
    return transition(d,aid,command,dict(note='Synthetic test observation, no professional signoff',**payload),actor,role,c)


def test_full_lifecycle_preserves_baseline_and_does_not_auto_pass_control():
    c,d,aid=case();baseline=deepcopy(d['baseline'])
    d=move(d,aid,'approve',c,assignee='operator',due_date='2099-12-31')
    d=move(d,aid,'start',c,'operator','operator')
    for task in d['actions'][0]['tasks']:d=move(d,aid,'task',c,'operator','operator',task_id=task['task_id'],done=True)
    c['evidence'].append(dict(evidence_id='after',sha256_hash='after-hash',is_synthetic=False,source='upload-source://test/after.txt'))
    c['review_token']='after'
    d=move(d,aid,'attach',c,'operator','operator',evidence_id='after')
    d=move(d,aid,'submit',c,'operator','operator')
    assert c['conclusion']=='Non-Compliant' and d['actions'][0]['state']=='AWAITING_VERIFICATION'
    with pytest.raises(ValueError):move(d,aid,'verify',c,outcome='accepted')
    c.update(human_review_current=True,human_review={'conclusion':'Compliant','evidence_ids':['after'],'reviewed_by':'consultant'})
    d=move(d,aid,'verify',c,outcome='accepted')
    d=move(d,aid,'close',c)
    assert d['actions'][0]['state']=='CLOSED' and d['baseline']==baseline
    assert c['conclusion']=='Non-Compliant' and len(d['history'])==8


def test_permissions_dependencies_and_submission_require_actual_new_sources():
    c,d,aid=case()
    with pytest.raises(PermissionError):move(d,aid,'approve',c,'operator','operator',assignee='operator',due_date='2099-12-31')
    d=move(d,aid,'approve',c,assignee='operator',due_date='2099-12-31')
    with pytest.raises(PermissionError):move(d,aid,'start',c,'other','operator')
    with pytest.raises(ValueError):move(d,aid,'task',c,'operator','operator',task_id=d['actions'][0]['tasks'][1]['task_id'],done=True)
    with pytest.raises(ValueError):move(d,aid,'submit',c,'operator','operator')
    with pytest.raises(ValueError):move(d,aid,'attach',c,'operator','operator',evidence_id='old')
    with pytest.raises(ValueError):move(d,aid,'attach',c,'operator','operator',evidence_id='other-control')
    c['evidence'].append(dict(evidence_id='preset',sha256_hash='test',is_synthetic=True,source='lab://preset'))
    with pytest.raises(ValueError):move(d,aid,'attach',c,'operator','operator',evidence_id='preset')


def test_stale_baseline_and_self_verification_are_rejected_without_mutation():
    c,d,aid=case();original=deepcopy(d);c['review_token']='new'
    with pytest.raises(ValueError):move(d,aid,'approve',c,assignee='operator',due_date='2099-12-31')
    assert d==original
    d['actions'][0].update(state='AWAITING_VERIFICATION',assignee='consultant',submitted_token='new')
    with pytest.raises(PermissionError):move(d,aid,'verify',c,outcome='accepted')


def test_collaborator_can_execute_but_cannot_submit_or_verify():
    c,d,aid=case()
    d=move(d,aid,'approve',c,assignee='operator',collaborator_ids=['helper'],due_date='2099-12-31')
    d=move(d,aid,'start',c,'helper','operator')
    d=move(d,aid,'task',c,'helper','operator',task_id=d['actions'][0]['tasks'][0]['task_id'],done=True)
    assert d['actions'][0]['tasks'][0]['done']
    with pytest.raises(PermissionError):move(d,aid,'submit',c,'helper','operator')
    d['actions'][0].update(state='AWAITING_VERIFICATION',submitted_token=c['review_token'])
    with pytest.raises(PermissionError):move(d,aid,'verify',c,'helper','verifier',outcome='accepted')
    with pytest.raises(PermissionError):move(d,aid,'return',c,'helper','verifier')


def test_task_assignment_is_restricted_to_action_participants_and_keeps_history():
    c,d,aid=case()
    d=move(d,aid,'approve',c,assignee='operator',collaborator_ids=['helper','other-helper'],due_date='2099-12-31')
    tid=d['actions'][0]['tasks'][0]['task_id']
    with pytest.raises(ValueError):move(d,aid,'assign_task',c,task_id=tid,task_assignee='outsider')
    with pytest.raises(PermissionError):move(d,aid,'assign_task',c,'helper','operator',task_id=tid,task_assignee='helper')
    d=move(d,aid,'assign_task',c,task_id=tid,task_assignee='helper')
    with pytest.raises(PermissionError):move(d,aid,'task',c,'other-helper','operator',task_id=tid,done=True)
    d=move(d,aid,'task',c,'helper','operator',task_id=tid,done=True)
    assert d['actions'][0]['tasks'][0]['assignee']=='helper' and d['history'][-2]['command']=='assign_task'


@pytest.mark.parametrize('outcome,state',[('partial','REWORK'),('rework','REWORK'),('more_information','NEEDS_INFORMATION')])
def test_rejection_is_logged_without_promoting_control(outcome,state):
    c,d,aid=case();d['actions'][0].update(state='AWAITING_VERIFICATION',assignee='operator',submitted_token='before')
    result=move(d,aid,'verify',c,outcome=outcome)
    assert result['actions'][0]['state']==state and result['actions'][0]['verifications'][0]['outcome']==outcome
    assert result['baseline']==d['baseline']
