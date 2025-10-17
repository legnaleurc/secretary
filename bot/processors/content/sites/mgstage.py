from pathlib import PurePath
from urllib.parse import SplitResult

from bot.context import Context
from bot.lib.keyboard import make_av_keyboard, make_link_preview
from bot.types.answer import Answer


async def solve(
    *, url: str, parsed_url: SplitResult, context: Context
) -> Answer | None:
    if parsed_url.hostname != "www.mgstage.com":
        return None

    path = PurePath(parsed_url.path)
    if path.parts[1] != "product":
        return None
    if path.parts[2] != "product_detail":
        return None

    av_id = path.parts[3]

    return Answer(
        text=av_id,
        keyboard=make_av_keyboard(av_id, dvd_origin=context.dvd_origin),
        link_preview=make_link_preview(url),
    )
