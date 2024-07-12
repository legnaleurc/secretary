import os
from dataclasses import dataclass


type DvdList = list[tuple[str, str]]


@dataclass(frozen=True, kw_only=True)
class Context:
    api_token: str
    dvd_list: DvdList


def get_context():
    api_token = os.environ.get("API_TOKEN", "")
    dvd_list = os.environ.get("DVD_LIST", "")
    if not api_token:
        raise RuntimeError("`API_TOKEN` environment variable missing")
    return Context(api_token=api_token, dvd_list=parse_dvd_list(dvd_list))


def parse_dvd_list(dvd_list: str) -> DvdList:
    if not dvd_list:
        return []
    pair_list = dvd_list.split(" ")
    raw_list = (_.split("|") for _ in pair_list)
    return [(_[0], _[1]) for _ in raw_list]
