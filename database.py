import logging
import sqlite3

logger = logging.getLogger(__name__)

class Connection:
    def __init__(self, database_name = "recap", memory = False):
        try:
            # Connect without implicitly creating a new database
            # See https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris)
            source = sqlite3.connect(f"file:{database_name}.db?mode=rw", uri = True)
        except sqlite3.OperationalError:
            source = sqlite3.connect(f"{database_name}.db")
            with open(f"{database_name}.sql", "r") as schema:
                source.executescript(schema.read())
        # Memory mode opens the connection in RAM so operations are nondestructive
        if memory:
            target = sqlite3.connect(":memory:")
            with target:
                source.backup(target)
            source.close()
            self.source = target
        else:
            self.source = source
        # Enable foreign key constraints
        self.source.execute("pragma foreign_keys = on;")

    def get_game_id(self, game):
        game_id = self.source.execute("select game_id from games where game = ?", (game,)).fetchone()
        if game_id:
            return game_id[0]

    def insert_game(self, post):
        try:
            with self.source:
                self.source.execute("insert into games (game, dev, tools, web) values (:game, :dev, :tools, :web)", post)
            return self.get_game_id(post["game"])
        except sqlite3.Error as error:
            logger.error(error)

    def insert_post(self, post):
        try:
            with self.source:
                game_id = self.get_game_id(post["game"])
                if game_id is None:
                    game_id = self.get_game_id(post["game"])
                self.source.execute(
                    "insert into posts (game_id, unix, ext, progress) values (?, ?, ?, ?);",
                    (game_id, post["unix"], post["ext"], post["progress"])
                )
        except sqlite3.Error as error:
            logger.error(error)

    def close(self):
        self.source.close()
