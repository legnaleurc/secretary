import os
from dataclasses import dataclass
from ipaddress import ip_address
from urllib.parse import urlsplit


type DvdList = list[tuple[str, str]]
type ListenList = list[tuple[str, int]]


@dataclass(frozen=True, kw_only=True)
class Context:
    api_token: str
    dvd_list: DvdList
    listen_list: ListenList
    client_token: str


def get_context():
    api_token = os.environ.get("API_TOKEN", "")
    dvd_list = os.environ.get("DVD_LIST", "")
    listen_list = os.environ.get("LISTEN_LIST", "")
    client_token = os.environ.get("CLIENT_TOKEN", "")
    if not api_token:
        raise RuntimeError("`API_TOKEN` environment variable missing")
    return Context(
        api_token=api_token,
        dvd_list=_parse_dvd_list(dvd_list),
        listen_list=_parse_listen_list(listen_list),
        client_token=client_token,
    )


def _parse_dvd_list(dvd_list: str) -> DvdList:
    if not dvd_list:
        return []
    pair_list = dvd_list.split(" ")
    raw_list = (_.split("|") for _ in pair_list)
    return [(_[0], _[1]) for _ in raw_list]


def _parse_listen_list(listen_list: str) -> ListenList:
    if not listen_list:
        return []
    pair_list = listen_list.split(" ")
    raw_list = (_parse_listen(_) for _ in pair_list)
    return [_ for _ in raw_list if _]


def _parse_listen(listen: str) -> tuple[str, int] | None:
    try:
        parts = urlsplit(f"tcp://{listen}")
        if not parts.hostname or not parts.port:
            return None
        ip = ip_address(parts.hostname)
        return str(ip), parts.port
    except Exception:
        return None
