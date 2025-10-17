from asyncio import Queue
from dataclasses import dataclass
from functools import partial
from logging import getLogger

from telegram.constants import ParseMode
from telegram.ext import ContextTypes, TypeHandler

from bot.context import Context
from bot.processors.pipeline import create_multiple_solver, create_single_solver
from bot.types.answer import Solver

from .lib import generate_answers, parse_plist


@dataclass
class ApiTextUpdate:
    chat_id: int
    text: str


_L = getLogger(__name__)


async def _solve_api_text(
    update: ApiTextUpdate,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    single_solve: Solver,
    multiple_solve: Solver,
) -> None:
    unknown_text = update.text
    if not unknown_text:
        _L.warning("empty input")
        return

    if unknown_text.startswith("about:"):
        return

    if plist := parse_plist(unknown_text):
        _L.debug(f"got plist: {plist}")
        return

    async for answer in generate_answers(
        update.text, single_solve=single_solve, multiple_solve=multiple_solve
    ):
        if not answer:
            continue

        await context.bot.send_message(
            update.chat_id,
            answer.html_text,
            parse_mode=ParseMode.HTML,
            reply_markup=answer.keyboard,
            link_preview_options=answer.link_preview,
        )


async def enqueue_update(*, chat_id: int, text: str, queue: Queue[object]) -> None:
    await queue.put(ApiTextUpdate(chat_id=chat_id, text=text))


def create_webhook_handler(context: Context):
    single_solve = create_single_solver(context)
    multiple_solve = create_multiple_solver(context)
    return TypeHandler(
        type=ApiTextUpdate,
        callback=partial(
            _solve_api_text, single_solve=single_solve, multiple_solve=multiple_solve
        ),
    )
