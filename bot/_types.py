from typing import TypedDict, NotRequired

from telegram import InlineKeyboardMarkup


class AnswerDict(TypedDict):
    text: str
    keyboard: NotRequired[InlineKeyboardMarkup]
