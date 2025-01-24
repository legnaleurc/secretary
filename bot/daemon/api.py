import logging
import re
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from functools import wraps
from typing import TypedDict
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from aiohttp.web import (
    AppKey,
    Application,
    AppRunner,
    Request,
    Response,
    TCPSite,
    json_response,
)
from aiohttp.web_exceptions import HTTPUnauthorized

from bot.context import Context


class TextData(TypedDict):
    chat_id: int
    text: str


type EnqueueCallback = Callable[[int, str], Awaitable[None]]


KEY_TOKEN = AppKey[str]("KEY_TOKEN")
KEY_ENQUEUE = AppKey[EnqueueCallback]("KEY_ENQUEUE")


_L = logging.getLogger(__name__)


@asynccontextmanager
async def api_daemon(context: Context, *, enqueue: EnqueueCallback):
    app = Application()

    app[KEY_TOKEN] = context.client_token
    app[KEY_ENQUEUE] = enqueue

    app.router.add_route("POST", "/api/v1/text", _handle_text)

    runner = AppRunner(app)
    await runner.setup()
    try:
        for host, port in context.listen_list:
            site = TCPSite(runner, host=host, port=port)
            await site.start()
        yield
    finally:
        await runner.cleanup()


def _token_required(
    fn: Callable[[Request], Awaitable[Response]],
) -> Callable[[Request], Awaitable[Response]]:
    def _is_valid(request: Request) -> bool:
        token = request.app.get(KEY_TOKEN, "")
        if not token:
            return True
        authorization = request.headers.get("Authorization")
        if not authorization:
            return False
        rv = re.match(r"Token\s+(.+)", authorization)
        if not rv:
            return False
        return rv.group(1) == token

    @wraps(fn)
    async def _assert_token(request: Request) -> Response:
        if not _is_valid(request):
            raise HTTPUnauthorized(
                headers={
                    "WWW-Authenticate": f"Token realm=api",
                },
            )
        return await fn(request)

    return _assert_token


@_token_required
async def _handle_text(request: Request) -> Response:
    enqueue = request.app[KEY_ENQUEUE]

    data: TextData = await request.json()
    chat_id = data["chat_id"]
    text = data["text"]

    text = _strip_trackers(text)

    await enqueue(chat_id, text)

    return json_response(
        {
            "text": text,
        }
    )


def _strip_trackers(unknown_text: str) -> str:
    try:
        parts = urlsplit(unknown_text)
    except Exception:
        return unknown_text

    queries = parse_qsl(parts.query)
    filtered = [(key, value) for key, value in queries if not key.startswith("utm_")]
    query = urlencode(filtered)

    parts = parts._replace(query=query)
    url = urlunsplit(parts)
    return url
