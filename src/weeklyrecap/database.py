import typing

import sqlalchemy.ext.hybrid
import sqlalchemy.orm

from . import app, common, config

_primary_key = typing.Annotated[
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
    __abstract__ = True

    @property
    def serialized(self) -> dict[str, object]:
        return {
            key: value
            for key in [
                column.key for column in sqlalchemy.inspect(self.__mapper__).columns
            ]
            if (value := getattr(self, key, None)) is not None
        }


class Game(_Base):  # noqa: D101
    __tablename__ = "game"

    game_id: sqlalchemy.orm.Mapped[_primary_key]
    title: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Text(collation="nocase"), unique=True
    )
    dev: sqlalchemy.orm.Mapped[str | None]
    tools: sqlalchemy.orm.Mapped[str | None]
    web: sqlalchemy.orm.Mapped[str | None]

    posts: sqlalchemy.orm.Mapped[list["Post"]] = sqlalchemy.orm.relationship(
        back_populates="game", cascade="all, delete-orphan"
    )


class Post(_Base):  # noqa: D101
    __tablename__ = "post"

    post_id: sqlalchemy.orm.Mapped[_primary_key]
    game_id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.ForeignKey("game.game_id", onupdate="cascade", ondelete="cascade")
    )
    datestamp: sqlalchemy.orm.Mapped[int]
    timestamp: sqlalchemy.orm.Mapped[int]
    filename: sqlalchemy.orm.Mapped[str | None]
    progress: sqlalchemy.orm.Mapped[str]

    game: sqlalchemy.orm.Mapped["Game"] = sqlalchemy.orm.relationship(
        back_populates="posts"
    )

    @sqlalchemy.ext.hybrid.hybrid_property
    def year(self) -> int:  # noqa: D102
        return common.datestamp_year(self.datestamp)

    @sqlalchemy.ext.hybrid.hybrid_property
    def month(self) -> int:  # noqa: D102
        return common.datestamp_month(self.datestamp)

    @sqlalchemy.ext.hybrid.hybrid_property
    def week(self) -> int:  # noqa: D102
        return common.datestamp_week(self.datestamp)


def get_game(game_id: int) -> Game | None:  # noqa: D103
    return _session.scalar(sqlalchemy.select(Game).filter_by(game_id=game_id))


def get_game_id(title: str) -> int | None:  # noqa: D103
    return _session.scalar(sqlalchemy.select(Game.game_id).filter_by(title=title))


def get_archive_data() -> list[tuple[int, int]]:  # noqa: D103
    game_counts = (
        sqlalchemy.select(
            Post.year,
            sqlalchemy.func.count(Post.game_id.distinct()).label("game_count"),
        )
        .group_by(Post.year)
        .subquery()
    )

    return [
        row.tuple()
        for row in _session.execute(
            sqlalchemy.select(Post.datestamp.distinct(), game_counts.c.game_count)
            .join(game_counts, Post.year.is_(game_counts.c.year))
            .order_by(Post.datestamp)
        ).all()
    ]


def get_rankings_data() -> list[tuple[Game, int]]:  # noqa: D103
    return [
        row.tuple()
        for row in _session.execute(
            sqlalchemy.select(
                Game,
                sqlalchemy.func.count(Post.datestamp.distinct()).label("score"),
            )
            .join(Game.posts)
            .group_by(Game.title)
            .order_by(
                sqlalchemy.desc("score"),
                sqlalchemy.desc(sqlalchemy.func.max(Post.timestamp)),
            )
        )
    ]


def get_games_data(search: str | None = None) -> list[tuple[Game, Post]]:  # noqa: D103
    random_post = sqlalchemy.select(
        Post,
        sqlalchemy.func.row_number()
        .over(
            partition_by=Post.game_id,
            order_by=[Post.filename.is_(None), sqlalchemy.func.random()],
        )
        .label("row_number"),
    ).subquery()
    query = (
        sqlalchemy.select(Game, sqlalchemy.orm.aliased(Post, random_post))
        .join(
            sqlalchemy.select(
                Post.game_id,
                sqlalchemy.func.max(Post.timestamp).label("max_timestamp"),
            )
            .group_by(Post.game_id)
            .subquery()
        )
        .join(random_post)
        .filter(random_post.c.row_number.is_(1))
        .order_by(sqlalchemy.desc("max_timestamp"))
    )

    if search:
        query = query.filter(
            sqlalchemy.or_(
                Game.title.ilike(f"%{search}%"),
                *[getattr(Game, key).ilike(f"%{search}%") for key in common.GAME_KEYS],
            )
        )

    return [row.tuple() for row in _session.execute(query)]


def add_game(title: str) -> Game:  # noqa: D103
    _session.add(game := Game(title=title))

    # Force primary key assignment (autoflush only assigns primary key in queries)
    _session.flush()

    return game


def add_post(  # noqa: D103
    game_id: int, timestamp: int, filename: str | None, progress: str
) -> Post:
    _session.add(
        post := Post(
            game_id=game_id,
            datestamp=common.timestamp_to_datestamp(timestamp),
            timestamp=timestamp,
            filename=filename,
            progress=progress,
        )
    )

    return post


def commit_session() -> None:  # noqa: D103
    _session.commit()


@app.teardown_appcontext
def _remove_session(_exception: BaseException | None) -> None:
    _session.remove()


_Base.metadata.create_all(bind=_session.get_bind())
