"""Keep API unit tests independent of the local PostgreSQL database."""
import pytest

from backend import database, enterprise_lab, company_storage, teamwork


@pytest.fixture(autouse=True)
def isolate_database_startup(monkeypatch):
    monkeypatch.setattr(database, "initialize_database", lambda: None)
    monkeypatch.setattr(teamwork, "init_teamwork", lambda: None)
    monkeypatch.setattr(enterprise_lab, "init_enterprise_lab", lambda: None)
    monkeypatch.setattr(company_storage, "initialize_company_inventory", lambda: None)
    from backend import main
    monkeypatch.setattr(main, "recover_interrupted", lambda: None)
