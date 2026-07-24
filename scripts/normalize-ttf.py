#!/usr/bin/env python3
"""Normalize raw TrueType glyph records before running ttfautohint."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import tempfile

from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont


def outline_digest(glyph_set, glyph_name: str) -> bytes:
    pen = RecordingPen()
    glyph_set[glyph_name].draw(pen)
    return hashlib.sha256(repr(pen.value).encode("utf-8")).digest()


def snapshot(font: TTFont) -> tuple[list[str], dict, dict, list[bytes]]:
    glyph_order = font.getGlyphOrder()
    glyph_set = font.getGlyphSet()
    outlines = [outline_digest(glyph_set, name) for name in glyph_order]
    return (
        glyph_order,
        font.getBestCmap(),
        font["hmtx"].metrics,
        outlines,
    )


def normalize(path: Path) -> None:
    original = TTFont(path, recalcBBoxes=False, recalcTimestamp=False)
    before = snapshot(original)

    # Accessing every glyph forces FontTools to decompile Iosevka's compact
    # raw glyf records. Saving then recompiles canonical, FreeType-compatible
    # records while preserving the designed outlines and metrics.
    glyf = original["glyf"]
    for glyph_name in before[0]:
        glyf[glyph_name]

    with tempfile.NamedTemporaryFile(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as temporary:
        temporary_path = Path(temporary.name)

    try:
        original.save(temporary_path, reorderTables=False)
        original.close()

        normalized = TTFont(
            temporary_path,
            recalcBBoxes=False,
            recalcTimestamp=False,
        )
        after = snapshot(normalized)
        normalized.close()

        if before != after:
            raise RuntimeError(f"normalization changed font semantics: {path}")

        os.replace(temporary_path, path)
    finally:
        original.close()
        temporary_path.unlink(missing_ok=True)

    print(f"normalized {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "directories",
        nargs="+",
        type=Path,
        help="Directories containing unhinted TTF files",
    )
    args = parser.parse_args()

    fonts = sorted(
        font
        for directory in args.directories
        for font in directory.glob("*.ttf")
    )
    if not fonts:
        raise SystemExit("no TTF files found")

    for font in fonts:
        normalize(font)


if __name__ == "__main__":
    main()
