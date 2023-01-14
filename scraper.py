import calendar
import datetime
import functools
import html
import json
import logging
import re
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

def is_agdg_thread(op = None, thread_no = None):
    """
    Helper for determining /agdg/ threads through the subject attribute of the opening post object. Sometimes the post object
    isn't immediately accessible, e.g. when processing the archive, which is just a collection of thread numbers. In these
    cases, the thread number may be used directly, albeit with the more expensive get_json call.
    :param op: Opening post object to evaluate
    :param thread_no: Thread number to retrieve opening post object from (if post object unavailable)
    :return: Boolean result
    """
    if thread_no:
        thread = get_json(thread_no = thread_no)
        if thread:
            op = thread["posts"][0]
        else:
            # Most likely a 404 due to mods manually deleting the thread
            return False
    return "agdg" in op.get("sub", "").casefold()

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
    threads = [x for x in (set(archived) - set(cached)) if is_agdg_thread(thread_no = x)]
    for page in get_json(URLS["CATALOG"]):
        for op in page["threads"]:
            if is_agdg_thread(op):
                threads.append(op["no"])
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

def process_post(post, connection):
    """
    Parses any recap data found in the given post and adds it to the posts table. Additionally, updates a game's properties if
    those fields are present (dev, tools, web). See below for the expected format. It should be noted that only "title" and
    "progress" are strictly necessary; the aforementioned property fields are optional.
    :: (title) ::
    dev ::
    tools ::
    web ::
    (progress)
    :param post: Post object to process
    :param connection: Database connection
    :return: None
    """
    comment = html.unescape(post.get("com", ""))
    field_pattern = r"<br>(dev|tools|web)\s?::\s?(.*?)(?=<br>|$)"
    for sanitize_pattern in [
        r"\\(\S)",
        r"\s?(<br>)\s?",
        r"<span.+?>(.+?)</span>"
    ]:
        comment = re.sub(sanitize_pattern, r"\1", comment)
    recap_match = re.search(r"::\s?(.+?)\s?::\s?(.+$)", comment)
    if recap_match:
        title = recap_match.group(1)
        body = recap_match.group(2)
        game_data = {"title": title} | {k.casefold(): v for k, v in re.findall(field_pattern, body, flags = re.IGNORECASE)}
        game = connection.get_game(title) or connection.insert_row("games", **game_data)
        connection.insert_row("posts", {
            "game_id": game["id"],
            "unix": post.get("tim", post["time"]),
            "ext": post.get("ext", ""),
            "progress": re.sub(r"^(<br>)*", "", re.split(field_pattern, body)[-1])
        })
        connection.update_game_columns(game, **game_data)

def scrape():
    connection = database.Connection(memory = True)
    for thread_no in get_agdg_threads():
        for post in get_json(thread_no = thread_no)["posts"]:
            process_post(post, connection)
    connection.close()
