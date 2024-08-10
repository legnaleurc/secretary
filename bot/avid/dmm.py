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


class VideoId:
    def __init__(self, series: str, number: str) -> None:
        self._series = series.upper()
        self._number = number
        self._re = re.compile(rf"{self._series}.*{self._number}", re.I)

    @property
    def series(self) -> str:
        return self._series

    @property
    def number(self) -> str:
        return self._number

    def __str__(self) -> str:
        return f"{self.series}-{self.number}"

    def exclude(self, raw_id: str) -> str:
        return self._re.sub("", raw_id)


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
        "keyboard": make_av_keyboard(str(avid), dvd_list=dvd_list),
    }


def parse_avid(unknown_text: str) -> VideoId | None:
    m = re.search(r"(\w{2,6})[-_](\d{2,4}\w?)", unknown_text)
    if not m:
        return None
    return VideoId(m.group(1), m.group(2))


async def get_url(avid: VideoId) -> str:
    soup = await get_html(f"https://www.dmm.co.jp/search/=/searchstr={str(avid)}/")

    anchor_list = soup.select(".txt > a")
    if not anchor_list:
        return ""

    pair_list = sorted(filter(None, (get_cid_and_url(_, avid) for _ in anchor_list)))
    original = pair_list[0][-1]
    return original


def get_cid_and_url(anchor: Tag, avid: VideoId) -> tuple[str, str] | None:
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

    cid = get_cid(parsed_url.path, avid)
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
def get_cid(url_path: str, avid: VideoId) -> str:
    path = PurePath(url_path)
    last = path.parts[-1]
    raw_id = last.replace("cid=", "")
    return avid.exclude(raw_id)
