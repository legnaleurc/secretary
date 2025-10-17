from bot.lib.fetch import post_none


async def save_url(url: str, name: str | None, *, duld_origin: str) -> None:
    api = duld_origin + "/api/v1/links"
    await post_none(
        api,
        data={
            "url": url,
            "name": name,
        },
    )
