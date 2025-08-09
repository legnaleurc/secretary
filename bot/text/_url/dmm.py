import re
from collections.abc import Iterable
from pathlib import PurePath
from urllib.parse import SplitResult, parse_qs

from bot.context import DvdList
from bot.fetch import get_html, get_json

from .._lib import (
    make_av_keyboard,
    make_book_keyboard,
    make_link_preview,
)
from ..types import Answer


_VIDEO_CATEGORIES: set[tuple[str, str]] = {
    ("digital", "videoa"),
    ("digital", "videoc"),
    ("mono", "dvd"),
}
_DOUJIN_CATEGORIES: set[tuple[str, str]] = {
    ("dc", "doujin"),
}


async def solve(
    *, url: str, parsed_url: SplitResult, dvd_list: DvdList
) -> Answer | None:
    rv = _find_av_id(url=url, parsed_url=parsed_url)
    if rv:
        return Answer(
            text=rv,
            keyboard=make_av_keyboard(rv, dvd_list=dvd_list),
            link_preview=make_link_preview(url),
        )

    rv = _find_av_id_in_video(url=url, parsed_url=parsed_url)
    if rv:
        return Answer(
            text=rv,
            keyboard=make_av_keyboard(rv, dvd_list=dvd_list),
            link_preview=make_link_preview(url),
        )

    author, is_ai = await _find_doujin_author(url=url, parsed_url=parsed_url)
    if author:
        return Answer(
            text=author,
            should_delete=is_ai,
            keyboard=make_book_keyboard(author, dvd_list=dvd_list),
            link_preview=make_link_preview(url),
        )

    rv = await _find_book_author(url=url, parsed_url=parsed_url)
    if rv:
        return Answer(
            text=rv,
            keyboard=make_book_keyboard(rv, dvd_list=dvd_list),
            link_preview=make_link_preview(url),
        )

    return None


def _find_av_id(*, url: str, parsed_url: SplitResult) -> str:
    if parsed_url.hostname != "www.dmm.co.jp":
        return ""

    path = PurePath(parsed_url.path)
    category = (path.parts[1], path.parts[2])
    if category not in _VIDEO_CATEGORIES:
        return ""

    return _find_id_from_path(path.parts)


def _find_av_id_in_video(*, url: str, parsed_url: SplitResult) -> str:
    if parsed_url.hostname != "video.dmm.co.jp":
        return ""

    queries = parse_qs(parsed_url.query)
    last = queries.get("id", [""])[-1]
    return _parse_av_id(last)


async def _find_doujin_author(*, url: str, parsed_url: SplitResult) -> tuple[str, bool]:
    if parsed_url.hostname != "www.dmm.co.jp":
        return "", False

    path = PurePath(parsed_url.path)
    category = (path.parts[1], path.parts[2])
    if category not in _DOUJIN_CATEGORIES:
        return "", False

    try:
        html = await get_html(
            url,
            cookies={
                "age_check_done": "1",
            },
        )
    except Exception:
        return "", False

    anchor = html.select_one(".circleName__txt")
    if not anchor:
        return "", False
    author = anchor.text.strip()

    genre = html.select_one(".c_icon_productGenre")
    if not genre:
        return author, False

    is_ai = "AI" in genre.text

    return author, is_ai


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
            queries={
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

    return _parse_av_id(av_id)


def _parse_av_id(raw_code: str) -> str:
    rv = re.search(r"\d*([a-z]+)0*(\d+)", raw_code)
    if not rv:
        return ""

    major = rv.group(1).upper()
    minor = rv.group(2)
    return f"{major}-{minor.zfill(3)}"
