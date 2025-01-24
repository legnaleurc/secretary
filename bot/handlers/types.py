from typing import Protocol

from bot.types import AnswerDict


class Dispatcher(Protocol):
    async def __call__(self, unknown_text: str, /) -> AnswerDict | None: ...
