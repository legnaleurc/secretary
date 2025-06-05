import re
from collections.abc import Awaitable, Callable
from functools import partial
from logging import getLogger
from urllib.parse import SplitResult, parse_qs, urlsplit, urlunsplit

from aiohttp import ClientSession

from bot.fetch import get_html


type _UrlResolver = Callable[[SplitResult], Awaitable[SplitResult]]


_L = getLogger(__name__)


async def _fetch_3xx(parts: SplitResult) -> SplitResult:
    url = urlunsplit(parts)
    async with ClientSession() as session, session.head(url) as response:
        response.raise_for_status()
        location = response.headers["Location"]
    return urlsplit(location)


async def _get_url_from_query(parts: SplitResult, *, key: str) -> SplitResult:
    queries = parse_qs(parts.query)
    value = queries[key]
    last = value[-1]
    return urlsplit(last)


async def _parse_bshortlink_url(parts: SplitResult) -> SplitResult:
    url = urlunsplit(parts)
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
    return urlsplit(url)


async def _strip_all_queries(parts: SplitResult) -> SplitResult:
    return parts._replace(query="", fragment="")


_HOST_TO_URL_RESOLVER: dict[str, _UrlResolver] = {
    "t.co": _fetch_3xx,
    "tinyurl.com": _fetch_3xx,
    "dlsharing.com": _fetch_3xx,
    "al.dmm.co.jp": partial(_get_url_from_query, key="lurl"),
    "rcv.idx.dmm.com": partial(_get_url_from_query, key="lurl"),
    "b-short.link": _parse_bshortlink_url,
    "www.dmm.co.jp": _strip_all_queries,
    "book.dmm.co.jp": _strip_all_queries,
}


async def maybe_resolve_url(url: str) -> str:
    _L.debug(f"(resolving) {url}")
    try:
        parts = urlsplit(url)
    except ValueError:
        _L.debug(f"not a url")
        return url

    if not parts.hostname:
        _L.debug(f"not a url")
        return url

    parts = await _resolve_url(parts)
    url = urlunsplit(parts)
    _L.debug(f"(resolved) {url}")
    return url


async def _resolve_url(parts: SplitResult) -> SplitResult:
    if not parts.hostname:
        raise ValueError("no hostname")

    resolver = _HOST_TO_URL_RESOLVER.get(parts.hostname)
    if not resolver:
        _L.debug(f"no resolver for {parts.hostname}")
        return parts

    next_parts = await resolver(parts)
    if next_parts.hostname == parts.hostname:
        # no change
        return next_parts

    _L.debug(f"(routing) {urlunsplit(parts)} -> {urlunsplit(next_parts)}")
    return await _resolve_url(next_parts)
