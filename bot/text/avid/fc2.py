import re

from bot.context import DvdList

from .._lib import make_av_keyboard
from ..types import Answer


async def solve(unknown_text: str, *, dvd_list: DvdList) -> Answer | None:
    avid = _parse_avid(unknown_text)
    if not avid:
        return None

    alt_link = _get_url(avid)
    avid = f"FC2-PPV-{avid}"

    return Answer(
        text=avid,
        keyboard=make_av_keyboard(avid, dvd_list=dvd_list, alt_link=alt_link),
    )


def _parse_avid(unknown_text: str) -> str | None:
    m = re.search(r"fc2-ppv-(\d+)", unknown_text, re.I)
    if not m:
        return None
    return m.group(1)


def _get_url(avid: str) -> dict[str, str]:
    return {
        "EC": f"https://adult.contents.fc2.com/article/{avid}/",
        "DB": f"https://fc2ppvdb.com/articles/{avid}",
    }
