from functools import partial
from logging import getLogger
from typing import cast

from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from bot.context import Context
from bot.fetch import post_none

from .types import CallbackAction


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
        await _post_to_duld(data["url"], data["name"], duld_origin=duld_origin)
        return None

    return None


async def _post_to_duld(url: str, name: str | None, *, duld_origin: str) -> None:
    api = duld_origin + "/api/v1/links"
    await post_none(
        api,
        data={
            "url": url,
            "name": name,
        },
    )


def create_callback_query_handler(context: Context):
    return CallbackQueryHandler(
        partial(_dispatch_query, duld_origin=context.duld_origin)
    )
