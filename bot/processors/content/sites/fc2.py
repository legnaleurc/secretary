import re
from urllib.parse import SplitResult

from bot.context import Context
from bot.processors.content.jav import fc2_answer
from bot.types.answer import Answer


_ARTICLE_PATH = re.compile(r"^/article/(\d+)/?$")


async def solve(
    *, url: str, parsed_url: SplitResult, context: Context
) -> Answer | None:
    if parsed_url.hostname != "adult.contents.fc2.com":
        return None

    match = _ARTICLE_PATH.fullmatch(parsed_url.path)
    if not match:
        return None

    av_id = f"FC2-PPV-{match.group(1)}"
    return fc2_answer(av_id, dvd_origin=context.dvd_origin)
