from pathlib import PurePath
from urllib.parse import ParseResult

from bot._types import AnswerDict


async def parse_mgstage(*, url: str, parsed_url: ParseResult) -> AnswerDict | None:
    if parsed_url.hostname != "www.mgstage.com":
        return None

    path = PurePath(parsed_url.path)
    if path.parts[1] != "product":
        return None
    if path.parts[2] != "product_detail":
        return None

    return {
        "text": path.parts[3],
    }
