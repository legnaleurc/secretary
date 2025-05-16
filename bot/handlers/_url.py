import re
from collections.abc import Awaitable, Callable
from functools import partial
from logging import getLogger
from urllib.parse import SplitResult, parse_qs, urlsplit, urlunsplit

from aiohttp import ClientSession

from bot.fetch import get_html


type _UrlResolver = Callable[[str, SplitResult], Awaitable[str]]


_L = getLogger(__name__)


async def _fetch_3xx(url: str, parts: SplitResult) -> str:
    async with ClientSession() as session, session.head(url) as response:
        response.raise_for_status()
        location = response.headers["Location"]
        return location


async def _get_url_from_query(url: str, parts: SplitResult, *, key: str) -> str:
    queries = parse_qs(parts.query)
    value = queries[key]
    return value[-1]


async def _parse_bshortlink_url(url: str, parts: SplitResult) -> str:
    html = await get_html(url)
    meta = html.select_one("meta[http-equiv='refresh']")
    if not meta:
        raise ValueError("no meta tag")
    content = meta.get("content")
    if not content or not isinstance(content, str):
        raise ValueError("no content in meta tag")

    match = re.match(r"0;\s*url=(.+)", content, re.I)
    if not match:
        raise ValueError("no match in content")
    url = match.group(1)
    if not url:
        raise ValueError("no url in match")
    return url


async def _strip_all_queries(url: str, parts: SplitResult) -> str:
    parts = parts._replace(query="", fragment="")
    url = urlunsplit(parts)
    return url


_HOST_TO_URL_RESOLVER: dict[str, _UrlResolver] = {
    "t.co": _fetch_3xx,
    "tinyurl.com": _fetch_3xx,
    "al.dmm.co.jp": partial(_get_url_from_query, key="lurl"),
    "rcv.idx.dmm.com": partial(_get_url_from_query, key="lurl"),
    "b-short.link": _parse_bshortlink_url,
    "www.dmm.co.jp": _strip_all_queries,
    "book.dmm.co.jp": _strip_all_queries,
}
_TERMINAL_HOSTS = {
    "www.dmm.co.jp",
    "book.dmm.co.jp",
}


async def maybe_resolve_url(url: str) -> str:
    _L.debug(f"(resolving) {url}")
    try:
        parts = urlsplit(url)
    except ValueError:
        # not a url
        return url

    if not parts.hostname:
        # no hostname
        return url

    resolver = _HOST_TO_URL_RESOLVER.get(parts.hostname)
    if not resolver:
        # no resolver
        return url

    url = await resolver(url, parts)
    if parts.hostname in _TERMINAL_HOSTS:
        # no need to resolve again
        return url

    return await maybe_resolve_url(url)
