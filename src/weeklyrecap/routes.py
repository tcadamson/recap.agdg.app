import calendar
import datetime
import re

import flask
import werkzeug.exceptions

from . import app, common


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
        datestamp=common.timestamp_to_datestamp(
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
