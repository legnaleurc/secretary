import re
from base64 import urlsafe_b64decode
from collections.abc import Awaitable, Callable, Set
from functools import partial, wraps
from logging import getLogger
from pathlib import PurePath
from typing import NamedTuple
from urllib.parse import SplitResult, parse_qs, unquote, urlencode, urlsplit, urlunsplit

from aiohttp import ClientSession

from bot.lib.fetch.aio import get_html, get_json


_L = getLogger(__name__)


class _Pack(NamedTuple):
    url: str
    parsed: SplitResult


type _UrlResolver = Callable[[_Pack], Awaitable[_Pack]]


def fallback(
    primary: _UrlResolver, secondary: _UrlResolver, *, on: tuple[type[Exception], ...]
) -> _UrlResolver:
    async def combined(pack: _Pack) -> _Pack:
        try:
            return await primary(pack)
        except on:
            return await secondary(pack)

    return combined


def pipe(*resolvers: _UrlResolver) -> _UrlResolver:
    async def combined(pack: _Pack) -> _Pack:
        for resolver in resolvers:
            pack = await resolver(pack)
        return pack

    return combined


def _from_url(url: str) -> _Pack:
    parsed = urlsplit(url)
    return _Pack(url, parsed)


def _from_parsed(parsed: SplitResult) -> _Pack:
    url = urlunsplit(parsed)
    return _Pack(url, parsed)


async def _fetch_3xx(pack: _Pack) -> _Pack:
    async with ClientSession() as session, session.head(pack.url) as response:
        response.raise_for_status()
        location = response.headers["Location"]
    return _from_url(location)


async def _get_url_from_query(pack: _Pack, *, key: str) -> _Pack:
    queries = parse_qs(pack.parsed.query)
    value = queries[key]
    last = value[-1]
    return _from_url(last)


async def _get_raw_from_query(pack: _Pack, *, key: str) -> _Pack:
    queries = parse_qs(pack.parsed.query)
    value = queries[key]
    last = value[-1]
    return _Pack(last, urlsplit(last))


async def _strip_url_quotes(pack: _Pack) -> _Pack:
    url = pack.url
    if url.startswith("'") and url.endswith("'"):
        url = url[1:-1]
    return _Pack(url, urlsplit(url))


async def _decode_base64_url(pack: _Pack) -> _Pack:
    url = urlsafe_b64decode(pack.url).decode("utf-8")
    return _from_url(url)


async def _replace_host(pack: _Pack, *, host: str) -> _Pack:
    parsed = pack.parsed._replace(netloc=host)
    return _from_parsed(parsed)


async def _replace_path(pack: _Pack, *, path: str) -> _Pack:
    parsed = pack.parsed._replace(path=path)
    return _from_parsed(parsed)


async def _parse_refresh(pack: _Pack) -> _Pack:
    html = await get_html(pack.url)
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
    queries = parse_qs(pack.parsed.query)
    queries = {key: value for key, value in queries.items() if key in allowed_keys}
    query = urlencode(queries, doseq=True)
    parsed = pack.parsed._replace(query=query)
    return _from_parsed(parsed)


async def _handle_addmm(pack: _Pack) -> _Pack:
    path = PurePath(pack.parsed.path)
    if path.parts[0:2] != ("/", "short"):
        raise ValueError("unknown path pattern")
    hash_ = path.parts[2]
    api_url = urlunsplit((pack.parsed.scheme, pack.parsed.netloc, "/api/proxy", "", ""))

    data = await get_json(api_url, queries={"id": hash_})
    url: str = data["url"]
    return _from_url(url)


async def _handle_dmm(pack: _Pack, *, allowed_keys: Set[str]) -> _Pack:
    if pack.parsed.hostname == "dmm.co.jp":
        new_parsed = pack.parsed._replace(netloc="www.dmm.co.jp")
        pack = _from_parsed(new_parsed)

    path = PurePath(pack.parsed.path)

    if path.parts[0:3] == ("/", "age_check", "="):
        return await _handle_dmm_age_check(pack)

    if path.parts[0:4] == ("/", "en", "age_check", "="):
        return await _handle_dmm_age_check(pack)

    return await _strip_query(pack, allowed_keys=allowed_keys)


async def _handle_dmm_age_check(pack: _Pack) -> _Pack:
    next_pack = await _get_url_from_query(pack, key="rurl")
    if next_pack.parsed.scheme:
        return next_pack

    # rurl is a hash
    html = await get_html(pack.url)
    anchor = html.select_one("div.turtle-component > a")
    if not anchor:
        raise ValueError("no anchor tag found")
    href = anchor.get("href")
    if not href or not isinstance(href, str):
        raise ValueError("no href in anchor tag")
    return _from_url(href)


async def _handle_dmm_login(pack: _Pack) -> _Pack:
    path = PurePath(pack.parsed.path)

    if path.parts[0:5] != ("/", "service", "login", "password", "="):
        raise ValueError("unknown path pattern")

    queries = path.parts[5]
    queries = parse_qs(queries)
    maybe_url = queries.get("path", [])
    if not maybe_url:
        raise ValueError("no path query parameter")
    maybe_url = maybe_url[-1]
    if not maybe_url:
        raise ValueError("empty path query parameter")

    next_pack = _from_url(maybe_url)
    if next_pack.parsed.scheme:
        return next_pack

    # path is a hash
    return _from_url(f"https://www.dmm.co.jp/age_check/=/?rurl={maybe_url}")


