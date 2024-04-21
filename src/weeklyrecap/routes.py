from . import app


@app.route("/")
def index() -> str:  # noqa: D103
    return ""
