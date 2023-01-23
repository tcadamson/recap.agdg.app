import logging
import re
import sqlite3

COLUMN_DEFAULTS = {
    "INTEGER": 0,
    "TEXT": ""
}

logger = logging.getLogger(__name__)

class Connection:
    def __init__(self, database_name = "recap", memory = False):
        """
        Connection class provides an interface for interacting with the SQLite database file. If the database file does not exist
        (e.g. on initial run), it is created using the included schema. Must be closed with the close() method after use.

        :param database_name: Database filename
        :param memory: Memory mode flag
        """
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
        self.source.row_factory = sqlite3.Row
        # Enable foreign key constraints
        self.source.execute("pragma foreign_keys = on;")

    def execute(self, query, parameters = ()):
        """
        Helper for executing queries on the connection object. Uses the connection as a context manager for automatic transaction
        management (https://docs.python.org/3.9/library/sqlite3.html#using-the-connection-as-a-context-manager) and provides
        informative error handling.

        :param query: Query string
        :param parameters: Values to substitute into any query placeholders
        :return: Cursor (on successful execution)
        """
        try:
            with self.source:
                return self.source.execute(query, parameters)
        except sqlite3.Error as error:
            logger.error(re.sub(r"class \'(.+)\'", r"\1", str(error.__class__)) + f" {error}")

    def insert_row(self, table, **kwargs):
        """
        Inserts a row into the table using the given column data. Column schema is determined programmatically and default values
        are used when applicable. If the specified columns do not exist in the schema, insertion will fail and raise an SQL
        exception instead of quietly sanitizing the input (by design, to help with debugging).

        :param table: Table name
        :param kwargs: Column values to insert
        :return: Row object (on successful insertion)
        """
        row_data = {
            k: COLUMN_DEFAULTS[v] for k, v in self.execute(f"select name, type from pragma_table_info('{table}') where pk != 1").fetchall()
        } | kwargs
        query_columns = ",".join(row_data.keys())
        query_placeholders = ":" + ",:".join(row_data.keys())
        cursor = self.execute(f"insert into {table} ({query_columns}) values ({query_placeholders});", row_data)
        if cursor:
            # https://peps.python.org/pep-0249/#lastrowid
            return self.get_row(table, cursor.lastrowid)

    def update_row(self, table, row_id, **kwargs):
        query_column_pairs = ",".join([f"{x}=?" for x in kwargs.keys()])
        self.execute(f"update {table} set {query_column_pairs} where id = ?;", tuple(kwargs.values()) + (row_id,))

    def get_row(self, table, row_id = None, **kwargs):
        return self.execute(f"select * from {table} where id = ?;", (row_id or self.get_id(table, **kwargs),)).fetchone()

    def get_id(self, table, **kwargs):
        """
        Gets the ID for a row given a separate key column value. Note that only the first kwarg pair is taken, and this pair must
        correspond to a key column, since multiple rows could match otherwise (only the first would be selected).

        :param table: Table name
        :param kwargs: Key column value
        :return: Row ID (on successful match)
        """
        key = next(iter(kwargs))
        cursor = self.execute(f"select id from {table} where {key} = :{key};", kwargs).fetchone()
        if cursor:
            return cursor["id"]

    def close(self):
        self.source.close()
