import enum
import functools
import typing

import requests

from . import app

_REQUEST_TIMEOUT_SECONDS: typing.Final = 10

# https://github.com/4chan/4chan-API
_JsonResponse: typing.TypeAlias = dict[str, typing.Any] | list[typing.Any]


class _Endpoint(enum.StrEnum):
    CATALOG = "https://a.4cdn.org/vg/catalog.json"
    ARCHIVE = "https://a.4cdn.org/vg/archive.json"
    THREAD = "https://a.4cdn.org/vg/thread/%d.json"
    MEDIA = "https://i.4cdn.org/vg/%d%s"


@functools.lru_cache
def _request_json(url: _Endpoint) -> _JsonResponse | None:
    try:
        return typing.cast(
            _JsonResponse,
            requests.get(url, timeout=_REQUEST_TIMEOUT_SECONDS).json(),
        )
    except requests.exceptions.JSONDecodeError:
        app.logger.error("No valid JSON response from URL: %s", url)
    except requests.exceptions.ReadTimeout:
        app.logger.error(
            "Request timed out (>%d seconds) for URL: %s", _REQUEST_TIMEOUT_SECONDS, url
        )
    return None


@app.cli.command("scrape")
def scrape() -> None:  # noqa: D103
    app.logger.info(_request_json(_Endpoint.CATALOG))
