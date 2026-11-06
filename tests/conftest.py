"""Keep API unit tests independent of the local PostgreSQL database."""
import pytest

from backend import database, enterprise_lab, incident_simulation, teamwork


@pytest.fixture(autouse=True)
def isolate_database_startup(monkeypatch):
    monkeypatch.setattr(database, "initialize_database", lambda: None)
    monkeypatch.setattr(teamwork, "init_teamwork", lambda: None)
    monkeypatch.setattr(enterprise_lab, "init_enterprise_lab", lambda: None)
    monkeypatch.setattr(incident_simulation, "initialize_incident_simulation", lambda: None)
