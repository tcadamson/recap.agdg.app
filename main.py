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
    connection.close()
    logger.info(scrape.get_agdg_threads())

if __name__ == "__main__":
    main()
