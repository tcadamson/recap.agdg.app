import calendar
import datetime
import functools
import html
import json
import logging
import urllib.error
import urllib.request

import math

import database

logger = logging.getLogger(__name__)

CACHE_PATH = "cache.json"
URLS = {
    "CATALOG": "https://a.4cdn.org/vg/catalog.json",
    "ARCHIVE": "https://a.4cdn.org/vg/archive.json",
    "THREAD": "https://a.4cdn.org/vg/thread/%d.json",
    "FILE": "https://i.4cdn.org/vg/%d%s"
}

@functools.lru_cache()
def get_json(url = None, thread_no = None):
    # Purely for convenience to access JSON for specified thread number
    if thread_no:
        url = URLS["THREAD"] % thread_no
    try:
        with urllib.request.urlopen(url) as data:
            return json.load(data)
    except urllib.error.HTTPError as error:
        logger.error(f"{url} returned {error}")

def get_agdg_threads():
    """
    Locates the threads that need to be processed by the scraper (in the catalog, or in the archive and not previously seen).
    A cache of previously seen thread numbers is utilized since JSON fetches could otherwise take upwards of a minute per
    function call.
    :return: List of thread numbers to process
    """
    cached = []
    archived = get_json(URLS["ARCHIVE"])
    try:
        with open(CACHE_PATH, "r") as cache:
            cached = json.load(cache)
    except IOError:
        logger.error("Thread cache couldn't be read")
    def is_agdg(post):
        return "agdg" in post.get("sub", "").casefold()
    threads = [x for x in (set(archived) - set(cached)) if is_agdg(get_json(thread_no = x)["posts"][0])]
    for page in get_json(URLS["CATALOG"]):
        for original_post in page["threads"]:
            if is_agdg(original_post):
                threads.append(original_post["no"])
    with open(CACHE_PATH, "w") as cache:
        json.dump(archived, cache, separators = (",", ":"))
    return threads

def decode_unix(unix):
    """
    Converts a unix timestamp to YYMMW format, e.g. 1587240724142 -> 20043
    Recap week begins every Monday at 12 AM (UTC), spanning Monday to Sunday inclusive; the date logic follows from this.
    :param unix: Unix timestamp (with or without microtime)
    :return: Corresponding datestamp of form YYMMW
    """
    date = datetime.datetime.fromtimestamp(int(str(unix)[:10]))
    day = date.day
    week_delta = datetime.timedelta(weeks = 1)
    week_threshold = math.ceil(week_delta.days / 2)
    if day < week_threshold < date.isoweekday():
        date -= datetime.timedelta(days = day)
        day += date.day
    first_weekday_index, total_days = calendar.monthrange(date.year, date.month)
    first_monday = (week_delta.days - first_weekday_index) + 1
    week = ((day - first_monday) // week_delta.days) + 1
    # Last day of month between M - W -> recap week rolls over to next month
    if (total_days - first_monday - week_delta.days * (week - 1)) in range (0, week_threshold - 1):
        week = 1
        # Advance date object to the next month just so strftime gives the correct year and month result (time delta is arbitrary)
        date += week_delta
    # First day of month between M - R -> recap week does not roll over
    elif first_weekday_index < week_threshold:
        week += 1
    return int(f"{date.strftime('%y%m')}{week}")

def scrape():
    """
    Iterates over all threads in need of processing, matching any posts with the recap format and adding their corresponding data
    to the SQLite database.
    """
    connection = database.Connection(memory = True)
    for thread_no in get_agdg_threads():
        for post in get_json(thread_no = thread_no)["posts"]:
            comment = html.unescape(post.get("com", "")).replace("<wbr>", "")
    connection.close()
