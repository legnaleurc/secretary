from collections.abc import Sequence
from functools import partial
from logging import getLogger

from bot.context import Context

from ._lib import first_not_none
from .types import Answer, Solver


_L = getLogger(__name__)


def create_single_solver(context: Context) -> Solver:
    from ._avid import create_solver as avid
    from ._twitter import create_single_solver as twitter
    from ._url import create_solver as url

    # NOTE avid should be the last.
    type_list = [twitter, url, avid]
    solver_list = [_(context) for _ in type_list]

    return partial(_solve, solver_list=solver_list)


def create_multiple_solver(context: Context) -> Solver:
    from ._twitter import create_multiple_solver as twitter

    type_list = [twitter]
    solver_list = [_(context) for _ in type_list]

    return partial(_solve, solver_list=solver_list)


async def _solve(
    unknown_text: str, /, *, solver_list: Sequence[Solver]
) -> Answer | None:
    callback_list = (partial(_, unknown_text) for _ in solver_list)
    return await first_not_none(callback_list)
