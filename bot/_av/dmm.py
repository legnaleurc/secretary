import re
from collections.abc import Iterable
from pathlib import PurePath
from urllib.parse import ParseResult


def parse_dmm(parsed_url: ParseResult) -> str:
    if parsed_url.hostname != "www.dmm.co.jp":
        return ""

    path = PurePath(parsed_url.path)
    if path.parts[1] != "digital":
        return ""

    return find_id_from_dmm(path.parts)


def find_id_from_dmm(args: Iterable[str]) -> str:
    av_id = ""
    for arg in args:
        rv = re.match(r"^cid=(.+)$", arg)
        if not rv:
            continue
        av_id = rv.group(1)
        break
    else:
        return ""

    rv = re.search(r"\d*([a-z]+)0*(\d+)", av_id)
    if not rv:
        return ""

    major = rv.group(1).upper()
    minor = rv.group(2)
    return f"{major}-{minor.zfill(3)}"
