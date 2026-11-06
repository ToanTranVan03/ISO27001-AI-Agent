from contextlib import contextmanager
from uuid import uuid4
import pytest
from backend import enterprise_missions as missions,mission_targets as targets

TARGET={"employee_id":"EMP-006","asset_id":"OFFICE-EMP-006"}


def test_targeted_scan_never_processes_other_employee_or_event():
    findings=[{**TARGET,"event_id":"chosen","control_id":"A.7.10"},
              {"employee_id":"EMP-025","asset_id":"OFFICE-EMP-025","event_id":"other","control_id":"A.7.10"},
              {**TARGET,"event_id":"another","control_id":"A.7.10"}]
    scan=missions.scoped_scan({"checked_assets":70,"findings":findings},"hardware",{**TARGET,"event_id":"chosen"})
    assert scan["findings"]==[findings[0]] and scan["checked_assets"]==1
    assert scan["source_asset_count"]==70 and len(findings)==3


def test_target_is_bound_into_artifact_hash_without_breaking_old_hashes():
    doc=missions.new_document(uuid4(),"Check workstation","all","tester")
    original=missions.artifact_hash(doc)
    doc.pop("target")
    assert missions.artifact_hash(doc)==original
    doc["target"]=TARGET
    assert missions.artifact_hash(doc)!=original


def test_unresolved_incident_filter_uses_exact_telemetry_identifiers():
    event={"ai_classification":{"telemetry_finding":{**TARGET,"event_id":"event"}}}
    assert targets.incident_matches(event,TARGET)
    assert not targets.incident_matches(event,{**TARGET,"employee_id":"EMP-025"})
    assert not targets.incident_matches(event,{**TARGET,"event_id":"wrong"})


def test_cross_workstation_target_is_rejected_before_database_access():
    with pytest.raises(ValueError):targets.resolve_target("aid",{**TARGET,"asset_id":"OFFICE-EMP-025"})


def test_event_and_assessment_relationship_are_checked(monkeypatch):
    class Cursor:
        def execute(self,sql,args):
            assert args[0]=="expected-assessment"
            self.result=("Employee","Workstation") if "JOIN" in sql else ({"employee_id":"EMP-025"},)
        def fetchone(self):return self.result
    class Connection:
        @contextmanager
        def cursor(self):yield Cursor()
    @contextmanager
    def connection():yield Connection()
    monkeypatch.setattr(targets,"get_connection",connection)
    assert targets.resolve_target("expected-assessment",TARGET)["employee_name"]=="Employee"
    with pytest.raises(ValueError):targets.resolve_target("expected-assessment",{**TARGET,"event_id":"mismatched-event"})
