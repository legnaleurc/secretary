from collections.abc import Awaitable, Callable
from functools import wraps
from logging import getLogger


_L = getLogger(__name__)


def async_trace[**P, R](fn: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    @wraps(fn)
    async def _wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        name = f"{fn.__module__}.{fn.__qualname__}"
        _L.debug(f"> {name} {args} {kwargs}")
        rv = await fn(*args, **kwargs)
        _L.debug(f"< {name} {rv}")
        return rv

    return _wrapper
