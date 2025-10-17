import plistlib
from asyncio import as_completed
from collections.abc import AsyncIterator
from logging import getLogger
from typing import Any

from bot.lib.url import maybe_resolve_url
from bot.types.answer import Answer, Solver


_L = getLogger(__name__)


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
