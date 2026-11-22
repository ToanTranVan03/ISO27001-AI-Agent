from copy import deepcopy
from uuid import UUID
import pytest
from pydantic import ValidationError
from fastapi import HTTPException
from backend.governance_api import Risk,Requirement,Save,score,validate_links


def risk():
    return dict(title='Synthetic service risk',asset='Test server',scenario='Synthetic loss of access scenario',rationale='Software fixture only, not a real risk estimate',
        likelihood=3,impact=4,owner_id=str(UUID(int=1)),treatment='mitigate',treatment_plan='Collect records, implement and verify',due_date='2099-12-31',control_ids=['A.8.13'])


def test_score_is_project_method_not_iso_and_does_not_invent_residual():
    data=Risk(**risk()).model_dump(mode='json');before=deepcopy(data)
    value=score(data)
    assert value['inherent_score']==12 and value['residual_score'] is None and 'NOT_AN_ISO' in value['scoring_method']
    assert data==before


@pytest.mark.parametrize('updates',[{'likelihood':True},{'impact':6},{'likelihood':0},{'residual_likelihood':2}])
def test_bad_risk_scales_or_partial_residual_never_validate(updates):
    with pytest.raises(ValidationError):Risk(**{**risk(),**updates})


def test_requirements_need_actual_source_version_and_rights_not_only_title():
    with pytest.raises(ValidationError):Requirement(reference='A.8.13',title='Backup example',description='This is a test only',category='standard',control_ids=['A.8.13'])
    with pytest.raises(ValidationError):Save(expected_version=0,kind='requirement',data=risk(),note='Wrong entity rejected')


def test_control_and_tenant_links_are_validated_before_saving():
    class Cursor:
        def execute(self,*args):pass
        def fetchone(self):return None
    for changes in ({'control_ids':['A.5.18']},{'control_ids':['A.8.13','A.8.13']},{}):
        with pytest.raises(HTTPException):validate_links(Cursor(),UUID(int=1),{**risk(),**changes})
