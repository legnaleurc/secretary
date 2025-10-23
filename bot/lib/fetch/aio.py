"""aiohttp-based fetch implementation."""

from contextlib import asynccontextmanager
from typing import Any

from aiohttp import ClientSession
from bs4 import BeautifulSoup

from bot.types.json import JsonDict


async def get_json(
    url: str,
    *,
    queries: dict[str, str] | None = None,
    headers: list[tuple[str, str]] | None = None,
) -> Any:
    """Get JSON response from URL."""
    async with _http_get(url, queries=queries, headers=headers) as response:
        return await response.json()


async def get_html(
    url: str,
    *,
    cookies: dict[str, str] | None = None,
    headers: list[tuple[str, str]] | None = None,
) -> BeautifulSoup:
    """Get HTML response from URL and parse with BeautifulSoup."""
    async with _http_get(url, cookies=cookies, headers=headers) as response:
        text = await response.text(errors="ignore")
        return BeautifulSoup(text, "html.parser")


async def post_json(
    url: str,
    *,
    data: JsonDict | None = None,
    headers: list[tuple[str, str]] | None = None,
) -> Any:
    """Post JSON data to URL and return JSON response."""
    async with _http_post(url, data=data, headers=headers) as response:
        return await response.json()


async def post_none(
    url: str,
    *,
    data: JsonDict | None = None,
    headers: list[tuple[str, str]] | None = None,
) -> str:
    """Post JSON data to URL and return text response."""
    async with _http_post(url, data=data, headers=headers) as response:
        return await response.text()


@asynccontextmanager
async def _http_get(
    url: str,
    *,
    queries: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
    headers: list[tuple[str, str]] | None = None,
):
    """HTTP GET request with aiohttp."""
    async with (
        ClientSession() as session,
        session.get(
            url,
            params=queries,
            cookies=cookies,
            headers=headers,
        ) as response,
    ):
        response.raise_for_status()
        yield response


@asynccontextmanager
async def _http_post(
    url: str,
    *,
    data: JsonDict | None = None,
    headers: list[tuple[str, str]] | None = None,
):
    """HTTP POST request with aiohttp."""
    async with (
        ClientSession() as session,
        session.post(url, json=data, headers=headers) as response,
    ):
        response.raise_for_status()
        yield response
