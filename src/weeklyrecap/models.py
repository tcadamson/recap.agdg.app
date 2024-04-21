import sqlalchemy as sql
import sqlalchemy.orm as sql_orm

from . import database


class Game(database.Base):
    """Represents a game in the database."""

    __tablename__ = "game"

    game_id: sql_orm.Mapped[int] = sql_orm.mapped_column(
        primary_key=True, autoincrement=True
    )
    title: sql_orm.Mapped[str] = sql_orm.mapped_column(
        sql.Text(collation="nocase"), unique=True
    )
    dev: sql_orm.Mapped[str | None]
    tools: sql_orm.Mapped[str | None]
    web: sql_orm.Mapped[str | None]

    posts: sql_orm.Mapped[list["Post"]] = sql_orm.relationship(
        back_populates="game", cascade="all, delete-orphan"
    )


class Post(database.Base):
    """Represents a post associated with a game in the database."""

    __tablename__ = "post"

    post_id: sql_orm.Mapped[int] = sql_orm.mapped_column(
        primary_key=True, autoincrement=True
    )
    game_id: sql_orm.Mapped[int] = sql_orm.mapped_column(
        sql.ForeignKey("game.game_id", onupdate="cascade", ondelete="cascade")
    )
    unix: sql_orm.Mapped[int]
    filename: sql_orm.Mapped[str | None]
    progress: sql_orm.Mapped[str]

    game: sql_orm.Mapped["Game"] = sql_orm.relationship(back_populates="posts")
