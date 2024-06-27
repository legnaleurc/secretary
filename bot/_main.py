from telegram.ext import ApplicationBuilder

from ._context import get_context
from ._handlers.text_message import create_text_message_handler


def main() -> int:
    context = get_context()
    application = ApplicationBuilder().token(context.api_token).build()
    application.add_handler(create_text_message_handler())
    application.run_polling()
    return 0
