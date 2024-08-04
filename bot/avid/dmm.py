import re
from logging import getLogger
from pathlib import PurePath
from urllib.parse import urlsplit, urlunsplit

from bs4 import Tag
from telegram import LinkPreviewOptions

from bot.lib import get_html, make_av_keyboard
from bot.context import DvdList
from bot.types import AnswerDict


_L = getLogger(__name__)


async def parse_dmm(unknown_text: str, *, dvd_list: DvdList) -> AnswerDict | None:
    avid = parse_avid(unknown_text)
    if not avid:
        return None

    url = await get_url(avid)
    if not url:
        return None

    return {
        "text": url,
        "link_preview": LinkPreviewOptions(is_disabled=False, url=url),
        "keyboard": make_av_keyboard(avid, dvd_list=dvd_list),
    }


def parse_avid(unknown_text: str) -> str:
    m = re.search(r"(\w{2,6})[-_](\d{2,4}\w?)", unknown_text)
    if not m:
        return ""
    name = f"{m.group(1)}-{m.group(2)}"
    name = name.upper()
    return name


async def get_url(avid: str) -> str:
    soup = await get_html(f"https://www.dmm.co.jp/search/=/searchstr={avid}/")

    anchor_list = soup.select(".txt > a")
    if not anchor_list:
        return ""

    flat_id = avid.replace("-", "").lower()

    pair_list = sorted(filter(None, (get_cid_and_url(_, flat_id) for _ in anchor_list)))
    original = pair_list[0][-1]
    return original


def get_cid_and_url(anchor: Tag, flat_id: str) -> tuple[str, str] | None:
    raw_url = anchor.get("href")
    if not raw_url:
        return None
    if not isinstance(raw_url, str):
        return None

    try:
        parsed_url = urlsplit(raw_url)
    except Exception:
        _L.exception(f"invalid url {raw_url}")
        return None

    cid = get_cid(parsed_url.path, flat_id)
    url = urlunsplit(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            "",
            "",
        )
    )
    return cid, url


# The original should have no prefix, should be the first after sorting.
def get_cid(url_path: str, flat_id: str) -> str:
    path = PurePath(url_path)
    last = path.parts[-1]
    return last.replace("cid=", "").replace(flat_id, "")
