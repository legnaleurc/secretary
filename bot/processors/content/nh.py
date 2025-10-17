import re
from functools import partial
from logging import getLogger

from bot.context import Context
from bot.lib.fetch.curl import get_html
from bot.lib.keyboard import make_book_keyboard, make_link_preview
from bot.types.answer import Answer, Solver


_L = getLogger(__name__)


def create_solver(context: Context) -> Solver:
    return partial(_solve, dvd_origin=context.dvd_origin)


async def _solve(unknown_text: str, /, *, dvd_origin: str) -> Answer | None:
    pattern = r"^\d+$"
    stripped = unknown_text.strip()
    match = re.match(pattern, stripped)
    if not match:
        return None

    url = f"https://nhentai.net/g/{stripped}/"
    author = await _fetch_author(url)
    if not author:
        return None

    return Answer(
        text=author,
        link_preview=make_link_preview(url),
        keyboard=make_book_keyboard(author, dvd_origin=dvd_origin),
    )


async def _fetch_author(url: str, /) -> str:
    try:
        html = await get_html(url)
    except Exception:
        _L.exception("failed to fetch nhentai url=%s", url)
        return ""

    span = html.select_one("h2.title > span:nth-child(1)")
    if not span:
        _L.error("author span not found url=%s", url)
        return ""

    author: str = span.text.strip()
    author = author[1:-1]  # Remove parentheses
    return author
