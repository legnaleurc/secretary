from collections.abc import Awaitable, Callable
from contextlib import AsyncExitStack, asynccontextmanager
from logging import getLogger

from telegram import Update
from telegram.ext import Application, Updater

from bot.context import Context
from bot.handlers.callback_query import create_callback_query_handler
from bot.handlers.command import create_command_handler
from bot.handlers.message import create_message_handler
from bot.handlers.webhook import create_webhook_handler, enqueue_update


_L = getLogger(__name__)


@asynccontextmanager
async def bot_daemon(context: Context):
    application = (
        Application.builder()
        .token(context.api_token)
        .arbitrary_callback_data(True)
        .build()
    )
    application.add_handler(create_message_handler(context))
    application.add_handler(create_webhook_handler(context))
    application.add_handler(create_command_handler())
    application.add_handler(create_callback_query_handler(context))

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
            update = Update.de_json(data=json_data, bot=application.bot)
            if not update:
                _L.warning("invalid update object from webhook")
                return None

            # required for callback query handler
            application.bot.insert_callback_data(update)
            await application.update_queue.put(update)

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
