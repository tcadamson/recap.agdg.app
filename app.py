import calendar
import os
import re

from flask import Flask, render_template
from werkzeug.exceptions import HTTPException
from werkzeug.routing import BaseConverter, ValidationError

import database
import scraper

STATIC_PATH = "static"

class DatestampConverter(BaseConverter):
    regex = r"\d{5}"

    def to_python(self, value):
        # Overriding to_python isn't actually necessary (we don't transform the datestamp into a different object), however we need
        # it to perform additional validation not possible through regex
        if os.path.exists(f"{STATIC_PATH}/{value}"):
            return value
        raise ValidationError

app = Flask(__name__)
# https://werkzeug.palletsprojects.com/en/2.2.x/routing/#custom-converters
app.url_map.converters["datestamp"] = DatestampConverter
# https://jinja.palletsprojects.com/en/3.0.x/templates/#whitespace-control
app.jinja_options["trim_blocks"] = True
app.jinja_options["lstrip_blocks"] = True

@app.route("/")
def index():
    return render_template("index.html", datestamp = scraper.decode_unix())

@app.route("/archive")
def archive():
    recaps = []
    for datestamp in [x.name for x in os.scandir(STATIC_PATH) if x.is_dir()]:
        datestamp_match = re.search(r"^(?P<year>\d{2})(?P<month>\d{2})(?P<week>\d)$", datestamp)
        if datestamp_match:
            recaps.append({k: datestamp_match.group(k) for k in datestamp_match.groupdict().keys()})
    return render_template("archive.html", recaps = recaps)

@app.route("/view/<datestamp:datestamp>")
def view(datestamp):
    unions = []
    filenames = [x.split(".")[0] for x in os.listdir(f"{STATIC_PATH}/{datestamp}")]
    connection = database.Connection(memory = True)
    cursor = connection.execute(f"select * from posts where unix in ({','.join(['?'] * len(filenames))})", filenames)
    if cursor:
        for post in cursor.fetchall():
            unions.append({**connection.get_row("games", post["game_id"])} | {**post})
    connection.close()
    # Jinja2's groupby filter always sorts by the grouper (in this case, title), discarding insertion order. As a consequence,
    # we have to pass in the titles manually
    return render_template("view.html", datestamp = datestamp, unions = unions, titles = dict.fromkeys([x["title"] for x in unions]))

@app.errorhandler(HTTPException)
def error(http_exception):
    return render_template("error.html", http_exception = http_exception), http_exception.code

@app.template_filter()
def month_name(month_index):
    return calendar.month_name[int(month_index)]