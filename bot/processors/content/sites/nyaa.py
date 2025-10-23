from logging import getLogger
from pathlib import PurePath
from urllib.parse import SplitResult

from bot.context import Context
from bot.lib.fetch.aio import post_json
from bot.lib.keyboard import make_torrent_keyboard
from bot.types.answer import Answer


_L = getLogger(__name__)


async def solve(
    *, url: str, parsed_url: SplitResult, context: Context
) -> Answer | None:
    if parsed_url.hostname != "sukebei.nyaa.si":
        return None

    path = PurePath(parsed_url.path)
    if path.suffix != ".torrent":
        return None

    torrent_name = await _send_to_duld(url, duld_origin=context.duld_origin)

    return Answer(
        text=torrent_name,
        keyboard=make_torrent_keyboard(context.torrent_url),
    )


async def _send_to_duld(url: str, *, duld_origin: str) -> str:
    api_url = f"{duld_origin}/api/v1/torrents"
    torrent_dict = await post_json(api_url, data={"urls": [url]})
    _L.debug("torrent_dict: %s", torrent_dict)
    return torrent_dict[url]["name"]
