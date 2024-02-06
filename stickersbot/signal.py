"""Signal sticker pack downlad tools"""

import os
import random
import zipfile
from tempfile import NamedTemporaryFile
from urllib import parse
from urllib.parse import quote, quote_plus

import anyio
from cachelib import BaseCache, NullCache
from emoji import demojize
from signalstickers_client import StickersClient
from signalstickers_client.models.sticker_pack import StickerPack

from .util import session


class SignalStickers:
    """Class to manage Signal stickers and packs."""

    def __init__(self, cache: BaseCache = NullCache(), max_search_results=100) -> None:
        self.cache = cache
        self.max_search_results = max_search_results

    def _get_cached_pack(self, pack_id: str, pack_key: str) -> StickerPack:
        pack = self.cache.get(pack_id)
        if not pack:
            pack = anyio.run(_get_pack, pack_id, pack_key)
            self.cache.set(pack_id, pack)
        return pack

    def _get_cached_sticker(
        self, sticker_id: int, pack_id: str, pack_key: str
    ) -> bytes:
        cache_key = f"{pack_id}+{sticker_id}"
        sticker = self.cache.get(cache_key)
        if not sticker:
            sticker = anyio.run(_get_sticker, sticker_id, pack_id, pack_key)
            self.cache.set(cache_key, sticker)
        return sticker

    def _get_metadata(self) -> list:
        url = "https://api.signalstickers.com/v1/packs/"
        data = self.cache.get(url)
        if not data:
            with session.get(url) as resp:
                resp.raise_for_status()
                data = resp.json()
            self.cache.set(url, data, timeout=60 * 60 * 24 * 3)
        return data

    @staticmethod
    def is_pack(url: str) -> bool:
        return url.startswith(
            ("https://signal.art/addstickers/", "sgnl://addstickers/")
        )

    def get_pack_metadata(self, pack_url: str) -> tuple:
        pack = self._get_cached_pack(*_parse_url(pack_url))
        text = f"Title: {pack.title or 'NO TITLE'}\nAuthor: {pack.author or 'ANONYMOUS'}\nStickers: {len(pack.stickers)}"
        for mpack in self._get_metadata():
            if mpack["meta"]["id"] == pack.id:
                tags = _get_tags(mpack)
                if tags:
                    text += f"\nTags: {', '.join(tags)}"
                break
        return text, self._get_cached_sticker(pack.cover.id, pack.id, pack.key)

    def download_pack(self, base_dir: str, pack_url: str) -> tuple:
        pack = self._get_cached_pack(*_parse_url(pack_url))
        pack_name = quote(pack.title, safe="")
        with NamedTemporaryFile(
            dir=base_dir,
            prefix=pack_name + "-",
            suffix=".zip",
            delete=False,
        ) as file:
            zip_path = file.name
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zfile:
            for sticker in pack.stickers:
                desc = demojize(sticker.emoji, delimiters=("", ""))
                name = os.path.join(
                    pack_name, f"{sticker.id}.{desc}+{sticker.emoji}.webp"
                )
                data = self._get_cached_sticker(sticker.id, pack.id, pack.key)
                zfile.writestr(name, data)
        return pack.title, zip_path

    def search(self, query: str) -> list:
        query = query.lower()
        data = self._get_metadata()
        packs = []
        count = 0
        for pack in data:
            title = pack["manifest"].get("title", "").lower()
            if query in title or query in _get_tags(pack):
                packs.append(pack)
                count += 1
                if count == self.max_search_results:
                    break
        return packs

    def search_html(self, addr: str, query: str) -> str:
        html = ""
        for pack in self.search(query):
            url = _get_pack_url(pack["meta"]["id"], pack["meta"]["key"])
            more_url = f"mailto:{addr}?body=/info+{quote_plus(url)}"
            url = f"mailto:{addr}?body={quote_plus(url)}"
            title = pack["manifest"].get("title", "NO TITLE")
            author = pack["manifest"].get("author", "ANONYMOUS")
            tags = ", ".join(_get_tags(pack))
            html += f'Title: {title}<br/>Author: {author}<br/>Tags: {tags}<br/>\n<a href="{more_url}">MORE</a> | <a href="{url}">DOWNLOAD</a><br/><hr/>'
        return html

    def get_random_sticker(self, emoji: str) -> tuple:
        data = self._get_metadata()
        i = 0
        while i < 200 and data:
            mpack = data.pop(random.randrange(len(data)))
            pack = self._get_cached_pack(mpack["meta"]["id"], mpack["meta"]["key"])
            for sticker in pack.stickers:
                if sticker.emoji == emoji:
                    url = _get_pack_url(pack.id, pack.key)
                    return url, self._get_cached_sticker(sticker.id, pack.id, pack.key)
            i += 1
        return "", b""


async def _get_pack(pack_id: str, pack_key: str) -> StickerPack:
    async with StickersClient() as client:
        return await client.get_pack_metadata(pack_id, pack_key)


async def _get_sticker(sticker_id: int, pack_id: str, pack_key: str) -> bytes:
    async with StickersClient() as client:
        return await client.download_sticker(sticker_id, pack_id, pack_key)


def _parse_url(url: str) -> tuple:
    result = parse.urlsplit(url)
    if result.query:
        data = dict(parse.parse_qsl(result.query))
    else:
        data = dict(parse.parse_qsl(result.fragment))
    return data["pack_id"], data["pack_key"]


def _get_pack_url(pack_id: str, pack_key: str) -> str:
    return f"sgnl://addstickers/?pack_id={pack_id}&pack_key={pack_key}"


def _get_tags(mpack: dict) -> set:
    tags = set(tag.lower() for tag in mpack["meta"].get("tags", []))
    if mpack["meta"].get("nsfw", False):
        tags.add("nsfw")
    if mpack["meta"].get("animated", False):
        tags.add("animated")
    if mpack["meta"].get("original", False):
        tags.add("original")
    return set(tags)
