from urllib.parse import quote_plus

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from bot.context import DvdList


def make_av_keyboard(av_id: str, *, dvd_list: DvdList) -> InlineKeyboardMarkup:
    quoted = quote_plus(av_id)
    return InlineKeyboardMarkup(
        [
            make_dvd_row(dvd_list, quoted),
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


def make_book_keyboard(author: str, *, dvd_list: DvdList) -> InlineKeyboardMarkup:
    quoted = quote_plus(author)
    return InlineKeyboardMarkup([make_dvd_row(dvd_list, quoted)])


def make_dvd_row(dvd_list: DvdList, quoted: str) -> list[InlineKeyboardButton]:
    return [
        InlineKeyboardButton(_[0], url=f"{_[1]}/search?name={quoted}") for _ in dvd_list
    ]
