import contextlib
import enum
import re
import typing

import redis
import requests

from . import app

_REQUEST_TIMEOUT_SECONDS: typing.Final = 10

_redis_session = redis.Redis()


class _Endpoint(enum.StrEnum):
    CATALOG = "https://a.4cdn.org/vg/catalog.json"
    ARCHIVE = "https://a.4cdn.org/vg/archive.json"
    THREAD = "https://a.4cdn.org/vg/thread/%d.json"
    MEDIA = "https://i.4cdn.org/vg/%d%s"


class _RedisKey(enum.StrEnum):
    ARCHIVE = enum.auto()


class _Post(typing.TypedDict):
    no: int
    sub: typing.NotRequired[str]


class _Thread(typing.TypedDict):
    posts: list[_Post]


class _Page(typing.TypedDict):
    threads: list[_Post]


def _is_post_list(posts: object) -> typing.TypeGuard[list[_Post]]:
    return isinstance(posts, list) and all(
        isinstance(post, dict)
        and post.keys()
        >= (
            _Post.__required_keys__
            if i > 0
            else _Post.__required_keys__ | _Post.__optional_keys__
        )
        for i, post in enumerate(posts)
    )


def _is_catalog(catalog: object) -> typing.TypeGuard[list[_Page]]:
    return isinstance(catalog, list) and all(
        isinstance(page, dict) and _is_post_list(page.get("threads"))
        for page in catalog
    )


def _is_archive(archive: object) -> typing.TypeGuard[list[int]]:
    return isinstance(archive, list) and all(
        isinstance(thread_id, int) for thread_id in archive
    )


def _is_thread(thread: object) -> typing.TypeGuard[_Thread]:
    return isinstance(thread, dict) and _is_post_list(thread.get("posts"))


def _post_has_subject(post: _Post, subject: str) -> bool:
    return bool(
        subject
        and re.search(
            rf"\b{re.escape(subject.casefold())}\b",
            post["sub"].casefold(),
        )
    )


def _request_json(endpoint: _Endpoint | str) -> object:
    try:
        return typing.cast(
            object, requests.get(endpoint, timeout=_REQUEST_TIMEOUT_SECONDS).json()
        )
    except requests.RequestException as e:
        app.logger.error("Request failed for %s: %r", endpoint, e)

    return None


def _request_thread_ids(subject: str) -> list[int]:
    thread_ids = []
    catalog = _request_json(_Endpoint.CATALOG)
    archive = _request_json(_Endpoint.ARCHIVE)

    if _is_catalog(catalog):
        thread_ids += [
            post["no"]
            for page in catalog
            for post in page["threads"]
            if _post_has_subject(post, subject)
        ]

    if _is_archive(archive):
        try:
            _redis_session.ping()
        except redis.RedisError as e:
            app.logger.error("Redis server unavailable: %r", e)

        with contextlib.suppress(redis.RedisError):
            for thread_id in map(int, _redis_session.scan_iter()):
                if thread_id in archive:
                    archive.remove(thread_id)
                else:
                    _redis_session.delete(str(thread_id))

        for thread_id in archive:
            thread = _request_json(_Endpoint.THREAD % thread_id)

            if _is_thread(thread):
                if _post_has_subject(thread["posts"][0], subject):
                    thread_ids.append(thread_id)
            else:
                continue

            with contextlib.suppress(redis.RedisError):
                _redis_session.set(str(thread_id), "")

    return sorted(thread_ids)


@app.cli.command("scrape")
def scrape() -> None:  # noqa: D103
    app.logger.info(_request_thread_ids("agdg"))
