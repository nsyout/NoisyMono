#!/usr/bin/env python3
"""Sync the showcase with a validated NoisyMono-Web candidate."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parents[1]
SITE_FONT_DIR = ROOT / "site/fonts"
SITE_FONT_CSS = ROOT / "site/css/fonts.css"
SITE_MAIN_CSS = ROOT / "site/css/main.css"
SITE_INDEX = ROOT / "site/index.html"
VALIDATOR = ROOT / "scripts/validate-webfonts.py"
CSS_GENERATOR = ROOT / "scripts/generate-webfont-css.py"
TOOLCHAIN = ROOT / ".github/font-toolchain.json"


def font_versions(font_dir: Path) -> set[str]:
    versions = set()
    for font_path in font_dir.glob("*.woff2"):
        font = TTFont(font_path, lazy=True)
        try:
            versions.update(
                record.toUnicode()
                for record in font["name"].names
                if record.nameID == 5
            )
        finally:
            font.close()
    return versions


def validate(font_dir: Path) -> str:
    subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            str(font_dir),
            "--expected-count",
            "60",
        ],
        check=True,
    )

    pinned = json.loads(TOOLCHAIN.read_text(encoding="utf-8"))["iosevka"]["tag"]
    expected_version = f"Version {pinned.removeprefix('v')}"
    versions = font_versions(font_dir)
    if versions != {expected_version}:
        raise RuntimeError(
            f"site candidate version mismatch: expected {expected_version!r}, "
            f"found {sorted(versions)!r}"
        )
    return expected_version


def generate_css(font_dir: Path, destination: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            str(CSS_GENERATOR),
            str(font_dir),
            str(destination),
            "--url-prefix",
            "../fonts",
        ],
        check=True,
    )


def check() -> None:
    version = validate(SITE_FONT_DIR)
    with tempfile.TemporaryDirectory(prefix="noisy-mono-site-css-") as temp_dir:
        generated = Path(temp_dir) / "fonts.css"
        generate_css(SITE_FONT_DIR, generated)
        if not SITE_FONT_CSS.is_file():
            raise RuntimeError(f"missing generated stylesheet: {SITE_FONT_CSS}")
        if generated.read_bytes() != SITE_FONT_CSS.read_bytes():
            raise RuntimeError(
                "site/css/fonts.css is stale; rerun sync-site-webfonts.py"
            )
    index_html = SITE_INDEX.read_text(encoding="utf-8")
    if 'href="css/fonts.css"' not in index_html:
        raise RuntimeError("site/index.html does not load css/fonts.css")
    main_css = SITE_MAIN_CSS.read_text(encoding="utf-8")
    if "@font-face" in main_css:
        raise RuntimeError(
            "site/css/main.css contains legacy @font-face declarations"
        )
    print(f"Showcase webfonts are current ({version})")


def sync(source_dir: Path) -> None:
    source_dir = source_dir.resolve()
    if source_dir == SITE_FONT_DIR.resolve():
        raise RuntimeError("source and destination font directories are identical")

    version = validate(source_dir)
    SITE_FONT_DIR.mkdir(parents=True, exist_ok=True)

    source_names = {path.name for path in source_dir.glob("*.woff2")}
    for old_font in SITE_FONT_DIR.glob("*.woff2"):
        if old_font.name not in source_names:
            old_font.unlink()
    for source_font in source_dir.glob("*.woff2"):
        shutil.copyfile(source_font, SITE_FONT_DIR / source_font.name)

    generate_css(SITE_FONT_DIR, SITE_FONT_CSS)
    check()
    print(f"Synced showcase webfonts from {source_dir} ({version})")


def main() -> None:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument(
        "--from",
        dest="source_dir",
        type=Path,
        help="Font directory extracted from NoisyMono-Web.zip.",
    )
    action.add_argument(
        "--check",
        action="store_true",
        help="Validate the tracked site fonts and generated CSS.",
    )
    args = parser.parse_args()

    if args.check:
        check()
    else:
        sync(args.source_dir)


if __name__ == "__main__":
    main()
