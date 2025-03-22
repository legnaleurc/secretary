from contextlib import asynccontextmanager
from typing import Any

from aiohttp import ClientSession
from bs4 import BeautifulSoup


async def get_json(url: str, *, queries: dict[str, str] | None = None):
    async with _http_get(url, queries=queries) as response:
        return await response.json()


async def get_html(url: str, *, cookies: dict[str, str] | None = None) -> BeautifulSoup:
    async with _http_get(url, cookies=cookies) as response:
        text = await response.text(errors="ignore")
        return BeautifulSoup(text, "html.parser")


async def post_none(url: str, *, data: Any | None = None):
    async with (
        ClientSession() as session,
        session.post(url, json=data) as response,
    ):
        response.raise_for_status()
        return await response.text()


@asynccontextmanager
async def _http_get(
    url: str,
    *,
    queries: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
):
    async with (
        ClientSession() as session,
        session.get(
            url,
            params=queries,
            cookies=cookies,
        ) as response,
    ):
        response.raise_for_status()
        yield response
