import typing

import sqlalchemy as sql
import sqlalchemy.orm as sql_orm

from . import app

session = sql_orm.scoped_session(
    sql_orm.sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=sql.create_engine(
            typing.cast(str, app.config.get("SQLALCHEMY_DATABASE_URI"))
        ),
    )
)


class Base(sql_orm.MappedAsDataclass, sql_orm.DeclarativeBase):  # noqa: D101
    @sql_orm.declared_attr.directive
    def __tablename__(self: "Base") -> str:  # noqa: D105
        return self.__name__.lower()


def init() -> None:
    """Create database tables and set up session handling in Flask."""
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=session.get_bind())

    # https://docs.sqlalchemy.org/en/20/orm/contextual.html#using-thread-local-scope-with-web-applications
    app.teardown_appcontext(lambda _exception: session.remove())
