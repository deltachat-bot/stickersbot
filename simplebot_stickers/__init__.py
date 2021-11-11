"""Plugin's filters and commands definitions."""

import io
import os

import simplebot
from deltachat import Message
from emoji import get_emoji_regexp
from simplebot.bot import DeltaBot, Replies

from . import signal, telegram
from .util import getdefault, sizeof_fmt, upload

DEF_MAX_PACK_SIZE = str(1024 ** 2 * 15)


@simplebot.hookimpl
def deltabot_init(bot: DeltaBot) -> None:
    getdefault(bot, "cloud", "https://0x0.st/")
    getdefault(bot, "max_size", DEF_MAX_PACK_SIZE)


@simplebot.filter
def filter_messages(bot: DeltaBot, message: Message, replies: Replies) -> None:
    """Send me an image or Telegram animated sticker and I will convert it to a Delta Chat sticker for you.

    Send me an emoji to get an sticker representing that emoji.

    Send me a text to search for sticker packs matching that text.

    Also, you can send me an URL of a Signal sticker pack, and I will send you the pack, for example, something like:
    sgnl://addstickers/?pack_id=59d338...&pack_key=56af35...
    """
    if message.chat.is_group():
        return

    if message.filemime.startswith("image/"):
        replies.add(filename=message.filename, viewtype="sticker")
    if telegram.is_sticker(message.filename):
        replies.add(filename=telegram.convert(message.filename), viewtype="sticker")
    elif signal.is_pack(message.text):
        _process_signal_pack(bot, message, replies)
    elif get_emoji_regexp().fullmatch(message.text):
        pack_url, sticker = signal.get_random_sticker(message.text)
        if pack_url:
            replies.add(
                filename=f"{message.text}.webp",
                bytefile=io.BytesIO(sticker),
                viewtype="sticker",
            )
            replies.add(text=pack_url)
        else:
            replies.add(text=f"❌ No sticker found for: {message.text!r}")
    elif message.text:
        html = signal.search_html(bot.self_contact.addr, message.text)
        if html:
            replies.add(text=f"Results for: {message.text!r}", html=html)
        else:
            replies.add(text=f"❌ No results for: {message.text!r}")


@simplebot.command
def info(payload: str, message: Message, replies: Replies) -> None:
    """Get pack info.

    Example:
    /info sgnl://addstickers/?pack_id=59d338...&pack_key=56af35...
    """
    if signal.is_pack(payload):
        text, cover = signal.get_pack_metadata(payload)
        replies.add(
            text=text, filename="cover.webp", bytefile=io.BytesIO(cover), quote=message
        )
    else:
        replies.add("❌ Unknow pack URL", quote=message)


def _process_signal_pack(bot: DeltaBot, message: Message, replies: Replies) -> None:
    title, path = signal.download_pack(bot.account.get_blobdir(), message.text)
    size = os.stat(path).st_size
    if size > int(getdefault(bot, "max_size", DEF_MAX_PACK_SIZE)):
        url = upload(bot, path)
        if url:
            replies.add(
                text=f"Name: {title}\nSize: {sizeof_fmt(size)}\nDownload: {url}",
                quote=message,
            )
        else:
            replies.add(text=f"❌ Pack too big ({sizeof_fmt(size)})", quote=message)
        os.remove(path)
    else:
        replies.add(filename=path, quote=message)
