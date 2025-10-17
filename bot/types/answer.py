from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from telegram import InlineKeyboardMarkup, LinkPreviewOptions


@dataclass(kw_only=True, frozen=True)
class Answer:
    text: str
    should_delete: bool = False
    keyboard: InlineKeyboardMarkup | None = None
    link_preview: LinkPreviewOptions | None = None

    @property
    def html_text(self) -> str:
        if self.should_delete:
            return f"<strike>{self.text}</strike>"
        return f"<code>{self.text}</code>"


type Solver = Callable[[str], Awaitable[Answer | None]]
