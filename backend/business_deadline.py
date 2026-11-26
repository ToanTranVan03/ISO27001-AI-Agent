"""Adapted from Tu/Tuan7 asset_return.return_due_date (720943e), calendar preview only."""
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo


def business_due_date(anchor:datetime,business_days:int):
    if anchor.tzinfo is None or not 0<=business_days<=3650:raise ValueError('Cần thời điểm có múi giờ và 0–3650 ngày làm việc.')
    day=anchor.astimezone(ZoneInfo('Asia/Bangkok')).date()
    if business_days==0:return day
    day+=timedelta(days=1)
    if day.weekday()>=5:day+=timedelta(days=7-day.weekday())
    weeks,extra=divmod(business_days-1,5)
    return day+timedelta(days=7*weeks+extra+(2 if day.weekday()+extra>=5 else 0))
