import json
import pytest
from agent_core import development_lab as lab


def test_bundle_covers_document_complement_and_keeps_key_out_of_model_sources():
    from agent_core.a8_assessment import catalog
    bundle=lab.build_bundle()
    scope=json.loads((lab.ROOT/'docs/56_controls_scope.json').read_text(encoding='utf-8'))
    assert len(bundle['cases'])==38
    assert {c['control_id'] for c in bundle['cases']}=={c['control_id'] for c in scope}-{c['control_id'] for c in catalog()}
    assert 'designer_verdicts' not in json.dumps(bundle)
    assert bundle['is_synthetic'] and not bundle['independent_validation']
    refs=json.loads(lab.DATA.read_text(encoding='utf-8'))['cases']
    for c in bundle['cases']:
        assert len(c['criteria'])==len(refs[c['control_id']]['designer_verdicts'])
        assert all(json.loads(a['content'])['professional_confirmation'] is False for a in c['artifacts'])


def test_inference_does_not_receive_designer_labels_and_preserves_invalid_response():
    case=lab.build_bundle()['cases'][0]
    def invalid(prompt):
        assert 'designer_verdicts' not in prompt
        return 'invalid original model response'
    result=lab.evaluate(case,'test',invalid)
    assert result['status'] is None and result['error'] and result['raw_response']=='invalid original model response'
    def valid(prompt):return json.dumps({'checks':[dict(criterion_index=i,verdict='unknown',rationale='Source cannot establish this criterion',source_files=[case['artifacts'][0]['filename']]) for i in range(len(case['criteria']))]})
    result=lab.evaluate(case,'test',valid)
    assert result['status']=='Insufficient Evidence' and not result['error']
    comparison=lab.compare_designer([result])
    assert comparison['total']==1 and 'NOT_HUMAN' in comparison['source']


def test_invalid_citations_and_duplicate_criteria_cannot_be_accepted():
    case=lab.build_bundle()['cases'][0]
    raw={'checks':[dict(criterion_index=0,verdict='met',rationale='Asserted without a real source',source_files=['not-present.json'])]*2}
    with pytest.raises(ValueError):lab.parse_result(json.dumps(raw),case)


def test_workbench_admin_only_and_does_not_call_formal_storage(monkeypatch,tmp_path):
    from backend import development_lab_api as api
    from fastapi import HTTPException
    from uuid import UUID
    aid=UUID('00000000-0000-0000-0000-000000000001')
    monkeypatch.setattr(api,'require_campaign',lambda *_:None)
    monkeypatch.setattr(api,'STORE',tmp_path)
    with pytest.raises(HTTPException) as exc:api.start_lab(aid,dict(role='assessor'))
    assert exc.value.status_code==403 and not list(tmp_path.rglob('*.json'))
    assert not api.get_lab(aid,dict(role='assessor'))['can_start']


def test_duplicate_development_runs_are_blocked_and_restart_is_explicit(monkeypatch,tmp_path):
    from backend import development_lab_api as api
    from fastapi import HTTPException
    from uuid import UUID
    aid=UUID('00000000-0000-0000-0000-000000000002')
    monkeypatch.setattr(api,'require_campaign',lambda *_:None)
    monkeypatch.setattr(api,'STORE',tmp_path)
    scheduled=[]
    monkeypatch.setattr(api.pool,'submit',lambda *args:scheduled.append(args))
    try:
        first=api.start_lab(aid,dict(role='admin'))
        assert first['is_synthetic'] and first['total']==38 and len(scheduled)==1
        with pytest.raises(HTTPException) as error:api.start_lab(aid,dict(role='admin'))
        assert error.value.status_code==409
        api.active.pop(str(aid))
        assert api.get_lab(aid,dict(role='admin'))['runs'][0]['state']=='INTERRUPTED'
    finally:api.active.pop(str(aid),None)


def test_schema_bounds_criteria_and_exact_source_filenames():
    case=lab.build_bundle()['cases'][0];schema=lab.output_schema(case)
    checks=schema['properties']['checks']
    assert checks['minItems']==checks['maxItems']==len(case['criteria'])
    assert checks['items']['properties']['source_files']['items']['enum']==[a['filename'] for a in case['artifacts']]


def test_retry_only_technical_errors_once_and_keeps_first_results(monkeypatch,tmp_path):
    import copy
    from scripts import retry_development_lab_errors as script
    monkeypatch.setattr(script,'ROOT',tmp_path)
    bundle=lab.build_bundle();cid=bundle['cases'][0]['control_id']
    original=[dict(control_id=cid,status=None,error='First schema error',raw_response='Original malformed response')]
    doc=dict(state='COMPLETED',bundle_sha256=bundle['sha256'],model='test',results=original)
    path=tmp_path/'work/development-lab/report.json';path.parent.mkdir(parents=True);path.write_text(json.dumps(doc),encoding='utf-8')
    before=copy.deepcopy(original)
    monkeypatch.setattr(script,'evaluate',lambda case,model:dict(control_id=case['control_id'],status='Insufficient Evidence',error=None))
    fixed=script.retry(path)
    assert fixed['results']==before and fixed['final_results'][0]['error'] is None
    assert len(fixed['repair_attempts'])==1
    with pytest.raises(ValueError,match='One retry'):script.retry(path)
