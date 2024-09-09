import calendar
import datetime

FIELDS = ["dev", "tools", "web"]


def timestamp_to_datestamp(timestamp: float) -> int:  # noqa: D103
    monday_date = (
        timestamp_date := datetime.datetime.fromtimestamp(
            float(str(timestamp)[:10]), tz=datetime.UTC
        )
    ) - datetime.timedelta(days=timestamp_date.weekday())
    month_weekday, month_days = calendar.monthrange(monday_date.year, monday_date.month)
    week_delta = datetime.timedelta(weeks=1)
    week_threshold = week_delta.days // 2
    week = (
        monday_date.day
        # Offset: 0, 1, 2, 3, -3, -2, -1 (Monday - Sunday)
        + ((month_weekday - week_threshold - 1) % week_delta.days - week_threshold)
        - 1
    ) // week_delta.days + 1

    if (month_days - monday_date.day) < week_threshold:
        week = 1
        monday_date += week_delta

    return int(f"{monday_date.strftime("%y%m")}{week}")
