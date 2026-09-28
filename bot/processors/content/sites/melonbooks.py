import re
from logging import getLogger
from urllib.parse import SplitResult, parse_qsl, urlencode, urlunsplit

from bs4 import BeautifulSoup

from bot.context import Context
from bot.lib.fetch.aio import get_html
from bot.lib.keyboard import make_book_keyboard, make_link_preview
from bot.types.answer import Answer


_L = getLogger(__name__)

_CIRCLE_SELECTOR = (
    ".table-wrapper > table:nth-child(1) > tr:nth-child(1)"
    " > td:nth-child(2) > a:nth-child(1)"
)
_AUTHOR_SELECTOR = (
    ".table-wrapper > table:nth-child(1) > tr:nth-child(2)"
    " > td:nth-child(2) > a:nth-child(1)"
)
_WORK_COUNT_PATTERN = re.compile(r"\(作品数:\s*\d+\)")


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
    if parsed_url.hostname != "www.melonbooks.co.jp":
        return ""

    if parsed_url.path != "/detail/detail.php":
        return ""

    try:
        html = await get_html(_with_adult_view(parsed_url))
    except Exception:
        _L.exception("Failed to fetch HTML for URL: %s", url)
        return ""

    return _parse_author(html)


def _with_adult_view(parsed_url: SplitResult) -> str:
    queries = parse_qsl(parsed_url.query, keep_blank_values=True)
    if ("adult_view", "1") in queries:
        return urlunsplit(parsed_url)

    queries = [(key, value) for key, value in queries if key != "adult_view"]
    queries.append(("adult_view", "1"))
    parsed = parsed_url._replace(query=urlencode(queries))
    return urlunsplit(parsed)


def _parse_author(html: BeautifulSoup) -> str:
    anchor = html.select_one(_CIRCLE_SELECTOR)
    if not anchor:
        return ""
    circle = _WORK_COUNT_PATTERN.sub("", anchor.text).strip()

    anchor = html.select_one(_AUTHOR_SELECTOR)
    author = "" if not anchor else _WORK_COUNT_PATTERN.sub("", anchor.text).strip()

    if not circle:
        return author
    if not author or author == circle:
        return circle
    return f"{circle} ({author})"
