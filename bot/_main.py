from telegram.ext import ApplicationBuilder

from ._context import get_context
from ._handlers.av import av_handler


def main() -> int:
    context = get_context()
    application = ApplicationBuilder().token(context.api_token).build()
    application.add_handler(av_handler())
    application.run_polling()
    return 0
