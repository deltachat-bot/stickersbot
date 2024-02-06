# StickersBot

[![Latest Release](https://img.shields.io/pypi/v/stickersbot.svg)](https://pypi.org/project/stickersbot)
[![CI](https://github.com/deltachat-bot/stickersbot/actions/workflows/python-ci.yml/badge.svg)](https://github.com/deltachat-bot/stickersbot/actions/workflows/python-ci.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Delta Chat bot that allows users to get stickers packs and convert normal images to stickers.

## Installation and configuration

```sh
pip install stickersbot
```

Configure the bot:

```sh
stickersbot init bot@example.com PASSWORD
```

Start the bot:

```sh
stickersbot serve
```

Run `stickersbot --help` to see all available options.

## Usage

To get sticker packs, browse https://signalstickers.com/ and copy the URL of the pack you want (the link in the "+ Add to Signal" button, an URL starting with ``https://signal.art/addstickers``) and send the pack URL to the bot in private, the bot will send you a zip with the sticker pack.

To create an sticker from a normal image send the image to the bot and it will send you back the image as sticker.

Send any text to the bot to search packs matching the given text.

Send an emoji to the bot to get a random sticker associated with that emoji.
