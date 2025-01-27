from collections.abc import Sequence
from functools import partial
from logging import getLogger

from bot.context import Context

from .._lib import first_not_none
from ..types import Answer, Solver


_L = getLogger(__name__)


def create_solver(context: Context) -> Solver:
    from .dmm import solve as dmm
    from .fc2 import solve as fc2

    site_list = [dmm, fc2]
    solver_list = [partial(_, dvd_list=context.dvd_list) for _ in site_list]

    return partial(_solve, solver_list=solver_list)


async def _solve(
    unknown_text: str, /, *, solver_list: Sequence[Solver]
) -> Answer | None:
    callback_list = (partial(_, unknown_text) for _ in solver_list)
    return await first_not_none(callback_list)
