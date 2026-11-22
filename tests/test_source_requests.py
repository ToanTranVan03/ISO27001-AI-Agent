from backend.scope56 import build_scope
from backend.source_requests import build_requests,markdown


def test_missing_source_requests_never_assign_people_or_create_evidence():
    scope=build_scope('test',{'controls':[]})
    result=scope['source_requests']
    assert len(result['requests'])==56 and sum(result['by_role'].values())==56
    assert all(r['assignee'] is None and r['due_date'] is None for r in result['requests'])
    assert all(r['criteria'] and not r['existing_evidence_ids'] for r in result['requests'])
    for role,count in result['by_role'].items():
        text=markdown(result,role)
        assert text.count('\n## ')==count


def test_unusable_source_is_requested_again_and_exclusion_is_respected():
    evidence=dict(evidence_id='bad',sha256_hash='hash',source='file',is_synthetic=False,source_quality={'usable':False})
    scope=build_scope('test',{'controls':[dict(control_id='A.6.2',evidence=[evidence])]},
        decisions={'A.6.1':dict(applicable=False,reason='Recorded exclusion rationale',treatment='Retain justification')})
    requests=scope['source_requests']['requests']
    assert len(requests)==55 and not any(r['control_id']=='A.6.1' for r in requests)
    r=next(r for r in requests if r['control_id']=='A.6.2')
    assert r['reason']=='replace_unusable_source' and r['existing_evidence_ids']==['bad']


def test_usable_sources_need_separate_coverage_review_without_inventing_missing_sources():
    packet=dict(assessment_id='test',sha256='packet',controls=[dict(control_id='A.8.1',
        excluded_by_recorded_decision=False,gaps=['human_criteria_review_not_current'],
        owner_role='IT',sources=[dict(evidence_id='source')],criteria=[dict(criterion='Check scope')])])
    result=build_requests(packet)
    assert not result['requests'] and not result['by_role']
    row=result['coverage_reviews'][0]
    assert row['reason']=='verify_source_coverage' and row['assignee'] is None
    assert row['existing_evidence_ids']==['source']
    assert 'A.8.1' in markdown(result,'IT')
    packet['controls'][0]['gaps']=[]
    assert not build_requests(packet)['coverage_reviews']


def test_integrity_failure_is_actionable_even_with_another_usable_source():
    import copy
    good=dict(evidence_id='good',sha256_hash='good-hash',source='file',is_synthetic=False,
              source_quality={'usable':True,'issues':[],'integrity':{'state':'verified'}})
    bad=dict(evidence_id='lost-original',sha256_hash='old-hash',source='file',is_synthetic=False,
             extracted_text='Private contents must not enter handoff reports',
             source_quality={'usable':False,'issues':['original_missing'],
                             'integrity':{'state':'failed'}})
    dossier={'controls':[dict(control_id='A.6.1',evidence=[good,bad])]}
    before=copy.deepcopy(dossier)
    scope=build_scope('test',dossier)
    row=scope['handoff_packet']['controls'][0]
    assert 'source_integrity_failed' in row['gaps']
    assert 'source_content_unusable' not in row['gaps']
    request=next(r for r in scope['source_requests']['requests'] if r['control_id']=='A.6.1')
    assert request['reason']=='restore_source_integrity'
    assert request['source_issues']==[dict(evidence_id='lost-original',issues=['original_missing'],integrity_state='failed')]
    rendered=markdown(scope['source_requests'])
    assert 'original_missing' in rendered and 'lost-original' in rendered
    assert 'Private contents' not in rendered
    assert dossier==before
    assert request['assignee'] is None


def test_legacy_unverified_integrity_is_not_mislabeled_as_corruption():
    evidence=dict(evidence_id='legacy',sha256_hash='hash',source='file',is_synthetic=False,
                  source_quality={'usable':True,'issues':[],'integrity':{'state':'not_verifiable'}})
    scope=build_scope('test',{'controls':[dict(control_id='A.6.1',evidence=[evidence])]})
    assert 'source_integrity_failed' not in scope['handoff_packet']['controls'][0]['gaps']
    assert not any(r['control_id']=='A.6.1' for r in scope['source_requests']['requests'])
    assert any(r['control_id']=='A.6.1' for r in scope['source_requests']['coverage_reviews'])
