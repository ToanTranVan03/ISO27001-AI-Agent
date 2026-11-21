import json
from pathlib import Path
import pytest
from backend import a8_api


def test_windows_sharing_retry_preserves_old_json_until_atomic_replacement(tmp_path,monkeypatch):
    target=tmp_path/'record.json';target.write_text('{"old": true}',encoding='utf-8')
    original=Path.replace;attempts=[];sleeps=[]
    def replace(source,destination):
        attempts.append(source)
        if len(attempts)<3:
            assert json.loads(target.read_text())=={'old':True}
            error=PermissionError('Sharing violation');error.winerror=32;raise error
        return original(source,destination)
    monkeypatch.setattr(Path,'replace',replace);monkeypatch.setattr(a8_api.time,'sleep',sleeps.append)
    a8_api.save(target,{'new':'kết quả'})
    assert json.loads(target.read_text(encoding='utf-8'))=={'new':'kết quả'}
    assert len(attempts)==3 and sleeps==[.01,.02]
    assert list(tmp_path.iterdir())==[target]


@pytest.mark.parametrize('winerror,attempts',[ (5,5),(32,5),(33,5),(None,1),(13,1) ])
def test_permanent_write_failure_keeps_prior_record_and_is_not_reported_as_success(tmp_path,monkeypatch,winerror,attempts):
    target=tmp_path/'record.json';target.write_text('{"old": true}')
    seen=[]
    def fail(source,destination):
        seen.append(source);error=PermissionError('No access');error.winerror=winerror;raise error
    monkeypatch.setattr(Path,'replace',fail);monkeypatch.setattr(a8_api.time,'sleep',lambda _:None)
    with pytest.raises(PermissionError):a8_api.save(target,{'new':True})
    assert len(seen)==attempts and json.loads(target.read_text())=={'old':True}
    assert list(tmp_path.iterdir())==[target]
