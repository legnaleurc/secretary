import re
from functools import partial
from logging import getLogger
from urllib.parse import urlsplit, urlunsplit

from bot.context import Context

from ._lib import make_link_preview, make_save_keyboard
from .types import Answer, Solver


_L = getLogger(__name__)


def create_solver(context: Context) -> Solver:
    return partial(_solve)


async def _solve(unknown_text: str, /) -> Answer | None:
    title, video_url = _parse_tweet(unknown_text)
    if not title or not video_url:
        _L.warning(f"no title {title} or video_url {video_url}")
        return None

    return Answer(
        text=title,
        link_preview=make_link_preview(video_url),
        keyboard=make_save_keyboard(video_url, f"{title}.mp4"),
    )


def _parse_tweet(unknown_text: str) -> tuple[str, str]:
    pattern = r"^(.+)\n+(ttps://video\.twimg\.com/\S+)$"
    stripped = unknown_text.strip()
    match = re.match(pattern, stripped)
    if not match:
        return "", ""
    title = match.group(1)
    video_url = match.group(2)
    video_url = _normalize_video_url(video_url)
    return title, video_url


def _normalize_video_url(url: str) -> str:
    if url.startswith("ttps://"):
        url = "h" + url
    parts = urlsplit(url)
    parts = parts._replace(query="", fragment="")
    url = urlunsplit(parts)
    return url
