#!/usr/bin/env python3
"""Convert a directory of full-glyph TTF files to WOFF2."""

from __future__ import annotations

import argparse
from pathlib import Path

from fontTools.ttLib import TTFont


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()

    fonts = sorted(args.source.glob("*.ttf"))
    if not fonts:
        raise SystemExit(f"no TTF files found in {args.source}")

    args.destination.mkdir(parents=True, exist_ok=True)
    for source in fonts:
        destination = args.destination / source.with_suffix(".woff2").name
        font = TTFont(source, recalcTimestamp=False)
        font.flavor = "woff2"
        font.save(destination, reorderTables=False)
        font.close()
        print(f"wrote {destination}")


if __name__ == "__main__":
    main()
