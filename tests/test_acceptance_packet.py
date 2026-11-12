import copy
from backend.scope56 import build_scope
from backend.acceptance_packet import build_packet
from backend.review_criteria import PROTOCOL


def test_packet_exposes_all_missing_criteria_without_fabricating_completion():
    scope = build_scope('campaign', {'controls': []})
    packet = scope['handoff_packet']
    assert len(packet['controls']) == 56
    assert sum(c['priority_a8'] for c in packet['controls']) == 18
    assert packet['professional_acceptance'] == 'NOT_ASSERTED'
    for row in packet['controls']:
        assert 'explicit_sources_missing' in row['gaps']
        assert all(c['request'] and c['verified_verdict'] == 'not_reviewed' for c in row['criteria'])
        assert row['current_human_conclusion'] is None
        assert row['treatment_proposal']['assignee'] is None
        assert row['treatment_proposal']['due_date'] is None
        assert not row['treatment_proposal']['approved']


def test_machine_pass_and_source_types_do_not_fill_human_criteria():
    evidence = dict(evidence_id='source',sha256_hash='abc',source='upload://document',
                    is_synthetic=False,evidence_type='EVID_PPL_HR_RECORD',extracted_text='private raw text')
    dossier = {'controls': [dict(control_id='A.6.1',conclusion='Compliant',assessment_state='evaluated',evidence=[evidence])]}
    original = copy.deepcopy(dossier)
    scope = build_scope('campaign',dossier)
    row = scope['handoff_packet']['controls'][0]
    assert dossier == original
    assert row['machine_conclusion'] == 'Compliant'
    assert all(c['verified_verdict'] == 'not_reviewed' for c in row['criteria'])
    assert 'human_criteria_review_not_current' in row['gaps']
    assert 'explicit_sources_missing' not in row['gaps']
    assert 'extracted_text' not in row['sources'][0]
    assert row['sources'][0]['sha256'] == 'abc'


def test_only_current_review_fills_criteria_and_source_change_invalidates_packet():
    dossier = {'controls': [dict(control_id='A.6.1',assessment_state='evaluated',evidence=[])]}
    scope = build_scope('campaign',dossier)
    first = scope['controls'][0]
    review = dict(protocol=PROTOCOL,review_token=first['review_token'],conclusion='Insufficient Evidence',
                  evidence_ids=[],criteria_reviews=[dict(criterion_index=i,verdict='unknown',
                  rationale='Actual evidence has not been supplied',evidence_ids=[])
                  for i in range(len(first['pass_criteria']))])
    current = build_scope('campaign',dossier,reviews={'A.6.1':review})
    row = current['handoff_packet']['controls'][0]
    assert row['current_human_conclusion'] == 'Insufficient Evidence'
    assert 'criteria_unknown' in row['gaps']
    assert all(c['request'] for c in row['criteria'])
    changed = build_scope('campaign',{**dossier,'company_snapshot_hash':'new'},reviews={'A.6.1':review})
    assert changed['handoff_packet']['controls'][0]['current_human_conclusion'] is None
    assert changed['handoff_packet']['sha256'] != current['handoff_packet']['sha256']


def test_excluded_control_needs_no_new_source_requests_but_never_auto_approves():
    decision = dict(applicable=False,reason='Recorded exclusion awaiting owner review',treatment='Keep rationale')
    scope = build_scope('campaign',{'controls':[]},decisions={'A.6.1':decision})
    before = copy.deepcopy(scope)
    packet = build_packet(scope)
    assert scope == before
    row = packet['controls'][0]
    assert not row['gaps'] and all(c['request'] is None for c in row['criteria'])
    assert row['treatment_proposal']['recorded_treatment'] == 'Keep rationale'
    assert packet['formal_soa_approval'] == 'DRAFT_NOT_APPROVED'
    assert packet == scope['handoff_packet']


def test_preset_only_control_directs_owner_to_collect_sources_not_run_agent():
    preset = dict(evidence_id='preset',sha256_hash='hash',source='lab://preset',is_synthetic=True)
    decision = dict(applicable=True,reason='Applicable to project scope',treatment='Collect and review sources')
    scope = build_scope('campaign',{'controls':[dict(control_id='A.6.1',evidence=[preset])]},decisions={'A.6.1':decision})
    row = scope['controls'][0]
    assert row['explicit_source_count'] == 0
    assert row['next_action'] == 'Thu hồ sơ hoặc bằng chứng cho control'
    assert 'explicit_sources_missing' in scope['handoff_packet']['controls'][0]['gaps']
