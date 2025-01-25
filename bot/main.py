import asyncio

from wcpan.logging import ConfigBuilder

from .context import get_context
from .daemon.api import api_daemon
from .daemon.bot import bot_daemon


async def amain() -> int:
    _setup_loggers()

    context = get_context()
    lock = _setup_signals()

    async with (
        bot_daemon(context) as (webhook, enqueue),
        api_daemon(context, webhook=webhook, enqueue=enqueue),
    ):
        await lock.wait()

    return 0


def _setup_loggers():
    from logging.config import dictConfig

    dictConfig(ConfigBuilder().add("bot", level="D").to_dict())


def _setup_signals():
    from signal import SIGABRT, SIGINT, SIGTERM

    stop_signals = (SIGINT, SIGTERM, SIGABRT)
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    for sig in stop_signals:
        loop.add_signal_handler(sig, lambda: stop_event.set())

    return stop_event
