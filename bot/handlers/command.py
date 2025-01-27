from telegram import ReplyParameters, Update
from telegram.ext import CommandHandler, ContextTypes


async def handle_chat_id(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    await update.message.reply_markdown_v2(
        f"`{update.message.chat_id}`",
        reply_parameters=ReplyParameters(message_id=update.message.id),
    )


def create_command_handler():
    return CommandHandler("chat_id", handle_chat_id)
