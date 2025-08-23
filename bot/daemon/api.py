from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from functools import partial, wraps
from typing import Concatenate, TypedDict

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


class TextData(TypedDict):
    chat_id: int
    text: str


type EnqueueCallback = Callable[[int, str], Awaitable[None]]
type WebhookCallback = Callable[[dict[str, object]], Awaitable[None]]


TOKEN_HEADER = "X-Telegram-Bot-Api-Secret-Token"

KEY_TOKEN = AppKey[str]("KEY_TOKEN")


@asynccontextmanager
async def api_daemon(
    context: Context, *, webhook: WebhookCallback | None, enqueue: EnqueueCallback
):
    app = Application()

    app[KEY_TOKEN] = context.client_token

    app.router.add_route("POST", "/api/v1/text", partial(_handle_text, enqueue=enqueue))

    if webhook and context.webhook_path:
        app.router.add_route(
            "POST", context.webhook_path, partial(_handle_webhook, webhook=webhook)
        )

    runner = AppRunner(app)
    await runner.setup()
    try:
        site = TCPSite(runner, host=context.host, port=context.port)
        await site.start()
        yield
    finally:
        await runner.cleanup()


def _token_required[**P](
    fn: Callable[Concatenate[Request, P], Awaitable[Response]],
) -> Callable[Concatenate[Request, P], Awaitable[Response]]:
    @wraps(fn)
    async def _assert_token(
        request: Request, *args: P.args, **kwargs: P.kwargs
    ) -> Response:
        if not _is_valid(request):
            raise HTTPUnauthorized()
        return await fn(request, *args, **kwargs)

    return _assert_token


def _is_valid(request: Request) -> bool:
    token = request.app.get(KEY_TOKEN, "")
    if not token:
        return True
    answer = request.headers.get(TOKEN_HEADER)
    return answer == token


@_token_required
async def _handle_text(request: Request, *, enqueue: EnqueueCallback) -> Response:
    data: TextData = await request.json()
    chat_id = data["chat_id"]
    text = data["text"]

    await enqueue(chat_id, text)

    raise HTTPNoContent()


@_token_required
async def _handle_webhook(request: Request, *, webhook: WebhookCallback) -> Response:
    data: dict[str, object] = await request.json()

    await webhook(data)

    raise HTTPNoContent()
