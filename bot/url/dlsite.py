from pathlib import PurePath
from urllib.parse import SplitResult

from bot.context import DvdList
from bot.lib import get_html, make_book_keyboard
from bot.types import AnswerDict


_DOUJIN_CATEGORIES: set[tuple[str, str]] = {
    ("books", "work"),
}


async def parse_dlsite(
    *, url: str, parsed_url: SplitResult, dvd_list: DvdList
) -> AnswerDict | None:
    rv = await _find_doujin_author(url=url, parsed_url=parsed_url)
    if rv:
        return {
            "text": rv,
            "keyboard": make_book_keyboard(rv, dvd_list=dvd_list),
        }

    return None


async def _find_doujin_author(*, url: str, parsed_url: SplitResult) -> str:
    if parsed_url.hostname != "www.dlsite.com":
        return ""

    path = PurePath(parsed_url.path)
    category = (path.parts[1], path.parts[2])
    if category not in _DOUJIN_CATEGORIES:
        return ""

    try:
        html = await get_html(
            url,
        )
    except Exception:
        return ""

    anchor = html.select_one("#work_maker > tr:nth-child(1) > td:nth-child(2) > a")
    if not anchor:
        return ""
    author = anchor.text.strip()
    return author
