import re
from collections.abc import Iterable
from pathlib import PurePath
from urllib.parse import ParseResult, urlunsplit, urlencode

from aiohttp import ClientSession
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from bot._types import AnswerDict


async def parse_dmm(*, url: str, parsed_url: ParseResult) -> AnswerDict | None:
    rv = _find_av_id(url=url, parsed_url=parsed_url)
    if rv:
        return {
            "text": rv,
            "keyboard": make_keyboard(rv),
        }

    rv = await _find_book_author(url=url, parsed_url=parsed_url)
    if rv:
        return {
            "text": rv,
        }

    return None


def _find_av_id(*, url: str, parsed_url: ParseResult) -> str:
    if parsed_url.hostname != "www.dmm.co.jp":
        return ""

    path = PurePath(parsed_url.path)
    if path.parts[1] != "digital":
        return ""

    return _find_id_from_path(path.parts)


async def _find_book_author(*, url: str, parsed_url: ParseResult) -> str:
    if parsed_url.hostname != "book.dmm.co.jp":
        return ""

    path = PurePath(parsed_url.path)
    if path.parts[1] != "product":
        return ""

    book_id = path.parts[3]

    async with ClientSession() as session:
        async with session.get(
            "https://book.dmm.co.jp/ajax/bff/content/",
            params={
                "shop_name": "adult",
                "content_id": book_id,
            },
        ) as response:
            if response.status != 200:
                return ""

            data = await response.json()
        authors = data["author"]
        name_list = [_["name"] for _ in authors]
        name = ", ".join(name_list)
        return name


def _find_id_from_path(args: Iterable[str]) -> str:
    av_id = ""
    for arg in args:
        rv = re.match(r"^cid=(.+)$", arg)
        if not rv:
            continue
        av_id = rv.group(1)
        break
    else:
        return ""

    rv = re.search(r"\d*([a-z]+)0*(\d+)", av_id)
    if not rv:
        return ""

    major = rv.group(1).upper()
    minor = rv.group(2)
    return f"{major}-{minor.zfill(3)}"


def make_keyboard(av_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "nyaa",
                    url=urlunsplit(
                        (
                            "https",
                            "sukebei.nyaa.si",
                            "/",
                            urlencode(
                                {
                                    "f": "0",
                                    "c": "2_0",
                                    "q": av_id,
                                }
                            ),
                            "",
                        )
                    ),
                ),
                InlineKeyboardButton(
                    "jav",
                    url=urlunsplit(
                        (
                            "https",
                            "jav-torrent.org",
                            "/search",
                            urlencode(
                                {
                                    "keyword": av_id,
                                }
                            ),
                            "",
                        )
                    ),
                ),
                InlineKeyboardButton(
                    "bee",
                    url=urlunsplit(
                        (
                            "https",
                            "javbee.me",
                            "/search",
                            urlencode(
                                {
                                    "keyword": av_id,
                                }
                            ),
                            "",
                        )
                    ),
                ),
            ],
        ]
    )
