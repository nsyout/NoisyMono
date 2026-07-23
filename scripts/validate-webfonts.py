#!/usr/bin/env python3
"""Validate curated Noisy Mono WOFF2 artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from fontTools.ttLib import TTFont

REQUIRED_CODEPOINTS = {
    0x0041: "Latin capital A",
    0x00E9: "Latin small e with acute",
    0x2192: "rightwards arrow",
    0x2500: "box drawings light horizontal",
}

REQUIRED_GSUB_FEATURES = {"calt", "dlig", "lnum", "onum", "zero"}
EXPECTED_FAMILY = "Noisy Mono"
FORBIDDEN_NAME_FRAGMENT = "Ioskeley"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("font_dir", type=Path)
    parser.add_argument("--expected-count", type=int)
    parser.add_argument("--max-bytes", type=int, default=160_000)
    args = parser.parse_args()

    font_paths = sorted(args.font_dir.glob("*.woff2"))
    if not font_paths:
        parser.error(f"no WOFF2 files found in {args.font_dir}")
    if args.expected_count is not None and len(font_paths) != args.expected_count:
        parser.error(
            f"expected {args.expected_count} WOFF2 files, found {len(font_paths)}"
        )

    for font_path in font_paths:
        size = font_path.stat().st_size
        if size > args.max_bytes:
            parser.error(
                f"{font_path.name} is {size} bytes (limit: {args.max_bytes})"
            )

        font = TTFont(font_path)
        if font.flavor != "woff2":
            parser.error(f"{font_path.name} is not WOFF2")
        if not font_path.name.startswith("NoisyMono-"):
            parser.error(f"{font_path.name} does not use the NoisyMono prefix")

        names = [record.toUnicode() for record in font["name"].names]
        if not any(EXPECTED_FAMILY in name for name in names):
            parser.error(f"{font_path.name} does not identify as {EXPECTED_FAMILY}")
        if any(FORBIDDEN_NAME_FRAGMENT in name for name in names):
            parser.error(
                f"{font_path.name} still contains the former family name"
            )

        cmap = font.getBestCmap()
        for codepoint, label in REQUIRED_CODEPOINTS.items():
            if codepoint not in cmap:
                parser.error(f"{font_path.name} is missing {label} (U+{codepoint:04X})")

        if "GSUB" not in font or font["GSUB"].table.FeatureList is None:
            parser.error(f"{font_path.name} has no GSUB feature list")
        feature_tags = {
            record.FeatureTag
            for record in font["GSUB"].table.FeatureList.FeatureRecord
        }
        missing_features = REQUIRED_GSUB_FEATURES - feature_tags
        if missing_features:
            parser.error(
                f"{font_path.name} is missing GSUB features: "
                f"{', '.join(sorted(missing_features))}"
            )

    total_bytes = sum(path.stat().st_size for path in font_paths)
    print(f"Validated {len(font_paths)} WOFF2 fonts ({total_bytes} bytes total)")


if __name__ == "__main__":
    main()
