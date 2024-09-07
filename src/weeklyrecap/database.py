import typing

import sqlalchemy as sql
import sqlalchemy.orm as sql_orm

from . import app, config

_PrimaryKey = typing.Annotated[
    int, sql_orm.mapped_column(primary_key=True, autoincrement=True)
]

_session = sql_orm.scoped_session(
    sql_orm.sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=sql.create_engine(config.sqlalchemy_database_uri),
    )
)


class _Base(sql_orm.DeclarativeBase):
    pass


class _Game(_Base):
    __tablename__ = "game"

    game_id: sql_orm.Mapped[_PrimaryKey]
    title: sql_orm.Mapped[str] = sql_orm.mapped_column(
        sql.Text(collation="nocase"), unique=True
    )
    dev: sql_orm.Mapped[str | None]
    tools: sql_orm.Mapped[str | None]
    web: sql_orm.Mapped[str | None]

    posts: sql_orm.Mapped[list["_Post"]] = sql_orm.relationship(
        back_populates="game", cascade="all, delete-orphan"
    )


class _Post(_Base):
    __tablename__ = "post"

    post_id: sql_orm.Mapped[_PrimaryKey]
    game_id: sql_orm.Mapped[int] = sql_orm.mapped_column(
        sql.ForeignKey("game.game_id", onupdate="cascade", ondelete="cascade")
    )
    timestamp: sql_orm.Mapped[int]
    filename: sql_orm.Mapped[str | None]
    progress: sql_orm.Mapped[str]

    game: sql_orm.Mapped["_Game"] = sql_orm.relationship(back_populates="posts")


def get_game(title: str) -> _Game | None:
    """Get the game from the database using the title key."""
    return _session.scalar(sql.select(_Game).filter_by(title=title))


def add_game(title: str) -> _Game:
    """Add the game to the database."""
    _session.add(game := _Game(title=title))
    _session.flush()

    return game


def add_post(
    game_id: int, timestamp: int, filename: str | None, progress: str
) -> _Post:
    """Add the post to the database."""
    _session.add(
        post := _Post(
            game_id=game_id, timestamp=timestamp, filename=filename, progress=progress
        )
    )

    return post


def commit() -> None:
    """Commit pending changes to the database."""
    _session.commit()


@app.teardown_appcontext
def _remove_session(_exception: BaseException | None) -> None:
    _session.remove()


_Base.metadata.create_all(bind=_session.get_bind())
