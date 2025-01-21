from urllib.parse import quote_plus

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

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
