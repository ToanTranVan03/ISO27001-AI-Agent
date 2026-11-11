import pytest
from backend.review_criteria import validate,current,PROTOCOL
from backend.scope56 import build_scope


def checks(verdicts):
    return [dict(criterion_index=i,verdict=v,rationale='Reviewed actual source or documented evidence gap',
                 evidence_ids=[] if v=='unknown' else ['source']) for i,v in enumerate(verdicts)]


@pytest.mark.parametrize('verdicts,expected',[
    (['met','met'],'Compliant'),(['met','not_met'],'Partially Compliant'),
    (['not_met','not_met'],'Non-Compliant'),(['met','unknown'],'Insufficient Evidence')])
def test_criterion_conclusion_and_citations(verdicts,expected):
    validate(['one','two'],checks(verdicts),['source'],expected)
    with pytest.raises(ValueError):validate(['one','two'],checks(verdicts),['source'],'Invalid conclusion')


def test_missing_duplicate_or_uncited_criterion_cannot_be_signed_off():
    for items in [checks(['met']),checks(['met','met'])[:1]*2]:
        with pytest.raises(ValueError):validate(['one','two'],items,['source'],'Compliant')
    with pytest.raises(ValueError):validate(['one','two'],checks(['met','met']),[],'Compliant')
    items=checks(['met','met']);items[0]['evidence_ids']=[]
    with pytest.raises(ValueError):validate(['one','two'],items,['source'],'Compliant')


def test_old_summary_only_reviews_remain_history_but_do_not_approve_soa():
    original=build_scope('a',{'controls':[]})
    row=original['controls'][0]
    old=dict(conclusion='Compliant',review_token=row['review_token'],evidence_ids=['source'],reviewed_by='human')
    updated=build_scope('a',{'controls':[]},reviews={row['control_id']:old})
    assert updated['controls'][0]['human_review']==old
    assert not updated['controls'][0]['human_review_current']
    assert not updated['soa']['approval_ready']
    old.update(protocol=PROTOCOL,conclusion='Insufficient Evidence',evidence_ids=[],criteria_reviews=checks(['unknown']*len(row['pass_criteria'])))
    assert current(old,row['pass_criteria'])
