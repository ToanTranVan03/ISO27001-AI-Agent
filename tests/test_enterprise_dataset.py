import json
import csv
from pathlib import Path
import pytest
from generate_enterprise_dataset import generate,validate


def test_generator_is_deterministic_linked_and_preserves_history(tmp_path):
    a=generate(tmp_path/'a',(30,),6);b=generate(tmp_path/'b',(30,),6)
    assert a==b and validate(tmp_path/'a')['passed']
    period=tmp_path/'a/SYNTH-001/2024-03'
    people=list(csv.DictReader((period/'people.csv').open(encoding='utf-8')))
    accounts=list(csv.DictReader((period/'accounts.csv').open(encoding='utf-8')))
    assert {p['employee_id'] for p in people}=={p['employee_id'] for p in accounts}
    exited={p['employee_id'] for p in people if p['status']=='terminated'}
    assert any(a['active']=='False' for a in accounts if a['employee_id'] in exited)
    assert any(a['active']=='True' for a in accounts if a['employee_id'] in exited)
    assert a['training_allowed'] is False and a['independent_validation'] is False
    with pytest.raises(ValueError):generate(tmp_path/'a',(30,),6)
    (period/'accounts.csv').write_text('tampered',encoding='utf-8')
    assert not validate(tmp_path/'a')['passed']


@pytest.mark.parametrize('sizes,months',[((0,),1),((5001,),1),((30,),61)])
def test_generator_rejects_unbounded_requests(tmp_path,sizes,months):
    with pytest.raises(ValueError):generate(tmp_path/'out',sizes,months)


def test_remove_only_intact_generated_subdirectory_and_refuse_extra_files(tmp_path,monkeypatch):
    import generate_enterprise_dataset as generator
    monkeypatch.setattr(generator,'GENERATED_ROOT',tmp_path)
    folder=tmp_path/'generated';generate(folder,(3,),1)
    (folder/'personal.txt').write_text('Not generated',encoding='utf-8')
    with pytest.raises(ValueError):generator.remove_dataset(folder)
    assert (folder/'personal.txt').exists()
    (folder/'personal.txt').unlink()
    assert generator.remove_dataset(folder)['database_affected'] is False
    assert not folder.exists()
    with pytest.raises(ValueError):generator.remove_dataset(tmp_path)
