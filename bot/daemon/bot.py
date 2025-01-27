import logging
from collections.abc import Awaitable, Callable
from contextlib import AsyncExitStack, asynccontextmanager

from telegram import Update
from telegram.ext import Application, Updater

from bot.context import Context
from bot.handlers.command import create_command_handler
from bot.handlers.text_api import create_text_api_handler, enqueue_update
from bot.handlers.text_message import create_text_message_handler


_L = logging.getLogger(__name__)


@asynccontextmanager
async def bot_daemon(context: Context):
    application = Application.builder().token(context.api_token).build()
    application.add_handler(create_text_message_handler(context))
    application.add_handler(create_text_api_handler(context))
    application.add_handler(create_command_handler())

    has_webhook = _has_webhook(context)
    if has_webhook:
        await application.bot.set_webhook(
            url=context.webhook_url,
            secret_token=context.client_token if context.client_token else None,
        )

    async with AsyncExitStack() as stack:
        await stack.enter_async_context(application)

        if not application.updater:
            return

        if not has_webhook:
            await stack.enter_async_context(_polling_context(application.updater))

        await stack.enter_async_context(
            _queue_context(
                start=application.start,
                stop=application.stop,
                is_running=lambda: application.running,
            )
        )

        async def _enqueue_api_text(chat_id: int, text: str):
            await enqueue_update(
                chat_id=chat_id, text=text, queue=application.update_queue
            )

        async def _enqueue_webhook(json_data: dict[str, object]):
            await application.update_queue.put(
                Update.de_json(data=json_data, bot=application.bot)
            )

        try:
            yield (_enqueue_webhook if has_webhook else None), _enqueue_api_text
        except (KeyboardInterrupt, SystemExit):
            _L.debug("expected normal exit")


def _has_webhook(context: Context) -> bool:
    return all((context.listen_list, context.webhook_url, context.webhook_path))


@asynccontextmanager
async def _polling_context(updater: Updater):
    await updater.start_polling()
    try:
        yield updater
    finally:
        if updater.running:
            await updater.stop()


@asynccontextmanager
async def _queue_context[CB: Callable[[], Awaitable[None]]](
    *, start: CB, stop: CB, is_running: Callable[[], bool]
):
    await start()
    try:
        yield
    finally:
        if is_running():
            await stop()
