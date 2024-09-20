import calendar
import datetime

import flask
import werkzeug.exceptions

from . import app, common, database


def _get_page() -> int:
    return flask.request.args.get("page", type=int, default=1)


def _get_bundle(
    game_: database.Game, post: database.Post, *excluded_keys: str
) -> dict[str, object]:
    return {
        key: value
        for key, value in (game_.serialized | post.serialized).items()
        if key not in excluded_keys
    }


@app.template_filter()
def datestamp_text(datestamp: int) -> str:  # noqa: D103
    return (
        f"{month_text(common.datestamp_month(datestamp))} "
        f"{common.datestamp_year(datestamp)}: Week "
        f"{common.datestamp_week(datestamp)}"
    )


@app.template_filter()
def month_text(month: int) -> str:  # noqa: D103
    return calendar.month_name[month]


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
    return flask.render_template(
        "archive.html",
        bundles=[
            {
                "datestamp": datestamp,
                "game_count": game_count,
                "year": common.datestamp_year(datestamp),
                "month": common.datestamp_month(datestamp),
                "week": common.datestamp_week(datestamp),
            }
            for datestamp, game_count in database.get_archive_data()
        ],
    )


@app.route("/rankings")
def rankings() -> str:  # noqa: D103
    superior_ranks = ["emperor"] + ["consul"] * 10 + ["patrician"] * 30

    return flask.render_template(
        "rankings.html",
        bundles=[
            game_.serialized
            | {
                "score": score,
                "rank": superior_ranks[i] if i < len(superior_ranks) else "plebeian",
            }
            for i, (game_, score) in enumerate(database.get_rankings_data())
        ],
    )


@app.route("/view/<int:datestamp>")
def view(_datestamp: int) -> str:  # noqa: D103
    return ""


@app.route("/games", methods=["GET", "POST"])
def games() -> str:  # noqa: D103
    search = flask.request.form.get("search", flask.request.args.get("search"))

    return flask.render_template(
        "games.html",
        bundles=[
            _get_bundle(game_, post, "progress")
            for game_, post in database.get_games_data(search)
        ],
        page=_get_page(),
        search=search,
    )


@app.route("/games/<int:game_id>")
def game(game_id: int) -> str:  # noqa: D103
    if not (game_ := database.get_game(game_id)):
        flask.abort(404)

    return flask.render_template(
        "game.html",
        bundles=[_get_bundle(game_, post, *common.GAME_KEYS) for post in game_.posts],
        page=_get_page(),
    )
