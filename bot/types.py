from typing import TypedDict, NotRequired

from telegram import InlineKeyboardMarkup, LinkPreviewOptions


class AnswerDict(TypedDict):
    text: str
    keyboard: NotRequired[InlineKeyboardMarkup]
    link_preview: NotRequired[LinkPreviewOptions]
