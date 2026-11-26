import pytest
from generate_enterprise_dataset import generate
from import_enterprise_dataset import import_dataset


def test_import_preflight_never_logs_in_or_mutates_database(tmp_path,monkeypatch):
    import requests
    generate(tmp_path/'generated',(6,),2)
    monkeypatch.setattr(requests,'Session',lambda:pytest.fail('Preflight must not open HTTP'))
    result=import_dataset(tmp_path/'generated','http://127.0.0.1:8000',tmp_path/'receipt.json')
    assert result['preflight_only'] and result['periods']==2 and not result['model_called']
    assert not (tmp_path/'receipt.json').exists()


def test_import_refuses_existing_receipt(tmp_path):
    (tmp_path/'receipt.json').write_text('prior history',encoding='utf-8')
    with pytest.raises(ValueError):import_dataset(tmp_path,'http://127.0.0.1:8000',tmp_path/'receipt.json',True)
