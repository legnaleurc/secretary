from functools import partial
from logging import getLogger

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.context import Context
from bot.text.lib import create_multiple_solver, create_single_solver
from bot.text.types import Solver

from ._lib import generate_answers


_L = getLogger(__name__)


async def _dispatch_text_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    single_solve: Solver,
    multiple_solve: Solver,
) -> None:
    if not update.message:
        _L.warning("no update.message")
        return

    unknown_text = update.message.text
    if not unknown_text:
        _L.warning("no update.message.text")
        return

    ok = True
    async for answer in generate_answers(
        unknown_text, single_solve=single_solve, multiple_solve=multiple_solve
    ):
        if not answer:
            ok = False
            continue

        await update.message.reply_html(
            answer.html_text,
            reply_markup=answer.keyboard,
            link_preview_options=answer.link_preview,
        )

    if ok:
        await context.bot.delete_message(update.message.chat.id, update.message.id)


def create_message_handler(context: Context):
    single_solve = create_single_solver(context)
    multiple_solve = create_multiple_solver(context)
    text_solver = partial(
        _dispatch_text_message, single_solve=single_solve, multiple_solve=multiple_solve
    )
    return MessageHandler(filters.TEXT & ~filters.COMMAND, text_solver)
