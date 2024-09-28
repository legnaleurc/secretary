import re

from telegram import LinkPreviewOptions

from bot.context import DvdList
from bot.lib import make_av_keyboard
from bot.types import AnswerDict


async def parse_fc2(unknown_text: str, *, dvd_list: DvdList) -> AnswerDict | None:
    avid = parse_avid(unknown_text)
    if not avid:
        return None

    url = await get_url(avid)
    if not url:
        return None

    avid = f"FC2-PPV-{avid}"

    return {
        "text": url,
        "link_preview": LinkPreviewOptions(is_disabled=False, url=url),
        "keyboard": make_av_keyboard(str(avid), dvd_list=dvd_list),
    }


def parse_avid(unknown_text: str) -> str | None:
    m = re.search(r"fc2-ppv-(\d+)", unknown_text, re.I)
    if not m:
        return None
    return m.group(1)


async def get_url(avid: str) -> str:
    return f"https://adult.contents.fc2.com/article/{avid}/"
