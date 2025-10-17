from functools import partial
from logging import getLogger

from wcpan.jav import generate_products
from wcpan.jav.types import Product

from bot.context import Context
from bot.lib.keyboard import make_av_keyboard, make_link_preview
from bot.types.answer import Answer, Solver


_L = getLogger(__name__)


def create_solver(context: Context) -> Solver:
    return partial(_solve, dvd_origin=context.dvd_origin)


async def _solve(unknown_text: str, /, *, dvd_origin: str) -> Answer | None:
    async for product in generate_products(unknown_text):
        match product.sauce:
            case "javbee":
                continue
            case "fc2":
                return fc2_answer(product, dvd_origin=dvd_origin)
            case "tokyohot":
                return tokyohot_answer(product, dvd_origin=dvd_origin)
            case _:
                return default_answer(product, dvd_origin=dvd_origin)

    return None


def default_answer(product: Product, *, dvd_origin: str) -> Answer:
    return Answer(
        text=product.id,
        link_preview=make_link_preview(product.url),
        keyboard=make_av_keyboard(product.id, dvd_origin=dvd_origin),
    )


def tokyohot_answer(product: Product, *, dvd_origin: str) -> Answer:
    url = product.url + "?lang=ja"
    return Answer(
        text=product.id,
        link_preview=make_link_preview(url),
        keyboard=make_av_keyboard(product.id, dvd_origin=dvd_origin),
    )


def fc2_answer(product: Product, *, dvd_origin: str) -> Answer:
    alt_link = _get_fc2_url(product.id)
    return Answer(
        text=product.id,
        keyboard=make_av_keyboard(product.id, dvd_origin=dvd_origin, alt_link=alt_link),
    )


def _get_fc2_url(id_: str) -> dict[str, str]:
    id_ = id_.replace("FC2-PPV-", "")
    return {
        "EC": f"https://adult.contents.fc2.com/article/{id_}/",
        "DB": f"https://fc2ppvdb.com/articles/{id_}",
    }
