"""Smoke-test the Streamlit dashboard headlessly (no server, no PostgreSQL)."""
import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from pathlib import Path  # noqa: E402

APP = str(Path(__file__).resolve().parents[1] / "dashboard_streamlit" / "app.py")


def test_dashboard_boots_scans_and_shows_pending_action():
    at = AppTest.from_file(APP, default_timeout=120).run()
    assert not at.exception, [e.value for e in at.exception]
    assert len(at.tabs) == 4
    assert at.sidebar.selectbox[0].value == "Standalone In-Memory"
    assert at.sidebar.selectbox[1].value == "COMP-CANONICAL-01"

    at.sidebar.button[0].click().run()
    assert not at.exception, [e.value for e in at.exception]
    labels = [m.label for m in at.metric]
    for state in ("Compliant", "Non-compliant", "Partial", "Insufficient Evidence", "Not Applicable", "Pending Remediation"):
        assert any(state in label for label in labels), state

    approve = [b for b in at.button if b.label.startswith("✅ Approve")]
    assert approve, "the NV015 offboarding action must be waiting for admin approval"
    approve[0].click().run()
    assert not at.exception, [e.value for e in at.exception]
