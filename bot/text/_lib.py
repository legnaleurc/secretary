from collections.abc import Awaitable, Callable, Iterator
from contextlib import asynccontextmanager
from logging import getLogger
from urllib.parse import quote_plus

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions

from bot.context import DvdList


_L = getLogger(__name__)


async def first_not_none[R](
    callbacks: Iterator[Callable[[], Awaitable[R | None]]],
) -> R | None:
    for cb in callbacks:
        try:
            rv = await cb()
            if rv is not None:
                return rv
        except Exception:
            _L.exception("error in loop")
    return None


async def get_json(url: str, *, queries: dict[str, str] | None = None):
    async with _http_get(url, queries=queries) as response:
        return await response.json()


async def get_html(url: str, *, cookies: dict[str, str] | None = None) -> BeautifulSoup:
    async with _http_get(url, cookies=cookies) as response:
        text = await response.text(errors="ignore")
        return BeautifulSoup(text, "html.parser")


@asynccontextmanager
async def _http_get(
    url: str,
    *,
    queries: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
):
    async with (
        ClientSession() as session,
        session.get(
            url,
            params=queries,
            cookies=cookies,
        ) as response,
    ):
        response.raise_for_status()
        yield response


def make_av_keyboard(
    av_id: str, *, dvd_list: DvdList, alt_link: dict[str, str] | None = None
) -> InlineKeyboardMarkup:
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
            _make_alt_row(alt_link),
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


def _make_alt_row(alt_link: dict[str, str] | None) -> list[InlineKeyboardButton]:
    if not alt_link:
        return []
    return [InlineKeyboardButton(k, url=v) for k, v in alt_link.items()]


def make_link_preview(url: str) -> LinkPreviewOptions:
    return LinkPreviewOptions(is_disabled=False, url=url)
