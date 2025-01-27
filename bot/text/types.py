from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from telegram import InlineKeyboardMarkup, LinkPreviewOptions


@dataclass(kw_only=True, frozen=True)
class Answer:
    text: str
    keyboard: InlineKeyboardMarkup | None = None
    link_preview: LinkPreviewOptions | None = None


type Solver = Callable[[str], Awaitable[Answer | None]]
