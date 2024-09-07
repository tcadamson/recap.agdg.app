import datetime

import dateutil.relativedelta

from . import app


def _timestamp_to_datestamp(timestamp: int) -> int:
    monday_date = (
        timestamp_date := datetime.datetime.fromtimestamp(
            float(str(timestamp)[:10]), tz=datetime.UTC
        )
    ) - datetime.timedelta(days=timestamp_date.weekday())
    week_length = 7
    week_threshold = week_length // 2
    week = (
        monday_date.day
        # First weekday maps to offset of 0, 1, 2, 3, -3, -2, -1
        + (
            (monday_date.replace(day=1).weekday() - week_threshold - 1) % week_length
            - week_threshold
        )
        - 1
    ) // week_length + 1

    if (
        (monday_date + dateutil.relativedelta.relativedelta(day=31)).day
        - monday_date.day
    ) < week_threshold:
        week = 1
        monday_date += dateutil.relativedelta.relativedelta(months=1)

    return int(f"{monday_date.strftime("%y%m")}{week}")


@app.route("/")
def index() -> str:  # noqa: D103
    return ""
