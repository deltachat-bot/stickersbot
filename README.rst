"Stickers" SimpleBot plugin
===========================

.. image:: https://img.shields.io/pypi/v/simplebot_stickers.svg
   :target: https://pypi.org/project/simplebot_stickers

.. image:: https://img.shields.io/pypi/pyversions/simplebot_stickers.svg
   :target: https://pypi.org/project/simplebot_stickers

.. image:: https://pepy.tech/badge/simplebot_stickers
   :target: https://pepy.tech/project/simplebot_stickers

.. image:: https://img.shields.io/pypi/l/simplebot_stickers.svg
   :target: https://pypi.org/project/simplebot_stickers

.. image:: https://github.com/simplebot-org/simplebot_stickers/actions/workflows/python-ci.yml/badge.svg
   :target: https://github.com/simplebot-org/simplebot_stickers/actions/workflows/python-ci.yml

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black

`SimpleBot`_ plugin that allows users to get stickers packs and convert normal images to stickers.

To get sticker packs, browse https://signalstickers.com/ and copy the URL of the pack you want (the link in the "+ Add to Signal" button, an URL starting with ``https://signal.art/addstickers``) and send the pack URL to the bot in private, the bot will send you a zip with the sticker pack.

To create an sticker from a normal image send the image to the bot and it will send you back the image as sticker.

Install
-------

To install run::

  pip install simplebot-stickers


.. _SimpleBot: https://github.com/simplebot-org/simplebot
