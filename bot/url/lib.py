from urllib.parse import quote_plus

from aiohttp import ClientSession
from telegram import InlineKeyboardMarkup, InlineKeyboardButton


async def get_json(url: str, *, query: dict[str, str] | None):
    async with ClientSession() as session:
        async with session.get(
            url,
            params=query,
        ) as response:
            response.raise_for_status()
            return await response.json()


def make_keyboard(av_id: str) -> InlineKeyboardMarkup:
    quoted = quote_plus(av_id)
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "nyaa", url=f"https://sukebei.nyaa.si/?f=0&c=2_0&q={quoted}"
                ),
                InlineKeyboardButton(
                    "jav", url=f"https://jav-torrent.org/search?keyword={quoted}"
                ),
                InlineKeyboardButton(
                    "bee", url=f"https://javbee.me/search?keyword={quoted}"
                ),
            ],
        ]
    )
