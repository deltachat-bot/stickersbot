"""Signal sticker pack downlad tools"""

import functools
import os
import random
import zipfile
from tempfile import NamedTemporaryFile
from urllib import parse
from urllib.parse import quote, quote_plus

import anyio
import appdirs
import requests
from cachelib import FileSystemCache
from emoji import demojize
from signalstickers_client import StickersClient
from signalstickers_client.models.sticker_pack import StickerPack

_cache_dir = appdirs.user_cache_dir("simplebot_stickers")
_cache = FileSystemCache(_cache_dir, threshold=5000, default_timeout=0)
_session = requests.Session()
_session.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:92.0) Gecko/20100101 Firefox/92.0"
    }
)
_session.request = functools.partial(_session.request, timeout=15)  # type: ignore
MAX_PACK_SIZE = 1024 ** 2 * 20


async def _get_pack(pack_id: str, pack_key: str) -> StickerPack:
    async with StickersClient() as client:
        return await client.get_pack_metadata(pack_id, pack_key)


async def _get_sticker(sticker_id: int, pack_id: str, pack_key: str) -> bytes:
    async with StickersClient() as client:
        return await client.download_sticker(sticker_id, pack_id, pack_key)


def _get_cached_pack(pack_id: str, pack_key: str) -> StickerPack:
    pack = _cache.get(pack_id)
    if not pack:
        pack = anyio.run(_get_pack, pack_id, pack_key)
        _cache.set(pack_id, pack)
    return pack


def _get_cached_sticker(sticker_id: int, pack_id: str, pack_key: str) -> bytes:
    cache_key = f"{pack_id}+{sticker_id}"
    sticker = _cache.get(cache_key)
    if not sticker:
        sticker = anyio.run(_get_sticker, sticker_id, pack_id, pack_key)
        _cache.set(cache_key, sticker)
    return sticker


def _parse_url(url: str) -> tuple:
    result = parse.urlsplit(url)
    if result.query:
        data = dict(parse.parse_qsl(result.query))
    else:
        data = dict(parse.parse_qsl(result.fragment))
    return data["pack_id"], data["pack_key"]


def _get_pack_url(pack_id: str, pack_key: str) -> str:
    return f"sgnl://addstickers/?pack_id={pack_id}&pack_key={pack_key}"


def _get_metadata() -> dict:
    url = "https://api.signalstickers.com/v1/packs/"
    data = _cache.get(url)
    if not data:
        with _session.get(url) as resp:
            resp.raise_for_status()
            data = resp.json()
        _cache.set(url, data, timeout=60 * 60 * 24 * 7)
    return data


def _get_tags(mpack: dict) -> list:
    tags = mpack["meta"].get("tags", [])
    if mpack["meta"].get("nsfw", False):
        tags.append("nsfw")
    if mpack["meta"].get("animated", False):
        tags.append("animated")
    if mpack["meta"].get("original", False):
        tags.append("original")
    return list(set(tags))


def is_pack(url: str) -> bool:
    return url.startswith(("https://signal.art/addstickers/", "sgnl://addstickers/"))


def download_pack(base_dir: str, pack_url: str) -> str:
    pack = _get_cached_pack(*_parse_url(pack_url))
    pack_name = quote(pack.title, safe="")
    with NamedTemporaryFile(
        dir=base_dir,
        prefix=pack_name + "-",
        suffix=".stickers.zip",
        delete=False,
    ) as file:
        zip_path = file.name
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zfile:
        size = 0
        for sticker in pack.stickers:
            desc = demojize(sticker.emoji, delimiters=("", ""))
            name = os.path.join(pack_name, f"{sticker.id}.{desc}+{sticker.emoji}.webp")
            data = _get_cached_sticker(sticker.id, pack.id, pack.key)
            size += len(data)
            if size > MAX_PACK_SIZE:
                break
            zfile.writestr(name, data)
    return zip_path


def search(query: str) -> list:
    data = _get_metadata()
    packs = []
    count = 0
    for pack in data:
        title = pack["manifest"].get("title", "")
        if query in title or query in _get_tags(pack):
            packs.append(pack)
            count += 1
            if count > 100:
                break
    return packs


def search_html(addr: str, query: str) -> str:
    html = ""
    for pack in search(query):
        url = _get_pack_url(pack["meta"]["id"], pack["meta"]["key"])
        url = f"mailto:{addr}?body={quote_plus(url)}"
        title = pack["manifest"].get("title", "NO TITLE")
        author = pack["manifest"].get("author", "ANONYMOUS")
        html += f'{title} - by {author}<br/><a href="{url}">DOWNLOAD</a><br/><hr/>'
    return html


def get_random_sticker(emoji: str) -> tuple:
    data = _get_metadata()
    i = 0
    while i < 200 and data:
        mpack = data.pop(random.randrange(len(data)))
        pack = _get_cached_pack(mpack["meta"]["id"], mpack["meta"]["key"])
        for sticker in pack.stickers:
            if sticker.emoji == emoji:
                url = _get_pack_url(pack.id, pack.key)
                return url, _get_cached_sticker(sticker.id, pack.id, pack.key)
        i += 1
    return "", b""
