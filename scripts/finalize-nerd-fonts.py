#!/usr/bin/env python3
"""Normalize and validate fixed-pitch metadata on patched Nerd Fonts."""

from __future__ import annotations

import argparse
from pathlib import Path

from fontTools.ttLib import TTFont


def finalize(font_path: Path) -> None:
    font = TTFont(font_path)
    changed = False

    if font["post"].isFixedPitch != 1:
        font["post"].isFixedPitch = 1
        changed = True

    if font["OS/2"].panose.bProportion != 9:
        font["OS/2"].panose.bProportion = 9
        changed = True

    if changed:
        font.save(font_path)
        font = TTFont(font_path)

    nonzero_widths = {
        font["hmtx"].metrics[glyph_name][0]
        for glyph_name in font.getGlyphOrder()
        if font["hmtx"].metrics[glyph_name][0] != 0
    }
    if len(nonzero_widths) != 1:
        widths = ", ".join(str(width) for width in sorted(nonzero_widths))
        raise ValueError(
            f"{font_path} is not strictly monospaced; advance widths: {widths}"
        )
    if font["post"].isFixedPitch != 1:
        raise ValueError(f"{font_path} does not set post.isFixedPitch")
    if font["OS/2"].panose.bProportion != 9:
        raise ValueError(f"{font_path} does not set monospaced Panose proportion")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directories", nargs="+", type=Path)
    args = parser.parse_args()

    font_paths = sorted(
        font_path
        for directory in args.directories
        for font_path in directory.rglob("*.ttf")
    )
    if not font_paths:
        parser.error("no TTF files found")

    for font_path in font_paths:
        finalize(font_path)

    print(f"Finalized and validated {len(font_paths)} monospaced Nerd Fonts")


if __name__ == "__main__":
    main()
