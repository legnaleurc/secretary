import os
from dataclasses import dataclass


type DvdList = list[tuple[str, str]]


@dataclass(frozen=True, kw_only=True)
class Context:
    api_token: str
    host: str
    port: int
    webhook_url: str
    webhook_path: str
    client_token: str
    dvd_list: DvdList
    duld_origin: str
    torrent_url: str


def get_context():
    api_token = os.environ.get("API_TOKEN", "")
    host = os.environ.get("HOST", "")
    port = os.environ.get("PORT", "")
    webhook_url = os.environ.get("WEBHOOK_URL", "")
    webhook_path = os.environ.get("WEBHOOK_PATH", "")
    client_token = os.environ.get("CLIENT_TOKEN", "")
    dvd_list = os.environ.get("DVD_LIST", "")
    duld_origin = os.environ.get("DULD_ORIGIN", "")
    torrent_url = os.environ.get("TORRENT_URL", "")
    if not api_token:
        raise RuntimeError("`API_TOKEN` environment variable missing")
    return Context(
        api_token=api_token,
        host=host,
        port=int(port) if port else 0,
        webhook_url=webhook_url,
        webhook_path=webhook_path,
        client_token=client_token,
        dvd_list=_parse_dvd_list(dvd_list),
        duld_origin=duld_origin,
        torrent_url=torrent_url,
    )


def _parse_dvd_list(dvd_list: str) -> DvdList:
    if not dvd_list:
        return []
    pair_list = dvd_list.split(" ")
    raw_list = (_.split("|") for _ in pair_list)
    return [(_[0], _[1]) for _ in raw_list]
