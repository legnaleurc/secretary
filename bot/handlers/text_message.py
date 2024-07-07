from logging import getLogger
from typing import Protocol
from urllib.parse import SplitResult, urlsplit

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.types import AnswerDict
from bot.url.dmm import parse_dmm
from bot.url.mgstage import parse_mgstage


class Parser(Protocol):
    async def __call__(
        self, *, url: str, parsed_url: SplitResult
    ) -> AnswerDict | None: ...


_L = getLogger(__name__)


class TextMessageDispatcher:
    def __init__(self, parser_list: list[Parser]):
        self._parser_list = parser_list

    async def __call__(
        self, update: Update, _context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not update.message:
            _L.warning("no update.message")
            return

        url = update.message.text
        if not url:
            _L.warning("no update.message.text")
            return

        try:
            parsed_url = urlsplit(url)
        except Exception as e:
            _L.debug(f"not a url: {e}")
            return

        answer = await self._parse(url=url, parsed_url=parsed_url)
        if not answer:
            _L.debug(f"no answer from {url}")
            return

        await update.message.reply_text(
            answer["text"],
            reply_markup=answer.get("keyboard", None),
            reply_to_message_id=update.message.id,
        )

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


def create_text_message_handler():
    dispatcher = TextMessageDispatcher(
        [
            parse_dmm,
            parse_mgstage,
        ]
    )
    return MessageHandler(filters.TEXT & ~filters.COMMAND, dispatcher)
