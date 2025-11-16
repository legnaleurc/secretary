from functools import partial
from logging import getLogger

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.context import Context
from bot.processors.pipeline import create_multiple_solver, create_single_solver
from bot.types.answer import Solver

from .lib import generate_answers, retry_on_timeout


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

    message = update.message
    unknown_text = message.text
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

        html_text = answer.html_text
        keyboard = answer.keyboard
        link_preview = answer.link_preview

        await retry_on_timeout(
            lambda: message.reply_html(
                html_text,
                reply_markup=keyboard,
                link_preview_options=link_preview,
            )
        )

    if ok:
        await context.bot.delete_message(message.chat.id, message.id)


def create_message_handler(context: Context):
    single_solve = create_single_solver(context)
    multiple_solve = create_multiple_solver(context)
    text_solver = partial(
        _dispatch_text_message, single_solve=single_solve, multiple_solve=multiple_solve
    )
    return MessageHandler(filters.TEXT & ~filters.COMMAND, text_solver)
