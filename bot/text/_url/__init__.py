from collections.abc import Sequence
from functools import partial
from logging import getLogger
from typing import Protocol
from urllib.parse import SplitResult, urlsplit

from bot.context import Context

from .._lib import first_not_none
from ..types import Answer, Solver


class _SubParser(Protocol):
    async def __call__(self, *, url: str, parsed_url: SplitResult) -> Answer | None: ...


_L = getLogger(__name__)


def create_solver(context: Context) -> Solver:
    from .dlsite import solve as dlsite
    from .dmm import solve as dmm
    from .mgstage import solve as mgstage
    from .nyaa import solve as nyaa

    site_list = [dmm, mgstage, dlsite, nyaa]
    parser_list = [partial(_, context=context) for _ in site_list]

    return partial(_solve, parser_list=parser_list)


async def _solve(
    unknown_text: str, /, *, parser_list: Sequence[_SubParser]
) -> Answer | None:
    try:
        parsed_url = urlsplit(unknown_text)
    except Exception as e:
        _L.debug(f"not a url: {e}")
        return None

    callback_list = (
        partial(_, url=unknown_text, parsed_url=parsed_url) for _ in parser_list
    )
    return await first_not_none(callback_list)
