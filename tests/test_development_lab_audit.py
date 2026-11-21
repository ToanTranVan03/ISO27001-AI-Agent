import copy
import json
import pytest
from agent_core.development_lab import build_bundle,evaluate
from agent_core.development_lab_audit import audit


def sample():
    bundle=build_bundle();case=bundle['cases'][0]
    raw=json.dumps({'checks':[dict(criterion_index=i,verdict='unknown',rationale='Need more evidence for this criterion',source_files=[case['artifacts'][0]['filename']]) for i in range(len(case['criteria']))]})
    result=evaluate(case,'test',lambda _:raw)
    return bundle,dict(run_id='test',bundle_sha256=bundle['sha256'],results=[result])


def test_audit_exposes_criterion_differences_without_mutation_or_human_claim():
    bundle,report=sample();before=copy.deepcopy(report)
    value=audit(report,bundle)
    assert report==before and value['controls_audited']==1
    assert value['differing_criteria']==2 and len(value['pending_controls'])==37
    assert not value['independent_validation']
    assert value['controls'][0]['review_state']=='PENDING_HUMAN_REVIEW'
    assert value['controls'][0]['criteria'][0]['citations'][0]['sha256']==report['results'][0]['source_hashes'][bundle['cases'][0]['artifacts'][0]['filename']]


def test_changed_sources_and_duplicate_records_are_rejected():
    bundle,report=sample()
    changed=copy.deepcopy(report);changed['bundle_sha256']='changed'
    with pytest.raises(ValueError):audit(changed,bundle)
    changed=copy.deepcopy(report);changed['results'][0]['source_hashes']={}
    with pytest.raises(ValueError):audit(changed,bundle)
    report['results']*=2
    with pytest.raises(ValueError):audit(report,bundle)


def test_modified_saved_conclusion_is_not_trusted_over_raw_response():
    bundle,report=sample();report['results'][0]['status']='Compliant'
    result=audit(report,bundle)
    assert result['invalid_results'] and all(c['model_verdict'] is None for c in result['controls'][0]['criteria'])


def test_frozen_reference_survives_current_key_changes_and_rejects_tampering():
    from agent_core.development_lab import designer_reference,reference_hash
    bundle,report=sample();reference=designer_reference()
    report.update(designer_reference_snapshot=copy.deepcopy(reference),designer_reference_sha256=reference_hash(reference))
    assert audit(report,bundle)['key_binding']=='FROZEN_BEFORE_RUN'
    report['designer_reference_snapshot'][bundle['cases'][0]['control_id']]['designer_verdicts'][0]='unknown'
    with pytest.raises(ValueError,match='key hash'):audit(report,bundle)
