#!/usr/bin/env python3
"""Validate the complete Iosevka output matrix before packaging."""

from __future__ import annotations

import argparse
from pathlib import Path


FAMILIES = ("NoisyMono", "NoisyMonoTerm", "NoisyMonoNL")
EXPECTED_FACES = 60


def stems(directory: Path, suffix: str) -> set[str]:
    if not directory.is_dir():
        raise ValueError(f"missing build directory: {directory}")
    return {path.stem for path in directory.glob(f"*{suffix}")}


def expect_count(label: str, values: set[str]) -> None:
    if len(values) != EXPECTED_FACES:
        raise ValueError(
            f"{label}: expected {EXPECTED_FACES} faces, found {len(values)}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("iosevka_root", type=Path)
    args = parser.parse_args()

    for family in FAMILIES:
        family_root = args.iosevka_root / "dist" / family
        unhinted = stems(family_root / "TTF-Unhinted", ".ttf")
        hinted = stems(family_root / "TTF", ".ttf")
        controls = {
            path.name.removesuffix(".ttfa.txt")
            for path in (
                args.iosevka_root / ".build" / "TTF" / family
            ).glob("*.ttfa.txt")
        }

        expect_count(f"{family} unhinted TTF", unhinted)
        expect_count(f"{family} hinted TTF", hinted)
        expect_count(f"{family} hinting controls", controls)
        if unhinted != hinted or unhinted != controls:
            raise ValueError(
                f"{family}: hinted, unhinted, and control face sets differ"
            )

    noisy_root = args.iosevka_root / "dist" / "NoisyMono"
    ttf_stems = stems(noisy_root / "TTF", ".ttf")
    for directory_name in ("WOFF2", "WOFF2-Unhinted"):
        web_stems = stems(noisy_root / directory_name, ".woff2")
        expect_count(f"NoisyMono {directory_name}", web_stems)
        if web_stems != ttf_stems:
            raise ValueError(
                f"NoisyMono {directory_name}: face set differs from TTF"
            )

    print("validated 180 hinted and unhinted TTF faces")
    print("validated 120 full-glyph WOFF2 faces")


if __name__ == "__main__":
    main()
