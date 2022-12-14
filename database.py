import sqlite3

database_name = "recap"

try:
    # Connect without implicitly creating a new database
    # See https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris)
    connection = sqlite3.connect("file:{}.db?mode=rw".format(database_name), uri = True)
except sqlite3.OperationalError:
    connection = sqlite3.connect("{}.db".format(database_name))
    with open("{}.sql".format(database_name), "r") as schema:
        connection.executescript(schema.read())
connection.execute("pragma foreign_keys = on;") # Enable foreign key constraints

def query_game_id(game):
    result = connection.execute("select game_id from games where game = ?", (game,)).fetchone()
    return result[0] if result else None

def insert_game(post):
    try:
        with connection:
            connection.execute("insert into games (game, dev, tools, web) values (:game, :dev, :tools, :web)", post)
        return query_game_id(post["game"])
    except sqlite3.Error as error:
        print(error)

def insert_post(post):
    try:
        with connection:
            # TODO: Construct post object from scraped data
            game_id = query_game_id(post.game)
            if game_id is None:
                game_id = insert_game(post)
            connection.execute("insert into posts (game_id, unix, ext, progress) values (?, ?, ?, ?)", (game_id, post["unix"], post["ext"], post["progress"]))
    except sqlite3.Error as error:
        print(error)

def close():
    connection.close()
