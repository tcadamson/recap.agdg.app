import typing

import sqlalchemy as sql
import sqlalchemy.orm as sql_orm

from . import app

_PK = typing.Annotated[int, sql_orm.mapped_column(primary_key=True, autoincrement=True)]

_session = sql_orm.scoped_session(
    sql_orm.sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=sql.create_engine(
            typing.cast(str, app.config.get("SQLALCHEMY_DATABASE_URI"))
        ),
    )
)


class Base(sql_orm.MappedAsDataclass, sql_orm.DeclarativeBase):
    """Define a declarative base class with common elements for derived model classes.

    Note that dataclass arguments (e.g. kw_only) should be passed as arguments to the
    derived model classes and not inherited. See:
    https://github.com/sqlalchemy/sqlalchemy/discussions/10219
    """

    @sql_orm.declared_attr.directive
    def __tablename__(self: "Base") -> str:  # noqa: D105
        return self.__name__.lower()


class Game(Base):
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


class Post(Base, kw_only=True):
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


@app.teardown_appcontext
def _teardown(_exception: BaseException | None) -> None:
    _session.remove()


Base.metadata.create_all(bind=_session.get_bind())
