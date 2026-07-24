#!/usr/bin/env python3
"""Hint normalized Noisy Mono TTFs with Iosevka's control files."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess


FAMILIES = ("NoisyMono", "NoisyMonoTerm", "NoisyMonoNL")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "iosevka_root",
        type=Path,
        help="Iosevka checkout containing .build and dist",
    )
    parser.add_argument(
        "--ttfautohint",
        default="ttfautohint",
        help="ttfautohint executable or path (default: ttfautohint)",
    )
    parser.add_argument(
        "--family",
        action="append",
        choices=FAMILIES,
        dest="families",
        help="Family to hint; repeat as needed (default: all families)",
    )
    args = parser.parse_args()

    executable = shutil.which(args.ttfautohint)
    if executable is None:
        raise SystemExit(f"ttfautohint executable not found: {args.ttfautohint}")

    for family in args.families or FAMILIES:
        unhinted = args.iosevka_root / "dist" / family / "TTF-Unhinted"
        hinted = args.iosevka_root / "dist" / family / "TTF"
        controls = args.iosevka_root / ".build" / "TTF" / family
        fonts = sorted(unhinted.glob("*.ttf"))
        if not fonts:
            raise SystemExit(f"no TTF files found in {unhinted}")

        hinted.mkdir(parents=True, exist_ok=True)
        for font in fonts:
            control = controls / f"{font.stem}.ttfa.txt"
            if not control.is_file():
                raise SystemExit(f"missing hinting control file: {control}")
            destination = hinted / font.name
            subprocess.run(
                [
                    executable,
                    "-m",
                    str(control),
                    str(font),
                    str(destination),
                ],
                check=True,
            )
            print(f"hinted {destination}")


if __name__ == "__main__":
    main()
