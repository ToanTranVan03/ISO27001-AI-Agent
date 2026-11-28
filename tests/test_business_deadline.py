from datetime import datetime,timedelta
import pytest
from backend.business_deadline import business_due_date


@pytest.mark.parametrize('days',[0,1,2,3,5,10,100,3650])
def test_business_deadline_matches_simple_calendar(days):
    anchor=datetime.fromisoformat('2026-11-27T20:00:00+07:00');expected=anchor.date();remaining=days
    while remaining:
        expected+=timedelta(days=1)
        if expected.weekday()<5:remaining-=1
    assert business_due_date(anchor,days)==expected


def test_normalizes_to_bangkok_and_rejects_naive_or_negative():
    assert str(business_due_date(datetime.fromisoformat('2026-11-27T23:00:00+00:00'),0))=='2026-11-28'
    with pytest.raises(ValueError):business_due_date(datetime(2026,11,27),1)
    with pytest.raises(ValueError):business_due_date(datetime.fromisoformat('2026-11-27T00:00:00+07:00'),-1)
