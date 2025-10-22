import os
from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Context:
    # Telegram Bot API token
    api_token: str

    # Telegram Webhook settings
    host: str
    port: int
    webhook_url: str
    webhook_path: str
    client_token: str

    # external integrations
    dvd_origin: str
    duld_origin: str
    torrent_url: str


def get_context(strict: bool = True):
    api_token = os.environ.get("API_TOKEN", "")
    host = os.environ.get("HOST", "")
    port = os.environ.get("PORT", "")
    webhook_url = os.environ.get("WEBHOOK_URL", "")
    webhook_path = os.environ.get("WEBHOOK_PATH", "")
    client_token = os.environ.get("CLIENT_TOKEN", "")
    dvd_origin = os.environ.get("DVD_ORIGIN", "")
    duld_origin = os.environ.get("DULD_ORIGIN", "")
    torrent_url = os.environ.get("TORRENT_URL", "")
    if strict and not api_token:
        raise RuntimeError("`API_TOKEN` environment variable missing")
    return Context(
        api_token=api_token,
        host=host,
        port=int(port) if port else 0,
        webhook_url=webhook_url,
        webhook_path=webhook_path,
        client_token=client_token,
        dvd_origin=dvd_origin,
        duld_origin=duld_origin,
        torrent_url=torrent_url,
    )
