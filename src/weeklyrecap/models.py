import typing

import sqlalchemy as sql
import sqlalchemy.orm as sql_orm

from . import database

_PK = typing.Annotated[int, sql_orm.mapped_column(primary_key=True, autoincrement=True)]


class Game(database.Base):
    """Represents a game in the database."""

    # Columns
    game_id: sql_orm.Mapped[_PK] = sql_orm.mapped_column(init=False)
    title: sql_orm.Mapped[str] = sql_orm.mapped_column(
        sql.Text(collation="nocase"), unique=True
    )
    dev: sql_orm.Mapped[str] = sql_orm.mapped_column(default=None)
    tools: sql_orm.Mapped[str] = sql_orm.mapped_column(default=None)
    web: sql_orm.Mapped[str] = sql_orm.mapped_column(default=None)

    # Relationships
    posts: sql_orm.Mapped[list["Post"]] = sql_orm.relationship(
        back_populates="game", cascade="all, delete-orphan", default_factory=list
    )


class Post(database.Base, kw_only=True):
    """Represents a post associated with a game in the database."""

    # Columns
    post_id: sql_orm.Mapped[_PK] = sql_orm.mapped_column(init=False)
    game_id: sql_orm.Mapped[int] = sql_orm.mapped_column(
        sql.ForeignKey("game.game_id", onupdate="cascade", ondelete="cascade")
    )
    unix: sql_orm.Mapped[int]
    filename: sql_orm.Mapped[str] = sql_orm.mapped_column(default=None)
    progress: sql_orm.Mapped[str]

    # Relationships
    game: sql_orm.Mapped["Game"] = sql_orm.relationship(
        back_populates="posts", default=None
    )
