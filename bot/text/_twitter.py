import re
from logging import getLogger
from pathlib import PurePath
from urllib.parse import urlsplit, urlunsplit

from bot.context import Context

from ._lib import make_link_preview, make_save_keyboard
from .types import Answer, Solver


_L = getLogger(__name__)


def create_multiple_solver(context: Context) -> Solver:
    return _solve_multi_line


def create_single_solver(context: Context) -> Solver:
    return _solve_single_line


async def _solve_multi_line(unknown_text: str, /) -> Answer | None:
    title, video_url = _parse_tweet(unknown_text)
    if not title or not video_url:
        return None

    return Answer(
        text=title,
        link_preview=make_link_preview(video_url),
        keyboard=make_save_keyboard(video_url, f"{title}.mp4"),
    )


async def _solve_single_line(unknown_text: str, /) -> Answer | None:
    pattern = r"^h?ttps://video\.twimg\.com/\S+$"
    stripped = unknown_text.strip()
    match = re.match(pattern, stripped)
    if not match:
        return None
    video_url = match.group(0)
    video_url = _normalize_video_url(video_url)
    name = _get_video_name(video_url)
    return Answer(
        text=name,
        link_preview=make_link_preview(video_url),
        keyboard=make_save_keyboard(video_url, f"{name}.mp4"),
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


def _get_video_name(url: str) -> str:
    parts = urlsplit(url)
    path = PurePath(parts.path)
    return path.stem
