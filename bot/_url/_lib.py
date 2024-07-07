from urllib.parse import urlunsplit, urlencode

from telegram import InlineKeyboardMarkup, InlineKeyboardButton


def make_keyboard(av_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "nyaa",
                    url=urlunsplit(
                        (
                            "https",
                            "sukebei.nyaa.si",
                            "/",
                            urlencode(
                                {
                                    "f": "0",
                                    "c": "2_0",
                                    "q": av_id,
                                }
                            ),
                            "",
                        )
                    ),
                ),
                InlineKeyboardButton(
                    "jav",
                    url=urlunsplit(
                        (
                            "https",
                            "jav-torrent.org",
                            "/search",
                            urlencode(
                                {
                                    "keyword": av_id,
                                }
                            ),
                            "",
                        )
                    ),
                ),
                InlineKeyboardButton(
                    "bee",
                    url=urlunsplit(
                        (
                            "https",
                            "javbee.me",
                            "/search",
                            urlencode(
                                {
                                    "keyword": av_id,
                                }
                            ),
                            "",
                        )
                    ),
                ),
            ],
        ]
    )
