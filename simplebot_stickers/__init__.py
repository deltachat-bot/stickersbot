"""Plugin's filters and commands definitions."""

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
    """Send me an image and I will convert it to sticker for you.

    Also, you can send me an URL of a Signal sticker pack, and I will send you the pack, for example, send me:
    https://signal.art/addstickers/#pack_id=59d3387717104e38a67f838e7ad0208c&pack_key=56af35841874d6fe82fa2085e8e5ed74dba5d187af007d3b4d8a3711dd722ad7
    """
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
