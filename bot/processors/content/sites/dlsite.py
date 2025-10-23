from collections.abc import Callable
from pathlib import PurePath
from urllib.parse import SplitResult

from bs4 import BeautifulSoup

from bot.context import Context
from bot.lib.fetch.aio import get_html
from bot.lib.keyboard import make_book_keyboard, make_link_preview
from bot.types.answer import Answer


type _Parser = Callable[[BeautifulSoup], str]


_BOOK_CATEGORIES: set[tuple[str, str]] = {
    ("books", "work"),
}
_DOUJIN_CATEGORIES: set[tuple[str, str]] = {
    ("maniax", "work"),
}
_MANIAX_TOUCH_CATEGORIES: set[tuple[str, str]] = {
    ("maniax-touch", "work"),
    ("girls-touch", "work"),
    ("books-touch", "work"),
}


async def solve(
    *, url: str, parsed_url: SplitResult, context: Context
) -> Answer | None:
    rv = await _find_author(url=url, parsed_url=parsed_url)
    if not rv:
        return None

    return Answer(
        text=rv,
        keyboard=make_book_keyboard(rv, dvd_origin=context.dvd_origin),
        link_preview=make_link_preview(url),
    )


async def _find_author(*, url: str, parsed_url: SplitResult) -> str:
    if parsed_url.hostname != "www.dlsite.com":
        return ""

    parse = _dispatch_parser(parsed_url)
    if not parse:
        return ""

    try:
        html = await get_html(url)
    except Exception:
        return ""

    return parse(html)


def _dispatch_parser(parsed_url: SplitResult) -> _Parser | None:
    path = PurePath(parsed_url.path)
    category = (path.parts[1], path.parts[2])

    match category:
        case _ if category in _BOOK_CATEGORIES:
            return _find_from_book
        case _ if category in _DOUJIN_CATEGORIES:
            return _find_from_doujin
        case _ if category in _MANIAX_TOUCH_CATEGORIES:
            return _find_from_maniax_touch
        case _:
            return None


def _find_from_book(html: BeautifulSoup) -> str:
    anchor = html.select_one("#work_maker > tr:nth-child(1) > td:nth-child(2) > a")
    if not anchor:
        return ""
    author = anchor.text.strip()
    return author


def _find_from_doujin(html: BeautifulSoup) -> str:
    anchor = html.select_one("span.maker_name > a")
    if not anchor:
        return ""
    circle = anchor.text.strip()
    anchor = html.select_one("#work_outline > tr:nth-child(2) > td:nth-child(2) > a")
    author = "" if not anchor else anchor.text.strip()
    full_name = f"{circle} ({author})" if author else circle
    return full_name


def _find_from_maniax_touch(html: BeautifulSoup) -> str:
    anchor = html.select_one(".topicpath_item:nth-child(3) > a")
    if not anchor:
        return ""
    author = anchor.text.strip()
    return author
