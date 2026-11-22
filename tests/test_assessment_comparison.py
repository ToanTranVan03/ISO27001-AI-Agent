import copy
import pytest
from agent_core.a8_assessment import digest
from agent_core.assessment_comparison import compare_reports


def report(source='source',status='Non-Compliant',error=None,model='test'):
    value=dict(model=model,records=[dict(control_id='A.8.1',status=status,error=error,
                                       evidence={'source_sha256':source})])
    value['sha256']=digest(value)
    return value


def test_source_change_is_not_proof_of_remediation_and_inputs_stay_intact():
    before=report();after=report('new','Compliant');original=copy.deepcopy((before,after))
    result=compare_reports(before,after)
    assert result['controls'][0]['interpretation']=='SOURCE_CHANGED_REQUIRES_REVIEW'
    assert not result['remediation_verified'] and not result['independent_validation']
    assert (before,after)==original


@pytest.mark.parametrize('after,interpretation',[
    (report(status='Compliant'),'SAME_SOURCE_OUTPUT_CHANGED'),
    (report(model='new'),'RECIPE_CHANGED_NOT_ATTRIBUTABLE_TO_REMEDIATION'),
    (report(status=None,error='Timeout'),'ENGINE_ERROR_REQUIRES_REVIEW'),
    (report(),'SAME_SOURCE_SAME_STATUS')])
def test_model_drift_and_errors_stay_separate(after,interpretation):
    assert compare_reports(report(),after)['controls'][0]['interpretation']==interpretation


def test_corrupt_duplicate_or_different_scope_cannot_be_compared():
    bad=report();bad['model']='tampered'
    with pytest.raises(ValueError):compare_reports(report(),bad)
    for rows in ([],report()['records']*2):
        bad=report();bad['records']=rows;bad['sha256']=digest({k:v for k,v in bad.items() if k!='sha256'})
        with pytest.raises(ValueError):compare_reports(report(),bad)
