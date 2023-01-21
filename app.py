import time

from flask import Flask, render_template

import scraper

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html", datestamp = scraper.decode_unix(time.time()))

@app.route("/view/<datestamp>")
def view(datestamp):
    return render_template("view.html", datestamp = datestamp)
