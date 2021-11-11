"""Telegram sticker tools"""

import os
from tempfile import NamedTemporaryFile

from lottie.exporters import exporters
from lottie.importers import importers
from lottie.utils.stripper import float_strip


def convert(path: str) -> str:
    prefix = os.path.join(os.path.dirname(path), "sticker")
    with NamedTemporaryFile(prefix=prefix, suffix=".webp", delete=False) as file:
        outpath = file.name
    anim = importers["lottie"].process(path)
    float_strip(anim)
    exporters["webp"].process(
        anim, outpath, lossless=False, method=0, quality=40, skip_frames=10
    )
    return outpath


def is_sticker(path: str) -> bool:
    return path.endswith((".json", ".tgs"))
