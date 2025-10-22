import asyncio
import json
import sys
from logging import getLogger

from wcpan.logging import ConfigBuilder

from .context import get_context
from .daemon.api import api_daemon
from .daemon.bot import bot_daemon
from .handlers.lib import generate_answers
from .processors.pipeline import create_multiple_solver, create_single_solver


_L = getLogger(__name__)


async def _main_daemon() -> int:
    """Main entry point for daemon mode."""

    context = get_context()
    lock = _setup_signals()

    async with (
        bot_daemon(context) as (webhook, enqueue),
        api_daemon(context, webhook=webhook, enqueue=enqueue),
    ):
        await lock.wait()

    return 0


async def _main_pipeline(unknown_text: str) -> int:
    """Test the pipeline with given text and output JSON results."""

    try:
        # Initialize context with optional environment variables
        context = get_context(strict=False)

        # Create solvers (same as daemon dispatch)
        single_solve = create_single_solver(context)
        multiple_solve = create_multiple_solver(context)

        # Collect all answers
        answers = [
            answer
            async for answer in generate_answers(
                unknown_text, single_solve=single_solve, multiple_solve=multiple_solve
            )
            if answer
        ]

        # Convert to JSON and print
        result = [answer.to_dict() for answer in answers]
        print(json.dumps(result, indent=2, ensure_ascii=False))

        return 0 if answers else 1

    except Exception as e:
        _L.exception("Error in test pipeline")
        print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
        return 1


def main(args: list[str]) -> int:
    """Main entry point that handles both daemon and CLI modes."""

    _setup_loggers()

    if len(args) >= 2:
        # Test mode: run pipeline with provided text
        return asyncio.run(_main_pipeline(args[1]))
    else:
        # Daemon mode: run the bot
        return asyncio.run(_main_daemon())


def _setup_loggers():
    from logging.config import dictConfig

    dictConfig(
        ConfigBuilder().add("bot", level="D").add("telegram", "aiohttp").to_dict()
    )


def _setup_signals():
    from signal import SIGABRT, SIGINT, SIGTERM

    stop_signals = (SIGINT, SIGTERM, SIGABRT)
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    for sig in stop_signals:
        loop.add_signal_handler(sig, lambda: stop_event.set())

    return stop_event
