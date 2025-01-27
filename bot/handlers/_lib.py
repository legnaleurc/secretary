from logging import getLogger
from urllib.parse import (
    SplitResult,
    parse_qs,
    urlsplit,
    urlunsplit,
)

from aiohttp import ClientSession


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


async def normalize_if_url(url: str) -> str:
    _L.debug(f"resolving: {url}")
    try:
        parts = urlsplit(url)
    except ValueError:
        # not a url
        return url

    match parts.hostname:
        case host if host in _SHORTEN_URL_HOSTS:
            url = await _fetch_redirection(url)
        case host if host in _REDIRECT_URL_HOSTS:
            key = _REDIRECT_URL_HOSTS[host]
            url = _get_url_from_query(parts.query, key)
        case host if host in _DMM_URL_HOSTS:
            return _strip_dmm(parts)
        case _:
            return url

    return await normalize_if_url(url)


async def _fetch_redirection(url: str) -> str:
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
