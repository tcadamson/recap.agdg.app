import sqlite3

database_name = "recap"

if __name__ == "__main__":
    try:
        # Connect without implicitly creating a new database
        # See https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris)
        connection = sqlite3.connect("file:{}.db?mode=rw".format(database_name), uri = True)
    except sqlite3.OperationalError:
        connection = sqlite3.connect("{}.db".format(database_name))
        with open("{}.sql".format(database_name), "r") as schema:
            connection.executescript(schema.read())
    connection.execute("pragma foreign_keys = on;") # Enable foreign key constraints

    for game in connection.execute("select * from games").fetchall():
        print(game)

    connection.close()
