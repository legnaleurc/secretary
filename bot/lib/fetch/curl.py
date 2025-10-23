"""curl_cffi-based fetch implementation."""

from contextlib import asynccontextmanager
from typing import Any

from bs4 import BeautifulSoup
from curl_cffi import AsyncSession, Response

from bot.types.json import JsonDict


_FINGERPRINT = "chrome120"


async def get_json(
    url: str,
    *,
    queries: dict[str, str] | None = None,
    headers: list[tuple[str, str]] | None = None,
) -> Any:
    """Get JSON response from URL using curl_cffi."""
    async with _http_get(url, queries=queries, headers=headers) as response:
        return response.json()  # type: ignore


async def get_html(
    url: str,
    *,
    cookies: dict[str, str] | None = None,
    headers: list[tuple[str, str]] | None = None,
) -> BeautifulSoup:
    """Get HTML response from URL and parse with BeautifulSoup using curl_cffi."""
    async with _http_get(url, cookies=cookies, headers=headers) as response:
        text = response.text
        return BeautifulSoup(text, "html.parser")


async def post_json(
    url: str,
    *,
    data: JsonDict | None = None,
    headers: list[tuple[str, str]] | None = None,
) -> Any:
    """Post JSON data to URL and return JSON response using curl_cffi."""
    async with _http_post(url, data=data, headers=headers) as response:
        return response.json()  # type: ignore


async def post_none(
    url: str,
    *,
    data: JsonDict | None = None,
    headers: list[tuple[str, str]] | None = None,
) -> str:
    """Post JSON data to URL and return text response using curl_cffi."""
    async with _http_post(url, data=data, headers=headers) as response:
        return response.text


@asynccontextmanager
async def _http_get(
    url: str,
    *,
    queries: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
    headers: list[tuple[str, str]] | None = None,
):
    """HTTP GET request with curl_cffi AsyncSession."""
    async with AsyncSession[Response](impersonate=_FINGERPRINT, timeout=30) as session:
        response = await session.get(
            url,
            params=queries,
            cookies=cookies,
            headers=headers,
        )
        response.raise_for_status()
        yield response


@asynccontextmanager
async def _http_post(
    url: str,
    *,
    data: JsonDict | None = None,
    headers: list[tuple[str, str]] | None = None,
):
    """HTTP POST request with curl_cffi AsyncSession."""
    async with AsyncSession[Response](impersonate=_FINGERPRINT, timeout=30) as session:
        response = await session.post(url, json=data, headers=headers)
        response.raise_for_status()
        yield response
