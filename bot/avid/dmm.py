import re
from logging import getLogger
from urllib.parse import urlsplit, urlunsplit

from telegram import LinkPreviewOptions

from bot.lib import get_html
from bot.types import AnswerDict


_L = getLogger(__name__)


async def parse_dmm(unknown_text: str) -> AnswerDict | None:
    avid = parse_avid(unknown_text)
    if not avid:
        return None

    url = await get_url(avid)
    if not url:
        return None

    return {
        "text": url,
        "link_preview": LinkPreviewOptions(is_disabled=False, url=url),
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

    anchor = soup.select_one(".txt > a:nth-child(1)")
    if not anchor:
        return ""

    raw_url = anchor.get("href")
    if not raw_url:
        return ""
    if not isinstance(raw_url, str):
        return ""

    try:
        parsed_url = urlsplit(raw_url)
    except Exception:
        _L.exception(f"invalid url {raw_url}")
        return ""

    url = urlunsplit(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            "",
            "",
        )
    )
    return url
