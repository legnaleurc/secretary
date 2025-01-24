from logging import getLogger

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.context import Context

from .avid import create_avid_dispatcher
from .types import Dispatcher
from .url import create_url_dispatcher


_L = getLogger(__name__)


class TextMessageDispatcher:
    def __init__(self, dispatcher_list: list[Dispatcher]):
        self._dispatcher_list = dispatcher_list

    async def __call__(
        self, update: Update, _context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not update.message:
            _L.warning("no update.message")
            return

        unknown_text = update.message.text
        if not unknown_text:
            _L.warning("no update.message.text")
            return

        answer = None
        for dispatch in self._dispatcher_list:
            try:
                answer = await dispatch(unknown_text)
                if answer:
                    break
            except Exception:
                _L.exception("dispatcher error")

        if not answer:
            _L.debug(f"no answer from {unknown_text}")
            return

        await update.message.reply_text(
            answer["text"],
            reply_markup=answer.get("keyboard", None),
            link_preview_options=answer.get("link_preview", None),
            reply_to_message_id=update.message.id,
        )


def create_text_message_handler(context: Context):
    url_dispatcher = create_url_dispatcher(context)
    avid_dispatcher = create_avid_dispatcher(context)
    text_dispatcher = TextMessageDispatcher(
        [
            url_dispatcher,
            avid_dispatcher,
        ]
    )
    return MessageHandler(filters.TEXT & ~filters.COMMAND, text_dispatcher)
