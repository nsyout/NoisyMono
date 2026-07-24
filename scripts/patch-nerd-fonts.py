#!/usr/bin/env python3
"""Patch the complete Noisy Mono family matrix with Nerd Font glyphs."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


FAMILIES = {
    "NoisyMono": "patched-fonts",
    "NoisyMonoTerm": "patched-fonts-term",
    "NoisyMonoNL": "patched-fonts-nl",
}
WIDTHS = ("Normal", "SemiCondensed", "Condensed")
EXPECTED_PER_WIDTH = 20
FONTFORGE_PYTHON_ENVIRONMENT = (
    "LD_LIBRARY_PATH",
    "PYTHONHOME",
    "PYTHONPATH",
)


def width_for(filename: str) -> str:
    if "SemiCondensed" in filename:
        return "SemiCondensed"
    if "Condensed" in filename:
        return "Condensed"
    return "Normal"


def clean_fontforge_environment(environment: dict[str, str]) -> dict[str, str]:
    """Remove caller-specific Python settings from FontForge's environment."""
    cleaned = environment.copy()
    for variable in FONTFORGE_PYTHON_ENVIRONMENT:
        cleaned.pop(variable, None)
    return cleaned


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("iosevka_root", type=Path)
    parser.add_argument("patcher", type=Path)
    parser.add_argument("output_root", type=Path)
    parser.add_argument(
        "--fontforge",
        default="fontforge",
        help="FontForge executable or path (default: fontforge)",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=2,
        help="Concurrent FontForge processes (default: 2)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reuse complete width groups and rebuild partial groups",
    )
    args = parser.parse_args()
    if args.jobs < 1:
        raise SystemExit("--jobs must be at least 1")

    executable = shutil.which(args.fontforge)
    if executable is None:
        raise SystemExit(f"FontForge executable not found: {args.fontforge}")
    if not args.patcher.is_file():
        raise SystemExit(f"Nerd Fonts patcher not found: {args.patcher}")

    # FontForge embeds the Python runtime supplied by its own installation.
    # actions/setup-python exports LD_LIBRARY_PATH for its hosted runtime, which
    # can make Ubuntu's FontForge combine that runtime with the system stdlib.
    # Keep caller-specific Python configuration out of every FontForge child.
    fontforge_environment = clean_fontforge_environment(dict(os.environ))

    for family, output_name in FAMILIES.items():
        source = args.iosevka_root / "dist" / family / "TTF"
        fonts = sorted(source.glob(f"{family}-*.ttf"))
        if len(fonts) != EXPECTED_PER_WIDTH * len(WIDTHS):
            raise SystemExit(
                f"{family}: expected 60 hinted TTFs, found {len(fonts)}"
            )

        output = args.output_root / output_name
        for width in WIDTHS:
            destination = output / width
            destination.mkdir(parents=True, exist_ok=True)
            existing = list(destination.glob("*.ttf"))
            if args.resume and len(existing) == EXPECTED_PER_WIDTH:
                print(f"already patched {family} {width}: 20 faces")
                continue
            if existing and not args.resume:
                raise SystemExit(
                    f"{family} {width}: output is not empty; "
                    "use an empty root or pass --resume"
                )
            if args.resume and len(existing) > EXPECTED_PER_WIDTH:
                raise SystemExit(
                    f"{family} {width}: found {len(existing)} existing faces"
                )
            width_fonts = [
                font for font in fonts if width_for(font.name) == width
            ]
            if len(width_fonts) != EXPECTED_PER_WIDTH:
                raise SystemExit(
                    f"{family} {width}: expected {EXPECTED_PER_WIDTH} faces, "
                    f"found {len(width_fonts)}"
                )

            def patch(font: Path) -> None:
                command = [
                    executable,
                    "-script",
                    str(args.patcher),
                    str(font),
                    "--complete",
                    "--careful",
                    "--mono",
                    "--outputdir",
                    str(destination),
                ]
                with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as log:
                    result = subprocess.run(
                        command,
                        env=fontforge_environment,
                        stdout=log,
                        stderr=subprocess.STDOUT,
                    )
                    if result.returncode != 0:
                        log.seek(0)
                        print(log.read())
                        raise SystemExit(
                            f"Nerd Fonts patcher failed for {font}"
                        )
                print(f"patched {font.name}")

            with ThreadPoolExecutor(max_workers=args.jobs) as executor:
                list(executor.map(patch, width_fonts))

            patched = list(destination.glob("*.ttf"))
            if len(patched) != EXPECTED_PER_WIDTH:
                raise SystemExit(
                    f"{family} {width}: patcher produced {len(patched)} faces"
                )
            print(f"patched {family} {width}: {len(patched)} faces")


if __name__ == "__main__":
    main()
