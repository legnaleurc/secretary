from functools import partial
from logging import getLogger
from typing import Protocol
from urllib.parse import SplitResult, urlsplit

from bot.context import Context
from bot.types import AnswerDict
from bot.url.dmm import parse_dmm
from bot.url.mgstage import parse_mgstage


class Parser(Protocol):
    async def __call__(
        self, *, url: str, parsed_url: SplitResult
    ) -> AnswerDict | None: ...


_L = getLogger(__name__)


class UrlDispatcher:
    def __init__(self, parser_list: list[Parser]) -> None:
        self._parser_list = parser_list

    async def __call__(self, unknown_text: str) -> AnswerDict | None:
        try:
            parsed_url = urlsplit(unknown_text)
        except Exception as e:
            _L.debug(f"not a url: {e}")
            return None

        answer = await self._parse(url=unknown_text, parsed_url=parsed_url)
        if not answer:
            return None

        return answer

    async def _parse(self, *, url: str, parsed_url: SplitResult) -> AnswerDict | None:
        for parser in self._parser_list:
            try:
                rv = await parser(url=url, parsed_url=parsed_url)
                if rv:
                    return rv
            except Exception:
                _L.exception("parse failed")
                continue
        else:
            return None


def create_url_dispatcher(context: Context):
    return UrlDispatcher(
        [
            partial(parse_dmm, dvd_list=context.dvd_list),
            partial(parse_mgstage, dvd_list=context.dvd_list),
        ]
    )
