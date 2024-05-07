import enum
import functools
import typing

import requests

from . import app

_REQUEST_TIMEOUT_SECONDS: typing.Final = 10


class _Endpoint(enum.StrEnum):
    CATALOG = "https://a.4cdn.org/vg/catalog.json"
    ARCHIVE = "https://a.4cdn.org/vg/archive.json"
    THREAD = "https://a.4cdn.org/vg/thread/%d.json"
    MEDIA = "https://i.4cdn.org/vg/%d%s"


@functools.cache
def _request_json(endpoint: _Endpoint) -> object:
    try:
        return typing.cast(
            object, requests.get(endpoint, timeout=_REQUEST_TIMEOUT_SECONDS).json()
        )
    except requests.RequestException as e:
        app.logger.error("Request failed for %s: %r", endpoint, e)

    return None


@app.cli.command("scrape")
def scrape() -> None:  # noqa: D103
    app.logger.info(_request_json(_Endpoint.CATALOG))
