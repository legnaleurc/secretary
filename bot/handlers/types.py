from typing import Literal, TypedDict


class SaveUrlCallbackAction(TypedDict):
    type: Literal["save_url"]
    url: str
    name: str | None


type CallbackAction = SaveUrlCallbackAction
