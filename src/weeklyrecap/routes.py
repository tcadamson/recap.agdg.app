import calendar
import datetime
import re

import dateutil.relativedelta
import flask
import werkzeug.exceptions

from . import app


def _timestamp_to_datestamp(timestamp: float) -> int:
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
