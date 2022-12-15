import logging
import json
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

def get_json(url):
    try:
        with urllib.request.urlopen(url) as data:
            return json.load(data)
    except urllib.error.HTTPError as error:
        logger.error(f"{url} returned {error}")

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
