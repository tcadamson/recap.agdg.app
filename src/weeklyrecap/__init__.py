import os
import pathlib

from flask import Flask

app = Flask(
    __name__, instance_path=(pathlib.Path(__file__).parents[2] / "instance").as_posix()
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
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI")

pathlib.Path(app.instance_path).mkdir(exist_ok=True)

from . import database, routes  # noqa: E402, F401

database.init()
