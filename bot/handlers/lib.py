import plistlib
from asyncio import as_completed
from collections.abc import AsyncIterator, Awaitable, Callable
from logging import getLogger
from typing import Any

from telegram.error import TimedOut

from bot.lib.url import maybe_resolve_url
from bot.types.answer import Answer, Solver


_L = getLogger(__name__)


async def retry_on_timeout[T](
    coro_factory: Callable[[], Awaitable[T]], *, max_retries: int = 3
) -> T:
    """
    Retry an async operation on TimeOut exception.

    Args:
        coro_factory: A callable that returns an awaitable (coroutine factory)
        max_retries: Maximum number of retry attempts (default: 3, meaning initial + 2 retries)

    Returns:
        The result of the awaitable

    Raises:
        TimedOut: If all retry attempts are exhausted
        Any other exception raised by the awaitable
    """
    for attempt in range(max_retries):
        try:
            return await coro_factory()
        except TimedOut:
            if attempt < max_retries - 1:
                _L.warning(
                    f"Telegram TimeOut on attempt {attempt + 1}/{max_retries}, retrying..."
                )
            else:
                _L.error(f"Telegram TimeOut after {max_retries} attempts, giving up")
                raise

    raise RuntimeError("unreachable code in retry_on_timeout")


def parse_plist(unknown_text: str) -> Any:
    try:
        return plistlib.loads(unknown_text.encode("utf-8"))
    except plistlib.InvalidFileException:
        return None
    except Exception:
        _L.exception("unexpected error in plist")
        return None


async def generate_answers(
    unknown_text: str, /, *, single_solve: Solver, multiple_solve: Solver
) -> AsyncIterator[Answer | None]:
    if answer := await multiple_solve(unknown_text):
        yield answer
        return
    lines = unknown_text.splitlines()
    normalized_lines = filter(None, (_.strip() for _ in lines))
    producers = (_get_answer(_, single_solve) for _ in normalized_lines)
    for consumer in as_completed(producers):
        yield await consumer


async def _get_answer(unknown_text: str, solve: Solver) -> Answer | None:
    unknown_text = await maybe_resolve_url(unknown_text)

    try:
        answer = await solve(unknown_text)
    except Exception:
        _L.exception(f"error while solving {unknown_text}")
        return None

    if not answer:
        _L.info(f"no answer from {unknown_text}")
        return None

    return answer
