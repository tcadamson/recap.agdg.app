import logging
import database
import scrape

logging.basicConfig(
    format = "%(asctime)s :: %(levelname)s [%(filename)s:%(lineno)d] :: %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
    level = logging.DEBUG
)
logger = logging.getLogger(__name__)

def main():
    connection = database.Connection(memory = True)
    scraper = scrape.FourChannelScraper()
    logger.info(scraper.get_agdg_thread())
    logger.info(connection.get_game_id("Frostbite"))
    connection.close()

if __name__ == "__main__":
    main()
