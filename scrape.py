import logging
import json
import datetime
import calendar
import math
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

CACHE_PATH = "cache.json"
URLS = {
    "CATALOG": "https://a.4cdn.org/vg/catalog.json",
    "ARCHIVE": "https://a.4cdn.org/vg/archive.json",
    "THREAD": "https://a.4cdn.org/vg/thread/%s.json",
    "FILE": "https://i.4cdn.org/vg/%d%s"
}

def get_json(url):
    try:
        with urllib.request.urlopen(url) as data:
            return json.load(data)
    except urllib.error.HTTPError as error:
        logger.error(f"{url} returned {error}")

def get_agdg_threads():
    cached = []
    archived = get_json(URLS["ARCHIVE"])
    try:
        with open(CACHE_PATH, "r") as cache:
            cached = json.load(cache)
    except IOError:
        logger.error("Thread cache couldn't be read")
    def is_agdg(post):
        return "agdg" in post.get("sub", "").casefold()
    # Check all newly archived threads (or if the cache is empty, all archived threads)
    threads = [no for no in set(archived) - set(cached) if is_agdg(get_json(URLS["THREAD"] % no)["posts"][0])]
    for page in get_json(URLS["CATALOG"]):
        for original_post in page["threads"]:
            if is_agdg(original_post):
                threads.append(original_post["no"])
    with open(CACHE_PATH, "w") as cache:
        json.dump(archived, cache, separators = (",", ":"))
    return threads

def decode_unix(unix):
    # Converts a unix timestamp to YYMMW format, e.g. 1587240724142 -> 20043
    # Recap week begins every Monday at 12 AM (UTC), spanning Monday to Sunday inclusive; date logic follows from this
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
