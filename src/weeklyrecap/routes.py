import calendar
import datetime
import re

import flask
import werkzeug.exceptions

from . import app


def _timestamp_to_datestamp(timestamp: float) -> int:
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


@app.template_filter()
def full_datestamp(datestamp: int) -> str:  # noqa: D103
    if not (datestamp_match := re.search(r"^(\d{2})(\d{2})(\d)$", str(datestamp))):
        return ""

    year, month, week = datestamp_match.groups()

    return f"{calendar.month_name[int(month)]} {2000 + int(year)}, Week {week}"


@app.errorhandler(werkzeug.exceptions.HTTPException)
def error(exception: werkzeug.exceptions.HTTPException) -> tuple[str, int]:  # noqa: D103
    return flask.render_template(
        "error.html", exception=exception
    ), exception.code or 500


@app.route("/")
def index() -> str:  # noqa: D103
    return flask.render_template(
        "index.html",
        datestamp=_timestamp_to_datestamp(
            datetime.datetime.now(datetime.UTC).timestamp()
        ),
    )


@app.route("/archive")
def archive() -> str:  # noqa: D103
    return ""


@app.route("/leaderboard")
def leaderboard() -> str:  # noqa: D103
    return ""


@app.route("/view/<int:datestamp>")
def view(_datestamp: int) -> str:  # noqa: D103
    return ""


@app.route("/games", methods=["GET", "POST"])
def games() -> str:  # noqa: D103
    return ""


@app.route("/game/<int:game_id>")
def game(_game_id: int) -> str:  # noqa: D103
    return ""
