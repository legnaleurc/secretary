from collections.abc import Awaitable, Callable, Iterator
from logging import getLogger
from urllib.parse import quote_plus

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions


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


def make_av_keyboard(
    av_id: str, *, dvd_origin: str, alt_link: dict[str, str] | None = None
) -> InlineKeyboardMarkup:
    quoted = quote_plus(av_id)
    return InlineKeyboardMarkup(
        [
            _make_dvd_row(dvd_origin, quoted),
            [
                InlineKeyboardButton(
                    "nyaa", url=f"https://sukebei.nyaa.si/?f=0&c=2_0&q={quoted}"
                ),
                InlineKeyboardButton(
                    "bee", url=f"https://javbee.vip/search?keyword={quoted}"
                ),
            ],
            _make_alt_row(alt_link),
        ]
    )


def make_book_keyboard(author: str, *, dvd_origin: str) -> InlineKeyboardMarkup:
    quoted = quote_plus(author)
    return InlineKeyboardMarkup(
        [
            _make_dvd_row(dvd_origin, quoted),
            [
                InlineKeyboardButton(
                    "nyaa", url=f"https://sukebei.nyaa.si/?f=0&c=1_0&q={quoted}"
                ),
            ],
        ]
    )


def make_torrent_keyboard(torrent_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("torrent", url=torrent_url),
            ]
        ]
    )


def make_save_keyboard(url: str, name: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "save", callback_data={"type": "save_url", "url": url, "name": name}
                )
            ],
        ]
    )


def _make_dvd_row(dvd_origin: str, quoted: str) -> list[InlineKeyboardButton]:
    return [InlineKeyboardButton("dvd", url=f"{dvd_origin}/search?name={quoted}")]


def _make_alt_row(alt_link: dict[str, str] | None) -> list[InlineKeyboardButton]:
    if not alt_link:
        return []
    return [InlineKeyboardButton(k, url=v) for k, v in alt_link.items()]


def make_link_preview(url: str) -> LinkPreviewOptions:
    return LinkPreviewOptions(is_disabled=False, url=url)
