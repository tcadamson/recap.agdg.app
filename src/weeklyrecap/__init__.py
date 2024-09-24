import pathlib

import flask
import pydantic
import pydantic_settings

from . import common

app = flask.Flask(
    __name__,
    instance_path=(
        instance_path := pathlib.Path(__file__).parents[2] / "instance"
    ).as_posix(),
)
app.jinja_options = {
    # https://jinja.palletsprojects.com/en/3.1.x/templates/#extensions
    "extensions": [
        f"jinja2.ext.{extension_name}" for extension_name in ["loopcontrols", "do"]
    ],
    # https://jinja.palletsprojects.com/en/3.1.x/templates/#whitespace-control
    "trim_blocks": True,
    "lstrip_blocks": True,
}


class _Config(pydantic_settings.BaseSettings):
    SQLALCHEMY_DATABASE_URI: str
    CDN_DOMAIN: str


try:
    config = _Config()
except pydantic.ValidationError as e:
    app.logger.critical(e)
    raise

app.jinja_env.globals.update(GAME_KEYS=common.GAME_KEYS, CDN_DOMAIN=config.CDN_DOMAIN)

if not instance_path.exists():
    instance_path.mkdir()

# Import any modules that use Flask decorators
from . import database, routes, scraper  # noqa: E402, F401
