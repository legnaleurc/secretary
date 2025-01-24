import logging
from asyncio import Queue
from dataclasses import dataclass
from functools import partial

from telegram.ext import ContextTypes, TypeHandler

from bot.context import Context

from .avid import create_avid_dispatcher
from .types import Dispatcher
from .url import create_url_dispatcher


@dataclass
class ApiTextUpdate:
    chat_id: int
    text: str


_L = logging.getLogger(__name__)


async def _dispatch_api_text(
    update: ApiTextUpdate,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    dispatcher_list: list[Dispatcher],
) -> None:
    unknown_text = update.text.strip()
    if not unknown_text:
        _L.debug("ignored empty message")
        return

    answer = None
    for dispatch in dispatcher_list:
        try:
            answer = await dispatch(unknown_text)
            if answer:
                break
        except Exception:
            _L.exception("dispatcher error")

    if not answer:
        _L.debug(f"no answer from {unknown_text}")
        return

    text = answer["text"]
    message = f"{text}\n\n{unknown_text}"

    await context.bot.send_message(
        update.chat_id,
        message,
        reply_markup=answer.get("keyboard", None),
        link_preview_options=answer.get("link_preview", None),
    )


async def enqueue_update(*, chat_id: int, text: str, queue: Queue[object]) -> None:
    await queue.put(ApiTextUpdate(chat_id=chat_id, text=text))


def create_text_api_handler(context: Context):
    url_dispatcher = create_url_dispatcher(context)
    avid_dispatcher = create_avid_dispatcher(context)
    return TypeHandler(
        type=ApiTextUpdate,
        callback=partial(
            _dispatch_api_text,
            dispatcher_list=[
                url_dispatcher,
                avid_dispatcher,
            ],
        ),
    )
