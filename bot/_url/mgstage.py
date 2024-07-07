from pathlib import PurePath
from urllib.parse import ParseResult

from bot._types import AnswerDict
from ._lib import make_keyboard


async def parse_mgstage(*, url: str, parsed_url: ParseResult) -> AnswerDict | None:
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
        "keyboard": make_keyboard(av_id),
    }
