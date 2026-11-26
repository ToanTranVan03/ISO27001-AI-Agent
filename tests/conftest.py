"""Keep API unit tests independent of the local PostgreSQL database."""
import pytest

from backend import database, enterprise_lab, company_storage, teamwork


@pytest.fixture(autouse=True)
def isolate_database_startup(monkeypatch):
    monkeypatch.setattr(database, "initialize_database", lambda: None)
    monkeypatch.setattr(teamwork, "init_teamwork", lambda: None)
    monkeypatch.setattr(teamwork, "inventory_mode", lambda *_:'lab')
    monkeypatch.setattr(enterprise_lab, "init_enterprise_lab", lambda: None)
    monkeypatch.setattr(company_storage, "initialize_company_inventory", lambda: None)
    from backend import main
    monkeypatch.setattr(main.remediation_api,'initialize',lambda:None)
    monkeypatch.setattr(main.governance_api,'initialize',lambda:None)
    monkeypatch.setattr(main.remediation_notifications,'initialize',lambda:None)
    monkeypatch.setattr(main.employee_workflow_api,'initialize',lambda:None)
    monkeypatch.setattr(main.remediation_notifications,'start',lambda:lambda:None)
    monkeypatch.setattr(main.remediation_api,'require_review_role',lambda *_:None)
    monkeypatch.setattr(main, "recover_interrupted", lambda: None)
