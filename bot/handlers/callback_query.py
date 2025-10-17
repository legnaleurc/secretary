from functools import partial
from logging import getLogger
from typing import cast

from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from bot.context import Context
from bot.integrations.duld import save_url
from bot.types.callback import CallbackAction


_L = getLogger(__name__)


async def _dispatch_query(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    duld_origin: str,
) -> None:
    query = update.callback_query
    if not query:
        _L.warning("empty callback query")
        return None

    ok = await query.answer()
    if not ok:
        _L.warning("failed to answer query")
        return None

    data = cast(CallbackAction, query.data)
    _L.debug("query data: %s", data)

    if not data:
        _L.warning("empty query data")
        return None

    if data["type"] == "save_url":
        if not duld_origin:
            _L.warning("no duld_origin")
            return None
        await save_url(data["url"], data["name"], duld_origin=duld_origin)
        return None

    return None


def create_callback_query_handler(context: Context):
    return CallbackQueryHandler(
        partial(_dispatch_query, duld_origin=context.duld_origin)
    )
