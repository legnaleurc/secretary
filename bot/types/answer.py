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

    def to_dict(self) -> dict[str, object]:
        return {
            "text": self.text,
            "should_delete": self.should_delete,
            "keyboard": self.keyboard.to_dict() if self.keyboard else None,
            "link_preview": self.link_preview.to_dict() if self.link_preview else None,
        }


type Solver = Callable[[str], Awaitable[Answer | None]]
