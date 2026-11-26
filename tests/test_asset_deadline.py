from datetime import date, datetime
from typing import cast
from uuid import uuid4

import pytest
from sqlalchemy.engine import RowMapping

from compliance_ai.assessments import offboarding_findings, research_catalog
from compliance_ai.asset_return import return_due_date


@pytest.mark.parametrize(
    ("start", "days", "due"),
    [
        ("2026-11-27T16:50:00Z", 3, "2026-12-02"),  # Friday evening in Vietnam
        ("2026-11-27T17:05:00Z", 0, "2026-11-28"),  # Saturday in Vietnam
        ("2026-11-28T12:00:00Z", 1, "2026-11-30"),
        ("2026-11-29T12:00:00Z", 5, "2026-12-04"),
        ("2026-12-01T10:00:00Z", 0, "2026-12-01"),
    ],
)
def test_due_date(start: str, days: int, due: str) -> None:
    assert return_due_date(datetime.fromisoformat(start), days) == date.fromisoformat(due)


@pytest.mark.parametrize(
    ("received", "expected"),
    [
        ("2026-12-02T16:59:59.999999Z", "COMPLIANT"),  # Last instant on the due date
        ("2026-12-02T17:00:00Z", "PARTIAL"),
        ("2026-11-26T15:00:00Z", "INSUFFICIENT_EVIDENCE"),  # Earlier than separation
        ("2026-12-09T15:00:00Z", "INSUFFICIENT_EVIDENCE"),  # Future observation
    ],
)
def test_receipt_timing_in_assessment(received: str, expected: str) -> None:
    catalog = research_catalog()
    policy = next(p for p in catalog.policies if p.id == "abc")
    employee = cast(
        RowMapping,
        {
            "id": uuid4(),
            "revision": 1,
            "employment_status": "terminated",
            "termination_effective_at": datetime.fromisoformat("2026-11-27T16:50:00Z"),
        },
    )
    asset = cast(
        RowMapping,
        {
            "id": uuid4(),
            "revision": 3,
            "receipt_id": uuid4(),
            "received_at": datetime.fromisoformat(received),
            "pending_action": None,
            "state": {"returned": True, "return_receipt": "desk", "custody": "asset_desk"},
        },
    )
    findings = offboarding_findings(
        uuid4(),
        employee,
        {"asset": asset},
        policy,
        {c.id: c for c in catalog.criteria},
        datetime.fromisoformat("2026-12-03T09:00:00Z"),
        "hardware",
    )
    finding = next(f for f in findings if f.criterion_id == "D02")
    assert finding.status == expected and finding.proposed_tool is None
