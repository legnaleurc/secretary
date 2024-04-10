import os
from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Context:
    api_token: str


def get_context():
    api_token = os.environ.get("API_TOKEN", "")
    if not api_token:
        raise RuntimeError("`API_TOKEN` environment variable missing")
    return Context(api_token=api_token)