async def _extract_dlsite_url_path(pack: _Pack) -> _Pack:
    path = PurePath(pack.parsed.path)
    # May raise ValueError for invalid url.
    url_index = path.parts.index("url")
    # May raise IndexError for invalid url.
    url_part = path.parts[url_index + 1]
    url_part = unquote(url_part)
    return _from_url(url_part)


_handle_dlsharing = fallback(
    _extract_dlsite_url_path,
    partial(_replace_host, host="www.dlsite.com"),
    on=(ValueError, IndexError),
)


def _dlsite_no_touch(fn: _UrlResolver) -> _UrlResolver:
    @wraps(fn)
    async def wrapped(pack: _Pack) -> _Pack:
        new_pack = await fn(pack)
        path = PurePath(new_pack.parsed.path)
        if not path.parts[1].endswith("-touch"):
            return new_pack

        parts_list = list(path.parts)
        parts_list[1] = parts_list[1][:-6]
        path = PurePath(*parts_list)
        return await _replace_path(new_pack, path=str(path))

    return wrapped


async def _handle_dlsite_inner(pack: _Pack) -> _Pack:
    # maybe dlaf
    path = PurePath(pack.parsed.path)
    if "dlaf" in path.parts:
        return await _parse_refresh(pack)
    return await _strip_query(pack, allowed_keys=set())


_handle_dlsite = _dlsite_no_touch(
    fallback(
        _extract_dlsite_url_path, _handle_dlsite_inner, on=(ValueError, IndexError)
    )
)


async def _parse_script_1(pack: _Pack) -> _Pack:
    html = await get_html(pack.url)
    scripts = html.find_all("script")
    if not scripts:
        raise ValueError("no script")
    script = scripts[-1].get_text()
    matched = re.search(r"\\\"(http.+)\\\"", script)
    if not matched:
        raise ValueError("url not found")
    url = matched.group(1)
    # escape \u0026
    url = url.encode().decode("unicode-escape")
    return _from_url(url)


_HOST_TO_URL_RESOLVER: dict[str, _UrlResolver] = {
    "t.co": _fetch_3xx,
    "x.gd": _fetch_3xx,
    "tinyurl.com": _fetch_3xx,
    "bit.ly": _fetch_3xx,
    "dlsharing.com": _handle_dlsharing,
    "dlaf.jp": partial(_replace_host, host="www.dlsite.com"),
    "adserver.assistads.net": _fetch_3xx,
    "tr.adplushome.com": _fetch_3xx,
    "ap.octopuspop.com": _fetch_3xx,
    "cloud.xaid.jp": _fetch_3xx,
    "al.fanza.co.jp": partial(_get_url_from_query, key="lurl"),
    "al.dmm.co.jp": partial(_get_url_from_query, key="lurl"),
    "al.mm.co.jp": partial(_get_url_from_query, key="lurl"),
    "al.dmm.com": partial(_get_url_from_query, key="lurl"),
    "rcv.idx.dmm.com": partial(_get_url_from_query, key="lurl"),
    "rcv.ixd.dmm.com": partial(_get_url_from_query, key="lurl"),
    "rcv.ixd.dmm.co.jp": partial(_get_url_from_query, key="lurl"),
    "lp.ixd.dmm.com": partial(_get_url_from_query, key="lpurl"),
    "ip.affiliate.dmm.com": pipe(
        partial(_get_raw_from_query, key="lurl"), _strip_url_quotes, _decode_base64_url
    ),
    "numa2.com": pipe(partial(_get_raw_from_query, key="u"), _decode_base64_url),
    "b-short.link": _parse_refresh,
    "momentary.link": _parse_refresh,
    "min-link.com": _parse_refresh,
    "to-link.click": _parse_refresh,
    "live-dh.cc": _parse_script_1,
    "ad-dmm.net": _handle_addmm,
    "ad-dmm.com": _handle_addmm,
    "dmm-ad.com": _handle_addmm,
    "live-gx.cc": _handle_addmm,
    "live-kq.cc": _handle_addmm,
    "short-net.org": _handle_addmm,
    "dmm.co.jp": partial(_handle_dmm, allowed_keys=set()),
    "www.dmm.co.jp": partial(_handle_dmm, allowed_keys=set()),
    "book.dmm.co.jp": partial(_handle_dmm, allowed_keys=set()),
    "video.dmm.co.jp": partial(_handle_dmm, allowed_keys={"id"}),
    "accounts.dmm.co.jp": _handle_dmm_login,
    "www.dlsite.com": _handle_dlsite,
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
        pack = _from_url(url)
    except ValueError:
        _L.debug(f"not a url")
        return url

    while True:
        hostname = pack.parsed.hostname
        if not hostname:
            _L.debug(f"not a url")
            return pack.url

        try:
            resolver = _HOST_TO_URL_RESOLVER[hostname]
        except KeyError:
            _L.debug(f"no resolver for {hostname}")
            return pack.url

        next_pack = await resolver(pack)

        # If the URL did not change, stop to avoid infinite loop.
        if next_pack.url == pack.url:
            _L.debug(f"(resolved) {next_pack.url}")
            return next_pack.url

        # Continue resolving with the new URL parts.
        pack = next_pack
        _L.debug(f"(resolving) {pack.url}")
