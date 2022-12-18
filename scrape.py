import logging
import json
import datetime
import calendar
import math
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

def get_json(url):
    try:
        with urllib.request.urlopen(url) as data:
            return json.load(data)
    except urllib.error.HTTPError as error:
        logger.error(f"{url} returned {error}")

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

class Endpoint:
    catalog = "https://a.4cdn.org/vg/catalog.json"
    thread = "https://a.4cdn.org/vg/thread/%s.json"
    file = "https://i.4cdn.org/vg/%d%s"

class FourChannelScraper:
    def __init__(self):
        self.agdg_thread_no = 0

    def get_agdg_thread(self):
        for page in get_json(Endpoint.catalog):
            for thread in page["threads"]:
                if "agdg" in thread["sub"] and self.agdg_thread_no < thread["no"]:
                    self.agdg_thread_no = thread["no"]
        return get_json(Endpoint.thread % self.agdg_thread_no)
