import typing

import sqlalchemy as sql
import sqlalchemy.orm as sql_orm

from . import app

engine = sql.create_engine(typing.cast(str, app.config.get("SQLALCHEMY_DATABASE_URI")))
session = sql_orm.scoped_session(
    sql_orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)
)


class Base(sql_orm.DeclarativeBase, sql_orm.MappedAsDataclass):  # noqa: D101
    pass


def init() -> None:
    """Create database tables and set up session handling in Flask."""
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # https://docs.sqlalchemy.org/en/20/orm/contextual.html#using-thread-local-scope-with-web-applications
    app.teardown_appcontext(lambda _exception: session.remove())
