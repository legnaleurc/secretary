from functools import partial
from logging import getLogger
from typing import Protocol

from bot.avid.dmm import parse_dmm
from bot.avid.fc2 import parse_fc2
from bot.context import Context
from bot.types import AnswerDict


class Parser(Protocol):
    async def __call__(self, unknown_text: str, /) -> AnswerDict | None: ...


_L = getLogger(__name__)


class AvidDispatcher:
    def __init__(self, parser_list: list[Parser]) -> None:
        self._parser_list = parser_list

    async def __call__(self, unknown_text: str) -> AnswerDict | None:
        for parser in self._parser_list:
            try:
                answer = await parser(unknown_text)
                if answer:
                    return answer
            except Exception:
                _L.exception("parse failed")
        return None


def create_avid_dispatcher(context: Context):
    return AvidDispatcher(
        [
            partial(parse_dmm, dvd_list=context.dvd_list),
            partial(parse_fc2, dvd_list=context.dvd_list),
        ]
    )
