import copy
import json
from pathlib import Path
import pytest
from agent_core.a8_teacher_pipeline import load_reports,build_assessor_ground_truth,export_all_deliverables,evaluate_accuracy_against_assessors


def report():return json.loads(Path('docs/a8-results/live-v2-ollama-pilot.json').read_text(encoding='utf-8'))['report']


def test_export_keeps_live_unrated_and_never_approves_soa(tmp_path):
    r=report();before=copy.deepcopy(r)
    payload=export_all_deliverables([r],tmp_path/'export')
    assert r==before
    assert all(row['rated']==0 and row['accuracy'] is None for row in payload['designer_comparisons'][0]['comparison']['per_control'])
    assert not payload['human_comparisons'][0]['analysis']['complete_reviewers']
    assert all(s['approval']=='DRAFT_NOT_APPROVED' for s in payload['soa_drafts'])
    assert all(e['applicable'] is None for s in payload['soa_drafts'] for e in s['entries'])
    assert (tmp_path/'export/per-control.csv').exists()
    with pytest.raises(FileExistsError):export_all_deliverables([r],tmp_path/'export')


def test_import_rejects_generated_human_labels_and_bad_report_binding(tmp_path):
    p=tmp_path/'labels.json'
    p.write_text(json.dumps([dict(label_origin='human-assessor-verified')]),encoding='utf-8')
    with pytest.raises(ValueError):build_assessor_ground_truth(p)
    with pytest.raises(ValueError):evaluate_accuracy_against_assessors([report()],[dict(report_sha256='wrong')])


def test_load_checks_hash_and_duplicate_inputs(tmp_path):
    p=tmp_path/'report.json';r=report()
    p.write_text(json.dumps(r),encoding='utf-8')
    assert len(load_reports([p]))==1
    with pytest.raises(ValueError,match='Duplicate'):load_reports([p,p])
    r['records'][0]['status']='Compliant';p.write_text(json.dumps(r),encoding='utf-8')
    with pytest.raises(ValueError,match='hash'):load_reports([p])


def test_export_excludes_pending_quality_without_changing_locked_labels():
    r=report()
    labels=[dict(reviewer_id='assessor',control_id=x['control_id'],case_id=x['case_id'],
        report_sha256=r['sha256'],evidence_sha256=x['evidence']['source_sha256'],
        expected=x['status'] or 'Insufficient Evidence',rationale='Recorded observation reviewed against the criterion.',
        assistance='unassisted',prior_exposure='no',
        quality_check=dict(blocked=False,issues=[])) for x in r['records']]
    before=copy.deepcopy(labels)
    clean=evaluate_accuracy_against_assessors([r],labels)[0]
    assert clean['quality_eligible_independently_declared_reviewers']==['assessor']
    labels[0]['quality_check']=dict(blocked=True,issues=[dict(code='filler',severity='error')])
    bad=copy.deepcopy(labels)
    result=evaluate_accuracy_against_assessors([r],labels)[0]
    assert result['analysis']['complete_reviewers']==['assessor']
    assert result['pending_human_comparison'] and not result['human_comparisons']
    assert labels==bad and before[0]['quality_check']['blocked'] is False
