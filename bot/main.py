import asyncio
from logging.config import dictConfig as dict_config

from wcpan.logging import ConfigBuilder

from .context import get_context
from .daemon.api import api_daemon
from .daemon.polling import polling_daemon


async def amain() -> int:
    _setup_loggers()

    context = get_context()
    lock = _setup_signals()

    async with (
        polling_daemon(context) as enqueue,
        api_daemon(context, enqueue=enqueue),
    ):
        await lock.wait()

    return 0


def _setup_loggers():
    dict_config(
        ConfigBuilder().add("bot", level="D").add("telegram").add("aiohttp").to_dict()
    )


def _setup_signals():
    from signal import SIGABRT, SIGINT, SIGTERM

    stop_signals = (SIGINT, SIGTERM, SIGABRT)
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    for sig in stop_signals:
        loop.add_signal_handler(sig, lambda: stop_event.set())

    return stop_event
