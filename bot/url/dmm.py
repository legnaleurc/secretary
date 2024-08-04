import re
from collections.abc import Iterable
from pathlib import PurePath
from urllib.parse import SplitResult

from bot.context import DvdList
from bot.lib import get_json, get_html, make_av_keyboard, make_book_keyboard
from bot.types import AnswerDict


_VIDEO_CATEGORIES: set[tuple[str, str]] = {
    ("digital", "videoa"),
    ("digital", "videoc"),
    ("mono", "dvd"),
}
_DOUJIN_CATEGORIES: set[tuple[str, str]] = {
    ("dc", "doujin"),
}


async def parse_dmm(
    *, url: str, parsed_url: SplitResult, dvd_list: DvdList
) -> AnswerDict | None:
    rv = _find_av_id(url=url, parsed_url=parsed_url)
    if rv:
        return {
            "text": rv,
            "keyboard": make_av_keyboard(rv, dvd_list=dvd_list),
        }

    rv = await _find_doujin_author(url=url, parsed_url=parsed_url)
    if rv:
        return {
            "text": rv,
            "keyboard": make_book_keyboard(rv, dvd_list=dvd_list),
        }

    rv = await _find_book_author(url=url, parsed_url=parsed_url)
    if rv:
        return {
            "text": rv,
            "keyboard": make_book_keyboard(rv, dvd_list=dvd_list),
        }

    return None


def _find_av_id(*, url: str, parsed_url: SplitResult) -> str:
    if parsed_url.hostname != "www.dmm.co.jp":
        return ""

    path = PurePath(parsed_url.path)
    category = (path.parts[1], path.parts[2])
    if category not in _VIDEO_CATEGORIES:
        return ""

    return _find_id_from_path(path.parts)


async def _find_doujin_author(*, url: str, parsed_url: SplitResult) -> str:
    if parsed_url.hostname != "www.dmm.co.jp":
        return ""

    path = PurePath(parsed_url.path)
    category = (path.parts[1], path.parts[2])
    if category not in _DOUJIN_CATEGORIES:
        return ""

    try:
        html = await get_html(
            url,
            cookies={
                "age_check_done": "1",
            },
        )
    except Exception:
        return ""

    anchor = html.select_one(".circleName__txt")
    if not anchor:
        return ""
    author = anchor.text.strip()
    return author


async def _find_book_author(*, url: str, parsed_url: SplitResult) -> str:
    if parsed_url.hostname != "book.dmm.co.jp":
        return ""

    path = PurePath(parsed_url.path)
    if path.parts[1] != "product":
        return ""

    book_id = path.parts[3]

    try:
        data = await get_json(
            "https://book.dmm.co.jp/ajax/bff/content/",
            query={
                "shop_name": "adult",
                "content_id": book_id,
            },
        )
    except Exception:
        return ""

    name_list: list[str] = [_["name"] for _ in data["author"]]
    name_list = [_ for _ in name_list if not _.endswith("編集部")]
    name = " ".join(name_list)
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
