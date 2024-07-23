from aiohttp import ClientSession
from bs4 import BeautifulSoup


async def get_json(url: str, *, query: dict[str, str] | None = None):
    async with ClientSession() as session:
        async with session.get(
            url,
            params=query,
        ) as response:
            response.raise_for_status()
            return await response.json()


async def get_html(
    url: str,
    *,
    query: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
):
    async with ClientSession() as session:
        async with session.get(
            url,
            params=query,
            cookies=cookies,
        ) as response:
            response.raise_for_status()
            text = await response.text(errors="ignore")
            return BeautifulSoup(text, "html.parser")
