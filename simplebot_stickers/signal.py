"""Signal sticker pack downlad tools"""

from urllib import parse

import anyio
from signalstickers_client import StickersClient


async def _get_stickers(pack_id: str, pack_key: str) -> tuple:
    async with StickersClient() as client:
        pack = await client.get_pack(pack_id, pack_key)
    return (pack.title, pack.stickers)


def get_stickers(url: str) -> tuple:
    result = parse.urlsplit(url)
    if result.query:
        data = dict(parse.parse_qsl(result.query))
    else:
        data = dict(parse.parse_qsl(result.fragment))
    return anyio.run(_get_stickers, data["pack_id"], data["pack_key"])


def is_pack(url: str) -> bool:
    return url.startswith(("https://signal.art/addstickers/", "sgnl://addstickers/"))
