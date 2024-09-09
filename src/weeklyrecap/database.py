import typing

import sqlalchemy.orm

from . import app, config

_PrimaryKey = typing.Annotated[
    int, sqlalchemy.orm.mapped_column(primary_key=True, autoincrement=True)
]

_session = sqlalchemy.orm.scoped_session(
    sqlalchemy.orm.sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=sqlalchemy.create_engine(config.sqlalchemy_database_uri),
    )
)


class _Base(sqlalchemy.orm.DeclarativeBase):
    pass


class _Game(_Base):
    __tablename__ = "game"

    game_id: sqlalchemy.orm.Mapped[_PrimaryKey]
    title: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Text(collation="nocase"), unique=True
    )
    dev: sqlalchemy.orm.Mapped[str | None]
    tools: sqlalchemy.orm.Mapped[str | None]
    web: sqlalchemy.orm.Mapped[str | None]

    posts: sqlalchemy.orm.Mapped[list["_Post"]] = sqlalchemy.orm.relationship(
        back_populates="game", cascade="all, delete-orphan"
    )


class _Post(_Base):
    __tablename__ = "post"

    post_id: sqlalchemy.orm.Mapped[_PrimaryKey]
    game_id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.ForeignKey("game.game_id", onupdate="cascade", ondelete="cascade")
    )
    timestamp: sqlalchemy.orm.Mapped[int]
    filename: sqlalchemy.orm.Mapped[str | None]
    progress: sqlalchemy.orm.Mapped[str]

    game: sqlalchemy.orm.Mapped["_Game"] = sqlalchemy.orm.relationship(
        back_populates="posts"
    )


def get_game(title: str) -> _Game | None:  # noqa: D103
    return _session.scalar(sqlalchemy.select(_Game).filter_by(title=title))


def add_game(title: str) -> _Game:  # noqa: D103
    _session.add(game := _Game(title=title))
    _session.flush()

    return game


def add_post(  # noqa: D103
    game_id: int, timestamp: int, filename: str | None, progress: str
) -> _Post:
    _session.add(
        post := _Post(
            game_id=game_id, timestamp=timestamp, filename=filename, progress=progress
        )
    )

    return post


def commit() -> None:  # noqa: D103
    _session.commit()


@app.teardown_appcontext
def _remove_session(_exception: BaseException | None) -> None:
    _session.remove()


_Base.metadata.create_all(bind=_session.get_bind())
