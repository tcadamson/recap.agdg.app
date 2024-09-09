import pathlib

import flask
import pydantic
import pydantic_settings

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
    sqlalchemy_database_uri: str


try:
    config = _Config()
except pydantic.ValidationError as e:
    app.logger.critical(e)
    raise

if not instance_path.exists():
    instance_path.mkdir()

from . import database, routes, scraper  # noqa: E402, F401
