import contextlib
import enum
import html
import re
import typing

import redis
import requests

from . import app, common, database

_redis_client = redis.Redis()


class _Endpoint(enum.StrEnum):
    CATALOG = "https://a.4cdn.org/vg/catalog.json"
    ARCHIVE = "https://a.4cdn.org/vg/archive.json"
    THREAD = "https://a.4cdn.org/vg/thread/%d.json"
    MEDIA = "https://i.4cdn.org/vg/%d%s"


class _Post(typing.TypedDict):
    no: int
    time: int
    tim: typing.NotRequired[int]
    ext: typing.NotRequired[str]
    sub: typing.NotRequired[str]
    com: typing.NotRequired[str]


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
        "sub" in post
        and subject
        and re.search(rf"(?i)\b{re.escape(subject)}\b", post["sub"])
    )


def _normalize_comment(comment: str) -> str:
    return common.normalize_text(
        html.unescape(comment),
        [
            r"\\(\S)",
            r"<span.+?>(.+?)</span>",
            r"\s?(::):*\s?",
            r"\s?(->)\s?",
            r"\s?(<br>)\s?",
        ],
    )


def _request_json(endpoint: _Endpoint | str) -> object:
    try:
        return typing.cast(object, requests.get(endpoint, timeout=10).json())
    except requests.RequestException as e:
        app.logger.warning("Request failed for %s: %r", endpoint, e)

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
        with contextlib.suppress(redis.RedisError):
            for thread_id in map(int, _redis_client.scan_iter()):
                if thread_id in archive:
                    archive.remove(thread_id)
                else:
                    _redis_client.delete(str(thread_id))

        for thread_id in archive:
            thread = _request_json(_Endpoint.THREAD % thread_id)

            if _is_thread(thread):
                if _post_has_subject(thread["posts"][0], subject):
                    thread_ids.append(thread_id)
            else:
                continue

            with contextlib.suppress(redis.RedisError):
                _redis_client.set(str(thread_id), "")

    return sorted(thread_ids)


def _scrape_thread_id(thread_id: int) -> None:
    thread = _request_json(_Endpoint.THREAD % thread_id)

    if _is_thread(thread):
        for post in thread["posts"]:
            if not (comment := post.get("com")):
                continue

            if not (
                text_match := re.search(
                    r"::((?:(?!::|<br>).)+?)(?:::((?:(?!<br>).)+?))?::(.+$)",
                    _normalize_comment(comment),
                )
            ):
                continue

            title, title_update, text = text_match.groups()

            if game_id := database.get_game_id(
                title := title_update
                if title_update and not database.get_game_id(title_update)
                else title
            ):
                game = typing.cast(database.Game, database.get_game(game_id))
            else:
                game = database.add_game(title)

            for key, value in re.findall(
                key_pattern
                := rf"(?i)(?:<br>)+({'|'.join(common.GAME_KEYS)})::((?:(?!<br>).)+)",
                text,
            ):
                setattr(game, key, value)

            if progress_match := re.search(
                r"(?:.+::(?:.*?<br>)?)?(?:<br>)*(.+)$",
                re.split(key_pattern, text)[-1],
            ):
                database.add_post(
                    game.game_id,
                    post["time"],
                    f"{post['tim']}{post['ext']}" if "tim" in post else None,
                    progress_match.group(1),
                )

        database.commit_session()


@app.cli.command("scrape")
def scrape() -> None:  # noqa: D103
    try:
        _redis_client.ping()
    except redis.RedisError as e:
        app.logger.warning("Redis server unavailable: %r", e)

    for thread_id in _request_thread_ids("agdg"):
        _scrape_thread_id(thread_id)
