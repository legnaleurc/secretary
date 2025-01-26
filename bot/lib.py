from collections.abc import Callable
from urllib.parse import (
    SplitResult,
    parse_qs,
    quote_plus,
    urlencode,
    urlsplit,
    urlunsplit,
)

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.context import DvdList


async def get_json(url: str, *, query: dict[str, str] | None = None):
    async with ClientSession() as session:
        async with session.get(
            url,
            params=query,
        ) as response:
            response.raise_for_status()
            return await response.json()


async def get_html(
    url: str,
    *,
    query: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
) -> BeautifulSoup:
    async with ClientSession() as session:
        async with session.get(
            url,
            params=query,
            cookies=cookies,
        ) as response:
            response.raise_for_status()
            text = await response.text(errors="ignore")
            return BeautifulSoup(text, "html.parser")


_SHORTEN_URL_HOSTS = {"t.co"}
_REDIRECT_URL_HOSTS = {
    "al.dmm.co.jp": "lurl",
    "rcv.idx.dmm.com": "lurl",
}
_DMM_URL_HOSTS = {
    "www.dmm.co.jp",
    "book.dmm.co.jp",
}


async def strip_url_trackers(url: str) -> str:
    try:
        parts = urlsplit(url)
    except Exception:
        # not a url
        return url

    match parts.hostname:
        case host if host in _SHORTEN_URL_HOSTS:
            url = await _fetch_redirection(url)
        case host if host in _REDIRECT_URL_HOSTS:
            key = _REDIRECT_URL_HOSTS[host]
            url = _get_url_from_query(parts.query, key)
        case host if host in _DMM_URL_HOSTS:
            return _strip_trackers(
                parts, condition=lambda key: not key.startswith("utm_")
            )
        case _:
            return url

    return await strip_url_trackers(url)


async def _fetch_redirection(url: str) -> str:
    async with ClientSession() as session, session.head(url) as response:
        response.raise_for_status()
        location = response.headers["Location"]
        return location


def _get_url_from_query(query: str, key: str) -> str:
    queries = parse_qs(query)
    value = queries[key]
    return value[-1]


def _strip_trackers(parts: SplitResult, *, condition: Callable[[str], bool]) -> str:
    queries = parse_qs(parts.query)
    filtered = [(key, value) for key, value in queries.items() if condition(key)]
    query = urlencode(filtered)

    parts = parts._replace(query=query)
    url = urlunsplit(parts)
    return url


def make_av_keyboard(av_id: str, *, dvd_list: DvdList) -> InlineKeyboardMarkup:
    quoted = quote_plus(av_id)
    return InlineKeyboardMarkup(
        [
            _make_dvd_row(dvd_list, quoted),
            [
                InlineKeyboardButton(
                    "nyaa", url=f"https://sukebei.nyaa.si/?f=0&c=2_0&q={quoted}"
                ),
                InlineKeyboardButton(
                    "bee", url=f"https://javbee.me/search?keyword={quoted}"
                ),
            ],
        ]
    )


def make_book_keyboard(author: str, *, dvd_list: DvdList) -> InlineKeyboardMarkup:
    quoted = quote_plus(author)
    return InlineKeyboardMarkup(
        [
            _make_dvd_row(dvd_list, quoted),
            [
                InlineKeyboardButton(
                    "nyaa", url=f"https://sukebei.nyaa.si/?f=0&c=1_0&q={quoted}"
                ),
            ],
        ]
    )


def _make_dvd_row(dvd_list: DvdList, quoted: str) -> list[InlineKeyboardButton]:
    return [
        InlineKeyboardButton(_[0], url=f"{_[1]}/search?name={quoted}") for _ in dvd_list
    ]
