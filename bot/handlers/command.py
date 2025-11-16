from telegram import ReplyParameters, Update
from telegram.ext import CommandHandler, ContextTypes

from bot.handlers.lib import retry_on_timeout


async def handle_chat_id(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    message = update.message

    await retry_on_timeout(
        lambda: message.reply_markdown_v2(
            f"`{message.chat_id}`",
            reply_parameters=ReplyParameters(message_id=message.id),
        )
    )


def create_command_handler():
    return CommandHandler("chat_id", handle_chat_id)
