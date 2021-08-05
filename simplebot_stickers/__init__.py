import os
import zipfile
from tempfile import NamedTemporaryFile
from urllib.parse import quote

import simplebot
from deltachat import Message
from emoji import demojize
from pkg_resources import DistributionNotFound, get_distribution
from simplebot.bot import Replies

from simplebot_stickers import signal

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    __version__ = "0.0.0.dev0-unknown"


@simplebot.filter
def filter_messages(message, replies, bot) -> None:
    """Process messages with sticker packs URL or images."""
    if not message.chat.is_group():
        if message.filemime.startswith("image/"):
            replies.add(filename=message.filename, viewtype="sticker")
        if signal.is_pack(message.text):
            pack_name, stickers = signal.get_stickers(message.text)
            pack_name = quote(pack_name, safe="")
            with NamedTemporaryFile(
                dir=bot.account.get_blobdir(),
                prefix=pack_name + "-",
                suffix=".stickers.zip",
                delete=False,
            ) as file:
                zip_path = file.name
            with zipfile.ZipFile(
                zip_path, "w", compression=zipfile.ZIP_DEFLATED
            ) as zfile:
                for sticker in stickers:
                    name = "{}.{}+{}.webp".format(
                        sticker.id,
                        demojize(sticker.emoji, delimiters=("", "")),
                        sticker.emoji,
                    )
                    name = os.path.join(pack_name, name)
                    zfile.writestr(name, sticker.image_data)
            replies.add(filename=zip_path, quote=message)


@simplebot.command
def sticker(message: Message, replies: Replies) -> None:
    """Send attached or quoted image as sticker."""
    file = None
    if message.filemime.startswith("image/"):
        file = message.filename
    elif message.quote and message.quote.filemime.startswith("image/"):
        file = message.quote.filename
    if file:
        replies.add(filename=file, viewtype="sticker")
