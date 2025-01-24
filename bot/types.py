from typing import NotRequired, TypedDict

from telegram import InlineKeyboardMarkup, LinkPreviewOptions


class AnswerDict(TypedDict):
    text: str
    keyboard: NotRequired[InlineKeyboardMarkup]
    link_preview: NotRequired[LinkPreviewOptions]
