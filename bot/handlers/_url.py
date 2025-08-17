import re
from collections.abc import Awaitable, Callable, Set
from functools import partial
from logging import getLogger
from pathlib import PurePath
from urllib.parse import SplitResult, parse_qs, urlencode, urlsplit, urlunsplit

from aiohttp import ClientSession

from bot.fetch import get_html, get_json


type _Pack = tuple[str, SplitResult]
type _UrlResolver = Callable[[_Pack], Awaitable[_Pack]]


_L = getLogger(__name__)


def _from_url(url: str) -> _Pack:
    parsed = urlsplit(url)
    return url, parsed


def _from_parsed(parsed: SplitResult) -> _Pack:
    url = urlunsplit(parsed)
    return url, parsed


async def _fetch_3xx(pack: _Pack) -> _Pack:
    url = pack[0]
    async with ClientSession() as session, session.head(url) as response:
        response.raise_for_status()
        location = response.headers["Location"]
    return _from_url(location)


async def _get_url_from_query(pack: _Pack, *, key: str) -> _Pack:
    parsed = pack[1]
    queries = parse_qs(parsed.query)
    value = queries[key]
    last = value[-1]
    return _from_url(last)


async def _parse_refresh(pack: _Pack) -> _Pack:
    url = pack[0]
    html = await get_html(url)
    meta = html.select_one("meta[http-equiv='refresh']")
    if not meta:
        raise ValueError("no meta tag")
    content = meta.get("content")
    if not content or not isinstance(content, str):
        raise ValueError("no content in meta tag")

    match = re.match(r"\d+\s*;\s*url=(.+)", content, re.I)
    if not match:
        raise ValueError("no match in content")
    url = match.group(1)
    if not url:
        raise ValueError("no url in match")
    return _from_url(url)


async def _strip_query(pack: _Pack, *, allowed_keys: Set[str]) -> _Pack:
    parsed = pack[1]
    queries = parse_qs(parsed.query)
    queries = {key: value for key, value in queries.items() if key in allowed_keys}
    query = urlencode(queries, doseq=True)
    parsed = parsed._replace(query=query)
    return _from_parsed(parsed)


async def _handle_addmm(pack: _Pack) -> _Pack:
    parsed = pack[1]
    path = PurePath(parsed.path)
    if path.parts[0:2] != ("/", "short"):
        raise ValueError("unknown path pattern")
    hash_ = path.parts[2]
    api_url = urlunsplit((parsed.scheme, parsed.netloc, "/api/proxy", "", ""))

    data = await get_json(api_url, queries={"id": hash_})
    url: str = data["url"]
    return _from_url(url)


_HOST_TO_URL_RESOLVER: dict[str, _UrlResolver] = {
    "t.co": _fetch_3xx,
    "tinyurl.com": _fetch_3xx,
    "bit.ly": _fetch_3xx,
    "dlsharing.com": _fetch_3xx,
    "adserver.assistads.net": _fetch_3xx,
    "tr.adplushome.com": _fetch_3xx,
    "ap.octopuspop.com": _fetch_3xx,
    "cloud.xaid.jp": _fetch_3xx,
    "al.dmm.co.jp": partial(_get_url_from_query, key="lurl"),
    "rcv.idx.dmm.com": partial(_get_url_from_query, key="lurl"),
    "b-short.link": _parse_refresh,
    "momentary.link": _parse_refresh,
    "min-link.com": _parse_refresh,
    "to-link.click": _parse_refresh,
    "ad-dmm.net": _handle_addmm,
    "ad-dmm.com": _handle_addmm,
    "dmm-ad.com": _handle_addmm,
    "live-gx.cc": _handle_addmm,
    "live-kq.cc": _handle_addmm,
    "short-net.org": _handle_addmm,
    "www.dmm.co.jp": partial(_strip_query, allowed_keys=set()),
    "book.dmm.co.jp": partial(_strip_query, allowed_keys=set()),
    "video.dmm.co.jp": partial(_strip_query, allowed_keys={"id"}),
    "www.dlsite.com": partial(_strip_query, allowed_keys=set()),
}


async def maybe_resolve_url(url: str) -> str:
    """
    Resolve a URL using hostname-specific handlers.
    1. If the input is not a valid URL, return it as is.
    2. If a handler exists for the hostname, call it and get the result URL.
    3. If the result URL's hostname is _TERMINAL_HOSTS, return it.
    4. Otherwise, repeat from step 2 with the new URL.
    """
    _L.debug(f"(resolving) {url}")
    try:
        url, parsed = _from_url(url)
    except ValueError:
        _L.debug(f"not a url")
        return url

    while True:
        hostname = parsed.hostname
        if not hostname:
            _L.debug(f"not a url")
            return url

        try:
            resolver = _HOST_TO_URL_RESOLVER[hostname]
        except KeyError:
            _L.debug(f"no resolver for {hostname}")
            return url

        next_url, next_parsed = await resolver((url, parsed))

        # If the URL did not change, stop to avoid infinite loop.
        if next_url == url:
            _L.debug(f"(resolved) {next_url}")
            return next_url

        # Continue resolving with the new URL parts.
        url, parsed = next_url, next_parsed
        _L.debug(f"(resolving) {url}")
