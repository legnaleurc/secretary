import re
from collections.abc import Iterable
from pathlib import PurePath
from urllib.parse import SplitResult

from bot._types import AnswerDict
from ._lib import make_keyboard, get_json


async def parse_dmm(*, url: str, parsed_url: SplitResult) -> AnswerDict | None:
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


def _find_av_id(*, url: str, parsed_url: SplitResult) -> str:
    if parsed_url.hostname != "www.dmm.co.jp":
        return ""

    path = PurePath(parsed_url.path)
    if path.parts[1] != "digital":
        return ""

    return _find_id_from_path(path.parts)


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
