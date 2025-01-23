import logging
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager

from telegram.ext import ApplicationBuilder, Updater

from bot.context import Context
from bot.handlers.text_message import create_text_message_handler


_L = logging.getLogger(__name__)


@asynccontextmanager
async def polling_daemon(context: Context):
    application = ApplicationBuilder().token(context.api_token).build()
    application.add_handler(create_text_message_handler(context))

    async with application:
        if not application.updater:
            return

        async with (
            polling_context(application.updater),
            application_context(
                start=application.start,
                stop=application.stop,
                is_running=lambda: application.running,
            ),
        ):
            try:
                yield application
            except (KeyboardInterrupt, SystemExit):
                _L.debug("expected normal exit")


@asynccontextmanager
async def polling_context(updater: Updater):
    await updater.start_polling()
    try:
        yield updater
    finally:
        if updater.running:
            await updater.stop()


@asynccontextmanager
async def application_context[CB: Callable[[], Awaitable[None]]](
    *, start: CB, stop: CB, is_running: Callable[[], bool]
):
    await start()
    try:
        yield
    finally:
        if is_running():
            await stop()
