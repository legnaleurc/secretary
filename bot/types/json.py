type JsonValue = str | int | float | bool | None
type JsonList = list["JsonType"]
type JsonDict = dict[str, "JsonType"]
type JsonType = JsonValue | JsonList | JsonDict
