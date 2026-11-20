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
