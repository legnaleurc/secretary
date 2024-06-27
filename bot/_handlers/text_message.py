from collections.abc import Callable
from logging import getLogger
from urllib.parse import urlparse, ParseResult

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bot._av.dmm import parse_dmm
from bot._av.mgstage import parse_mgstage


type Parser = Callable[[ParseResult], str]


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
            parsed_url = urlparse(url)
        except Exception as e:
            _L.debug(f"not a url: {e}")
            return

        av_id = self._parse(parsed_url)
        if not av_id:
            _L.debug(f"no id from {url}")
            return

        await update.message.reply_text(av_id, reply_to_message_id=update.message.id)

    def _parse(self, parsed_url: ParseResult) -> str:
        for parser in self._parser_list:
            try:
                rv = parser(parsed_url)
                if rv:
                    return rv
            except Exception:
                _L.exception("parse failed")
                continue
        else:
            return ""


def create_text_message_handler():
    dispatcher = TextMessageDispatcher(
        [
            parse_dmm,
            parse_mgstage,
        ]
    )
    return MessageHandler(filters.TEXT & ~filters.COMMAND, dispatcher)
