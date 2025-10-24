from collections.abc import Callable
from logging import getLogger
from urllib.parse import SplitResult

from bs4 import BeautifulSoup

from bot.context import Context
from bot.lib.fetch.curl import get_html
from bot.lib.keyboard import make_book_keyboard, make_link_preview
from bot.types.answer import Answer


type _Parser = Callable[[BeautifulSoup], str]


_L = getLogger(__name__)


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
    if parsed_url.hostname != "nhentai.net":
        return ""

    if not parsed_url.path.startswith("/g/"):
        return ""

    try:
        html = await get_html(url)
    except Exception:
        _L.exception("Failed to fetch HTML for URL: %s", url)
        return ""

    span = html.select_one("h2.title > span:nth-child(1)")
    if not span:
        return ""

    author = span.text.strip()
    author = author[1:-1]  # Remove parentheses
    return author
