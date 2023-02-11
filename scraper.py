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

CACHE_PATH = "cache.json"
URLS = {
    "CATALOG": "https://a.4cdn.org/vg/catalog.json",
    "ARCHIVE": "https://a.4cdn.org/vg/archive.json",
    "THREAD": "https://a.4cdn.org/vg/thread/%d.json",
    "FILE": "https://i.4cdn.org/vg/%d%s"
}

logger = logging.getLogger(__name__)

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

    :return: List of /agdg/ thread numbers
    """
    cached = []
    archived = get_json(URLS["ARCHIVE"])
    try:
        with open(CACHE_PATH, "r") as cache:
            cached = json.load(cache)
    except IOError:
        logger.error("Failed to read thread cache")
    threads = [x for x in (set(archived) - set(cached)) if is_agdg_thread(thread_no = x)]
    for page in get_json(URLS["CATALOG"]):
        for op in page["threads"]:
            if is_agdg_thread(op):
                threads.append(op["no"])
    with open(CACHE_PATH, "w") as cache:
        json.dump(archived, cache, separators = (",", ":"))
    return threads

def decode_unix(unix = datetime.datetime.now(datetime.timezone.utc).timestamp()):
    """
    Converts a unix timestamp to YYMMW format, e.g. 1587240724142 -> 20043
    Recap week begins every Monday at 12 AM (UTC), spanning Monday to Sunday inclusive; the date logic follows from this.

    :param unix: Unix timestamp (with or without microtime)
    :return: Datestamp of form YYMMW
    """
    date = datetime.datetime.fromtimestamp(float(re.sub(r"(\d{10})(\d+)", r"\1.\2", str(unix))), tz = datetime.timezone.utc)
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
    those fields are present (dev, tools, web). It should be noted that only "title" is strictly necessary; if "title" is
    accompanied by at least one field and/or "progress", the post will be processed. Expected format:

    :: (title) ::
    dev ::
    tools ::
    web ::
    (progress)

    Lastly, a game's title may be updated through use of a special syntax:

    :: (old title) -> (new title) ::

    :param post: Post object
    :param connection: Database connection
    :return: None
    """
    comment = html.unescape(post.get("com", ""))
    field_pattern = r"(?:<br>)+(dev|tools|web)::((?:(?!::|<br>).)+?)(?=$|<br>)"
    for sanitize_pattern in [
        r"\\(\S)",
        r"<span.+?>(.+?)</span>",
        r"\s?(::):*\s?",
        r"\s?(->)\s?",
        r"\s?(<br>)\s?"
    ]:
        comment = re.sub(sanitize_pattern, r"\1", comment)
    recap_match = re.search(r"::((?:(?!->|<br>).)+?)(?:->((?:(?!<br>).)+?))?::(.+$)", comment)
    if recap_match:
        old_title = recap_match.group(1)
        new_title = recap_match.group(2)
        content = recap_match.group(3)
        # While the database already handles the unique title constraint, we want to fall back to the old title instead of
        # discarding the post entirely
        if not new_title or connection.get_row("games", title = new_title):
            new_title = old_title
        game_data = {"title": new_title} | {k.casefold(): v for k, v in re.findall(field_pattern, content, flags = re.IGNORECASE)}
        try:
            game_id = (connection.get_row("games", title = old_title) or connection.insert_row("games", **game_data))["id"]
            connection.update_row("games", game_id, **game_data)
            connection.insert_row("posts",
                game_id = game_id,
                unix = post.get("tim", post["time"]),
                ext = post.get("ext", ""),
                progress = re.search(r"^(?:<br>)*(?P<progress>.+)$", re.split(field_pattern, content)[-1]).group("progress")
            )
        except AttributeError:
            # Progress not found
            pass
        except TypeError:
            logger.error(f"Failed to parse https://arch.b4k.co/vg/thread/{post['resto']}/#{post['no']}")

def scrape():
    connection = database.Connection(memory = True)
    for thread_no in get_agdg_threads():
        for post in get_json(thread_no = thread_no)["posts"]:
            process_post(post, connection)
    connection.close()
