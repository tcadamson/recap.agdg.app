import time

from flask import Flask, render_template

import scraper

app = Flask(__name__)
# https://jinja.palletsprojects.com/en/3.0.x/templates/#whitespace-control
app.jinja_options["trim_blocks"] = True
app.jinja_options["lstrip_blocks"] = True

@app.route("/")
def home():
    return render_template("home.html", datestamp = scraper.decode_unix(time.time()))

@app.route("/view/<datestamp>")
def view(datestamp):
    return render_template("view.html", datestamp = datestamp)
