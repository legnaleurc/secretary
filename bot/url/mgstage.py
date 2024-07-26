from pathlib import PurePath
from urllib.parse import SplitResult

from bot.context import DvdList
from bot.lib import make_av_keyboard
from bot.types import AnswerDict


async def parse_mgstage(
    *, url: str, parsed_url: SplitResult, dvd_list: DvdList
) -> AnswerDict | None:
    if parsed_url.hostname != "www.mgstage.com":
        return None

    path = PurePath(parsed_url.path)
    if path.parts[1] != "product":
        return None
    if path.parts[2] != "product_detail":
        return None

    av_id = path.parts[3]

    return {
        "text": av_id,
        "keyboard": make_av_keyboard(av_id, dvd_list=dvd_list),
    }
