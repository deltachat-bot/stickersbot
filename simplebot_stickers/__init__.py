"""Plugin's filters and commands definitions."""

import io
import os

import simplebot
from deltachat import Message
from emoji import get_emoji_regexp
from pkg_resources import DistributionNotFound, get_distribution
from simplebot.bot import DeltaBot, Replies

from . import signal

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    __version__ = "0.0.0.dev0-unknown"


@simplebot.filter
def filter_messages(bot: DeltaBot, message: Message, replies: Replies) -> None:
    """Send me an image and I will convert it to sticker for you.

    Send me an emoji to get an sticker representing that emoji.

    Send me a text to search for sticker packs matching that text.

    Also, you can send me an URL of a Signal sticker pack, and I will send you the pack, for example, send me:
    sgnl://addstickers/?pack_id=59d3387717104e38a67f838e7ad0208c&pack_key=56af35841874d6fe82fa2085e8e5ed74dba5d187af007d3b4d8a3711dd722ad7
    """
    if message.chat.is_group():
        return

    if message.filemime.startswith("image/"):
        replies.add(filename=message.filename, viewtype="sticker")
    elif signal.is_pack(message.text):
        path = signal.download_pack(bot.account.get_blobdir(), message.text)
        name = os.path.basename(path)
        with open(path, "rb") as file:
            replies.add(filename=name, bytefile=io.BytesIO(file.read()), quote=message)
        os.remove(path)
    elif get_emoji_regexp().fullmatch(message.text):
        pack_url, sticker = signal.get_random_sticker(message.text)
        if pack_url:
            replies.add(
                text=pack_url,
                filename=f"{message.text}.webp",
                bytefile=io.BytesIO(sticker),
                viewtype="sticker",
            )
        else:
            replies.add(text=f"❌ No sticker found for: {message.text!r}")
    elif message.text:
        html = signal.search_html(bot.self_contact.addr, message.text)
        if html:
            replies.add(text=f"Results for: {message.text!r}", html=html)
        else:
            replies.add(text=f"❌ No results for: {message.text!r}")
