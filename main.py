import logging
import database

logging.basicConfig(
    format = "%(asctime)s :: %(levelname)s [%(filename)s:%(lineno)d] :: %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
    level = logging.DEBUG
)
logger = logging.getLogger(__name__)

def main():
    connection = database.Connection(memory = True)
    logger.info(connection.query_game_id("Frostbite"))
    connection.close()

if __name__ == "__main__":
    main()
