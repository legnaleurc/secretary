from functools import partial
from logging import getLogger

from telegram import ReplyParameters, Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.context import Context
from bot.text.lib import create_solver
from bot.text.types import Solver

from ._lib import normalize_if_url


_L = getLogger(__name__)


async def _dispatch_text_message(
    update: Update, _context: ContextTypes.DEFAULT_TYPE, *, solve: Solver
) -> None:
    if not update.message:
        _L.warning("no update.message")
        return

    unknown_text = update.message.text
    if not unknown_text:
        _L.warning("no update.message.text")
        return

    unknown_text = await normalize_if_url(unknown_text)

    answer = await solve(unknown_text)
    if not answer:
        _L.debug(f"no answer from {unknown_text}")
        return

    await update.message.reply_markdown_v2(
        f"`{answer.text}`",
        reply_parameters=ReplyParameters(
            message_id=update.message.id,
        ),
        reply_markup=answer.keyboard,
        link_preview_options=answer.link_preview,
    )


def create_text_message_handler(context: Context):
    solve = create_solver(context)
    text_solver = partial(_dispatch_text_message, solve=solve)
    return MessageHandler(filters.TEXT & ~filters.COMMAND, text_solver)
