from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from functools import wraps
from typing import TypedDict

from aiohttp.web import (
    AppKey,
    Application,
    AppRunner,
    Request,
    Response,
    TCPSite,
)
from aiohttp.web_exceptions import HTTPNoContent, HTTPUnauthorized

from bot.context import Context
from bot.lib import strip_url_trackers


class TextData(TypedDict):
    chat_id: int
    text: str


type EnqueueCallback = Callable[[int, str], Awaitable[None]]
type WebhookCallback = Callable[[dict[str, object]], Awaitable[None]]


TOKEN_HEADER = "X-Telegram-Bot-Api-Secret-Token"

KEY_TOKEN = AppKey[str]("KEY_TOKEN")
KEY_ENQUEUE = AppKey[EnqueueCallback]("KEY_ENQUEUE")
KEY_WEBHOOK = AppKey[WebhookCallback]("KEY_WEBHOOK")


@asynccontextmanager
async def api_daemon(
    context: Context, *, webhook: WebhookCallback | None, enqueue: EnqueueCallback
):
    app = Application()

    app[KEY_TOKEN] = context.client_token
    app[KEY_ENQUEUE] = enqueue

    app.router.add_route("POST", "/api/v1/text", _handle_text)
    if webhook and context.webhook_path:
        app[KEY_WEBHOOK] = webhook
        app.router.add_route("POST", context.webhook_path, _handle_webhook)

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
        answer = request.headers.get(TOKEN_HEADER)
        return answer == token

    @wraps(fn)
    async def _assert_token(request: Request) -> Response:
        if not _is_valid(request):
            raise HTTPUnauthorized()
        return await fn(request)

    return _assert_token


@_token_required
async def _handle_text(request: Request) -> Response:
    enqueue = request.app[KEY_ENQUEUE]

    data: TextData = await request.json()
    chat_id = data["chat_id"]
    text = data["text"]

    text = await strip_url_trackers(text)

    await enqueue(chat_id, text)

    raise HTTPNoContent()


@_token_required
async def _handle_webhook(request: Request) -> Response:
    webhook = request.app[KEY_WEBHOOK]

    data: dict[str, object] = await request.json()

    await webhook(data)

    raise HTTPNoContent()
