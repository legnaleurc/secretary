from pathlib import PurePath
from urllib.parse import ParseResult


def parse_mgstage(parsed_url: ParseResult) -> str:
    if parsed_url.hostname != "www.mgstage.com":
        return ""

    path = PurePath(parsed_url.path)
    if path.parts[1] != "product":
        return ""
    if path.parts[2] != "product_detail":
        return ""

    return path.parts[3]
