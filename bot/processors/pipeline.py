from collections.abc import Awaitable, Callable, Iterator, Sequence
from functools import partial
from logging import getLogger

from bot.context import Context
from bot.types.answer import Answer, Solver


_L = getLogger(__name__)


async def first_not_none[R](
    callbacks: Iterator[Callable[[], Awaitable[R | None]]],
) -> R | None:
    for cb in callbacks:
        try:
            rv = await cb()
            if rv is not None:
                return rv
        except Exception:
            _L.exception("error in loop")
    return None


def create_single_solver(context: Context) -> Solver:
    from .content.jav import create_solver as jav
    from .content.nh import create_solver as nh
    from .content.sites import create_solver as sites
    from .content.twitter import create_single_solver as twitter

    # NOTE jav should be the last.
    type_list = [twitter, sites, jav, nh]
    solver_list = [_(context) for _ in type_list]

    return partial(_solve, solver_list=solver_list)


def create_multiple_solver(context: Context) -> Solver:
    from .content.twitter import create_multiple_solver as twitter

    type_list = [twitter]
    solver_list = [_(context) for _ in type_list]

    return partial(_solve, solver_list=solver_list)


async def _solve(
    unknown_text: str, /, *, solver_list: Sequence[Solver]
) -> Answer | None:
    callback_list = (partial(_, unknown_text) for _ in solver_list)
    return await first_not_none(callback_list)
