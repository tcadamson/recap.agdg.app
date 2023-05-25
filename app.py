import bisect
import calendar
import glob
import pathlib
import re
import urllib.parse

from flask import Flask, render_template, request, abort
from urlextract import URLExtract
from werkzeug.exceptions import HTTPException

import database
import scraper

STATIC_PATH = "static"
# Legacy recaps have entries that don't "belong", i.e. the unix timestamp doesn't match the datestamp. This is because entries
# were manually collected at the end of the week. As a consequence, we map each unix timestamp to the correct datestamp
LEGACY_UNIX_TO_DATESTAMP = {
    int(k.stem): int(k.parent.stem) for k in pathlib.Path(STATIC_PATH).rglob("*/*") if str(scraper.decode_unix(k.stem)) != k.parent.stem
}

app = Flask(__name__)
url_extractor = URLExtract()
# https://pypi.org/project/urlextract
url_extractor.update()
# https://jinja.palletsprojects.com/en/3.0.x/templates/#whitespace-control
app.jinja_options["trim_blocks"] = True
app.jinja_options["lstrip_blocks"] = True

def split_datestamp(datestamp):
    split_match = re.search(r"(?P<year>\d{2})(?P<month>\d{2})(?P<week>\d)", str(datestamp))
    if split_match:
        return {k: split_match.group(k) for k in split_match.groupdict().keys()}

def get_page():
    return int(request.args.get("page", default = 1))

@app.route("/")
def index():
    return render_template("index.html.jinja", datestamp = scraper.decode_unix())

@app.route("/archive")
def archive():
    return render_template("archive.html.jinja", datestamps = [split_datestamp(x) for x in glob.glob(f"{STATIC_PATH}/*/") if x])

@app.route("/view/<int:datestamp>")
def view(datestamp):
    rows = []
    connection = database.Connection(memory = True)
    cursor = connection.execute("""
        select *
        from games
        join posts on
            games.id = posts.game_id
        where decode_unix(unix) == ?
        order by substr(unix, 1)
    """, (datestamp,))
    if cursor:
        rows = cursor.fetchall()
    if not rows:
        abort(404)
    connection.close()
    return render_template("view.html.jinja", datestamp = datestamp, rows = rows)

@app.route("/games")
def games():
    rows = []
    connection = database.Connection(memory = True)
    cursor = connection.execute("""
        select *
        from (
            select games.id, title, dev, tools, web, unix, ext
            from games
            join posts on
                games.id = posts.game_id
            where ext != ''
            or games.id not in (
                select game_id from posts where ext != ''
            )
            order by random()
        )
        group by id
        order by id desc
    """)
    if cursor:
        rows = cursor.fetchall()
    connection.close()
    return render_template("games.html.jinja", rows = rows, page = get_page())

@app.route("/games/<int:game_id>")
def game(game_id):
    rows = []
    connection = database.Connection(memory = True)
    game_data = connection.get_row("games", game_id)
    if not game_data:
        abort(404)
    cursor = connection.execute("select * from posts where game_id = ? order by substr(unix, 1) desc", (game_id,))
    if cursor:
        rows = cursor.fetchall()
    connection.close()
    return render_template("game.html.jinja", rows = rows, page = get_page(), game_data = game_data)

@app.errorhandler(HTTPException)
def error(http_exception):
    return render_template("error.html.jinja", http_exception = http_exception), http_exception.code

@app.template_filter()
def full_year(year):
    return 2000 + int(year)

@app.template_filter()
def calendar_month(month_index):
    return calendar.month_name[int(month_index)]

@app.template_filter()
def decode_unix(unix):
    legacy_unix = [*LEGACY_UNIX_TO_DATESTAMP]
    padded_unix = unix * 1000
    # Null entry (no attached media, no microtime) belonging to a legacy recap
    if padded_unix < legacy_unix[-1]:
        i = bisect.bisect_right(legacy_unix, padded_unix)
        # Null entries on an edge borrow the unix timestamp from the nearest non-null entry, truncate microtime, then + or - 1
        # depending on edge, e.g.
        # 1519635518161 -> 1519635517
        # 1527082325055 -> 1527082326
        unix = legacy_unix[i] if (legacy_unix[i] - padded_unix) < 2000 else legacy_unix[i - 1]
    return LEGACY_UNIX_TO_DATESTAMP.get(unix, scraper.decode_unix(unix))

@app.template_filter()
def urlize(text):
    # Overwrites the default urlize filter, which doesn't correctly handle all TLDs
    for url in url_extractor.find_urls(text):
        scheme = urllib.parse.urlparse(url).scheme
        text = re.sub(fr"({re.escape(url)})", fr'<a href="{"//" if not scheme else ""}\1">\1</a>', text)
    return text

@app.template_filter()
def semantic_datestamp(datestamp):
    datestamp_data = split_datestamp(datestamp)
    if datestamp_data:
        return f"{calendar_month(datestamp_data['month'])} {full_year(datestamp_data['year'])}, Week {datestamp_data['week']}"

@app.template_test()
def matches_datestamp(unix, datestamp):
    return decode_unix(unix) == datestamp

@app.template_test()
def nonempty_field_data(field_data):
    return "".join([dict(field_data).get(x, "") for x in ["dev", "tools", "web"]])
