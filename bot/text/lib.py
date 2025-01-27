from collections.abc import Sequence
from functools import partial
from logging import getLogger

from bot.context import Context

from ._lib import first_not_none
from .types import Answer, Solver


_L = getLogger(__name__)


def create_solver(context: Context) -> Solver:
    from .avid import create_solver as avid
    from .url import create_solver as url

    # NOTE avid should be the last.
    type_list = [url, avid]
    solver_list = [_(context) for _ in type_list]

    return partial(_solve, solver_list=solver_list)


async def _solve(
    unknown_text: str, /, *, solver_list: Sequence[Solver]
) -> Answer | None:
    callback_list = (partial(_, unknown_text) for _ in solver_list)
    return await first_not_none(callback_list)
