import logging

import scraper

logging.basicConfig(
    format = "%(asctime)s :: %(levelname)s [%(filename)s:%(lineno)d] :: %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
    level = logging.DEBUG
)
logger = logging.getLogger(__name__)

def main():
    scraper.scrape()

if __name__ == "__main__":
    main()
