"""Event Hooks"""

import os
from argparse import Namespace
from tempfile import TemporaryDirectory

from cachelib import FileSystemCache
from deltabot_cli import (
    AttrDict,
    Bot,
    BotCli,
    ChatType,
    EventType,
    events,
    is_not_known_command,
)
from emoji import emoji_count

from .signal import SignalStickers
from .util import sizeof_fmt, upload

DEF_MAX_PACK_SIZE = "15"
DEF_CLOUDS = "https://ttm.sh/ https://envs.sh/ https://x0.at/ https://0x0.st/"
signal = SignalStickers()
cli = BotCli("stickersbot")


@cli.on_init
def on_init(bot: Bot, _args: Namespace) -> None:
    for accid in bot.rpc.get_all_account_ids():
        if not bot.rpc.get_config(accid, "displayname"):
            bot.rpc.set_config(accid, "displayname", "StickersBot")
            status = "I am a Delta Chat bot, send me /help for more info"
            bot.rpc.set_config(accid, "selfstatus", status)
            bot.rpc.set_config(accid, "delete_server_after", "1")


@cli.on_start
def on_start(_bot: Bot, args: Namespace) -> None:
    path = os.path.join(args.config_dir, "cache")
    if not os.path.exists(path):
        os.makedirs(path)
    signal.cache = FileSystemCache(
        path, threshold=5000, default_timeout=60 * 60 * 24 * 60
    )


@cli.on(events.RawEvent)
def log_event(bot: Bot, accid: int, event: AttrDict) -> None:
    if event.kind == EventType.INFO:
        bot.logger.info(event.msg)
    elif event.kind == EventType.WARNING:
        bot.logger.warning(event.msg)
    elif event.kind == EventType.ERROR:
        bot.logger.error(event.msg)
    elif event.kind == EventType.SECUREJOIN_INVITER_PROGRESS:
        if event.progress == 1000:
            bot.logger.debug("QR scanned by contact id=%s", event.contact_id)
            chatid = bot.rpc.create_chat_by_contact_id(accid, event.contact_id)
            send_help(bot, accid, chatid)


@cli.on(events.NewMessage(is_info=False, func=is_not_known_command))
def on_message(bot: Bot, accid: int, event: AttrDict) -> None:
    msg = event.msg
    chat = bot.rpc.get_basic_chat_info(accid, msg.chat_id)
    if chat.chat_type != ChatType.SINGLE:
        return

    bot.rpc.markseen_msgs(accid, [msg.id])

    if msg.file_mime and msg.file_mime.startswith("image/"):
        bot.rpc.send_sticker(accid, msg.chat_id, msg.file)
    elif signal.is_pack(msg.text):
        process_signal_pack(bot, accid, msg)
    elif emoji_count(msg.text):
        pack_url, sticker = signal.get_random_sticker(msg.text)
        if pack_url:
            with TemporaryDirectory() as tmp_dir:
                filename = os.path.join(tmp_dir, f"{msg.text}.webp")
                with open(filename, mode="wb") as attachment:
                    attachment.write(sticker)
                msg_id = bot.rpc.send_sticker(accid, msg.chat_id, filename)
                bot.rpc.send_msg(
                    accid, msg.chat_id, {"text": pack_url, "quotedMessageId": msg_id}
                )
        else:
            text = f"❌ No sticker found for: {msg.text!r}"
            bot.rpc.send_msg(accid, msg.chat_id, {"text": text})
    elif msg.text:
        selfaddr = bot.rpc.get_config(accid, "configured_addr")
        html = signal.search_html(selfaddr, msg.text)
        if html:
            text = f"Results for: {msg.text!r}"
            bot.rpc.send_msg(accid, msg.chat_id, {"text": text, "html": html})
        else:
            text = f"❌ No results for: {msg.text!r}"
            bot.rpc.send_msg(accid, msg.chat_id, {"text": text})


@cli.on(events.NewMessage(command="/help"))
def _help(bot: Bot, accid: int, event: AttrDict) -> None:
    send_help(bot, accid, event.msg.chat_id)


@cli.on(events.NewMessage(command="/info"))
def _info(bot: Bot, accid: int, event: AttrDict) -> None:
    msg = event.msg
    if signal.is_pack(event.payload):
        text, cover = signal.get_pack_metadata(event.payload)
        with TemporaryDirectory() as tmp_dir:
            filename = os.path.join(tmp_dir, "cover.webp")
            with open(filename, mode="wb") as attachment:
                attachment.write(cover)
            reply = {"text": text, "file": filename, "quotedMessageId": msg.id}
            bot.rpc.send_msg(accid, msg.chat_id, reply)
    else:
        reply = {"text": "❌ Unknow pack URL", "quotedMessageId": msg.id}
        bot.rpc.send_msg(accid, msg.chat_id, reply)


def process_signal_pack(bot: Bot, accid: int, msg: AttrDict) -> None:
    title, path = signal.download_pack(bot.account.get_blobdir(), msg.text)
    size = os.stat(path).st_size
    if size > 1024**2 * 15:
        url = upload(bot.logger, path)
        if url:
            text = f"Name: {title}\nSize: {sizeof_fmt(size)}\nDownload: {url}"
        else:
            text = f"❌ Pack too big ({sizeof_fmt(size)})"
        bot.rpc.send_msg(accid, msg.chat_id, {"text": text, "quotedMessageId": msg.id})
    else:
        bot.rpc.send_msg(accid, msg.chat_id, {"file": path, "quotedMessageId": msg.id})
    os.remove(path)


def send_help(bot: Bot, accid: int, chatid: int) -> None:
    lines = [
        "Send me an image and I will convert it to a Delta Chat sticker for you.\n",
        "Send me an emoji to get an sticker representing that emoji.\n",
        "Send me a text to search for sticker packs matching that text.\n",
        "Also, you can send me an URL of a Signal sticker pack, and I will send you the pack, for example, something that looks like:",
        "sgnl://addstickers/?pack_id=59d338...&pack_key=56af35..." "",
        "**Available commands**",
        "/info URL - Get more information about the sticker pack with given URL, example: /info sgnl://addstickers/?pack_id=59d338...&pack_key=56af35...",
    ]
    bot.rpc.send_msg(accid, chatid, {"text": "\n".join(lines)})
