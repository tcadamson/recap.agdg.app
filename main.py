import os
import re
import json
import sqlite3

db = sqlite3.connect(":memory:")

def process_weekly_data(path):
    for game, entry_data in json.load(open(path)).items():
        for filename, progress in entry_data.items():
            # Split legacy file strings like so
            # 1663593871:352651.webm -> '1663593871352651', '.webm'
            # 1669070581:default.png -> '1669070581', ''
            filename_parts = re.sub("(:)([^.]*)", "\g<2>\g<1>", filename).split(":")
            if "default" in filename_parts[0]:
                filename_parts = [re.sub("[.a-z]+", "", part) for part in filename_parts]
            game_id = db.execute("SELECT game_id FROM games WHERE game=?", (game,)).fetchone()[0]
            db.execute("INSERT INTO entries (game_id, stamp, ext, progress) VALUES (?, ?, ?, ?)", (game_id, filename_parts[0], filename_parts[1], progress))

if __name__ == "__main__":
    db.execute("PRAGMA foreign_keys = ON") # Enable foreign key constraints
    db.execute("""
        CREATE TABLE games (
            game_id INTEGER PRIMARY KEY AUTOINCREMENT,
            game TEXT UNIQUE NOT NULL,
            dev TEXT NOT NULL,
            tools TEXT NOT NULL,
            web TEXT NOT NULL
        )""")
    db.execute("""
        CREATE TABLE entries (
            entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER NOT NULL,
            stamp INTEGER NOT NULL,
            ext TEXT NOT NULL,
            progress TEXT NOT NULL,
            FOREIGN KEY (game_id) REFERENCES games (game_id)
                ON UPDATE CASCADE
                ON DELETE CASCADE
        )""")

    # Populate the games table from the old games data
    for game, game_data in json.load(open("recap.agdg.io/res/games.json")).items():
        db.execute("INSERT INTO games (game, dev, tools, web) VALUES (?, ?, ?, ?)", (game, game_data["dev"], game_data["tools"], game_data["web"]))
    # Populate the entries table from all the old weekly data
    for root, folders, files in os.walk("recap.agdg.io/res", topdown=True):
        for folder in folders:
            process_weekly_data(f"{os.path.join(root, folder)}/data.json")
    for entry in db.execute("SELECT * FROM entries LIMIT 10").fetchall():
        print(entry)

    # Commit to ensure there are no pending transactions before closing
    db.commit()
    db.close()
