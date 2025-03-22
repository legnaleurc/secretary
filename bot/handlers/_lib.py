import plistlib
from asyncio import as_completed
from collections.abc import AsyncIterator
from logging import getLogger
from typing import Any
from urllib.parse import (
    SplitResult,
    parse_qs,
    urlsplit,
    urlunsplit,
)

from aiohttp import ClientSession

from bot.text.types import Answer, Solver


_SHORTEN_URL_HOSTS = {"t.co"}
_REDIRECT_URL_HOSTS = {
    "al.dmm.co.jp": "lurl",
    "rcv.idx.dmm.com": "lurl",
}
_DMM_URL_HOSTS = {
    "www.dmm.co.jp",
    "book.dmm.co.jp",
}


_L = getLogger(__name__)


def parse_plist(unknown_text: str) -> Any:
    try:
        return plistlib.loads(unknown_text.encode("utf-8"))
    except plistlib.InvalidFileException:
        return None
    except Exception:
        _L.exception("unexpected error in plist")
        return None


async def generate_answers(
    unknown_text: str, /, *, single_solve: Solver, multiple_solve: Solver
) -> AsyncIterator[Answer | None]:
    if answer := await multiple_solve(unknown_text):
        yield answer
        return
    lines = unknown_text.splitlines()
    normalized_lines = filter(None, (_.strip() for _ in lines))
    producers = (_get_answer(_, single_solve) for _ in normalized_lines)
    for consumer in as_completed(producers):
        yield await consumer


async def _get_answer(unknown_text: str, solve: Solver) -> Answer | None:
    unknown_text = await _normalize_if_url(unknown_text)

    try:
        answer = await solve(unknown_text)
    except Exception:
        _L.exception(f"error while solving {unknown_text}")
        return None

    if not answer:
        _L.info(f"no answer from {unknown_text}")
        return None

    return answer


async def _normalize_if_url(url: str) -> str:
    _L.debug(f"normalizing: {url}")
    try:
        parts = urlsplit(url)
    except ValueError:
        # not a url
        return url

    match parts.hostname:
        case host if host in _SHORTEN_URL_HOSTS:
            url = await _fetch_3xx(url)
        case host if host in _REDIRECT_URL_HOSTS:
            key = _REDIRECT_URL_HOSTS[host]
            url = _get_url_from_query(parts.query, key)
        case host if host in _DMM_URL_HOSTS:
            return _strip_dmm(parts)
        case _:
            return url

    return await _normalize_if_url(url)


async def _fetch_3xx(url: str) -> str:
    async with ClientSession() as session, session.head(url) as response:
        response.raise_for_status()
        location = response.headers["Location"]
        return location


def _get_url_from_query(query: str, key: str) -> str:
    queries = parse_qs(query)
    value = queries[key]
    return value[-1]


def _strip_dmm(parts: SplitResult) -> str:
    parts = parts._replace(query="", fragment="")
    url = urlunsplit(parts)
    return url
