import re
from collections.abc import Iterable
from logging import getLogger
from pathlib import PurePath
from urllib.parse import urlparse

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters


_L = getLogger(__name__)


async def handle_av(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        _L.warning("no update.message")
        return

    url = update.message.text
    if not url:
        _L.warning("no update.message.text")
        return

    try:
        av_id = parse_id(url)
    except Exception as e:
        _L.debug(f"not a url: {e}")
        return

    if not av_id:
        _L.debug(f"no id from {url}")
        return

    await update.message.reply_text(av_id, reply_to_message_id=update.message.id)


def parse_id(url: str) -> str:
    parsed = urlparse(url)

    if parsed.hostname != "www.dmm.co.jp":
        return ""

    path = PurePath(parsed.path)
    if path.parts[1] != "digital":
        return ""

    return find_id_from_dmm(path.parts)


def find_id_from_dmm(args: Iterable[str]) -> str:
    av_id = ""
    for arg in args:
        rv = re.match(r"^cid=(.+)$", arg)
        if not rv:
            continue
        av_id = rv.group(1)
        break
    else:
        return ""

    rv = re.search(r"\d*([a-z]+)0*(\d+)", av_id)
    if not rv:
        return ""

    major = rv.group(1).upper()
    minor = rv.group(2)
    return f"{major}-{minor:03}"


def av_handler():
    return MessageHandler(filters.TEXT & ~filters.COMMAND, handle_av)
