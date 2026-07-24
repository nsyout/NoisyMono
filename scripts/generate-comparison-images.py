#!/usr/bin/env python3
"""Render honest, like-for-like Noisy Mono and Berkeley Mono specimens."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parents[1]
NOISY_WOFF2 = ROOT / "site/fonts/NoisyMono-Regular.woff2"
SWIFT_RENDERER = ROOT / "scripts/render-comparison.swift"


def font_names(path: Path) -> dict[str, str]:
    font = TTFont(path)
    names = font["name"]

    def first(name_id: int) -> str:
        for record in names.names:
            if record.nameID == name_id:
                return record.toUnicode()
        raise RuntimeError(f"{path} has no name table entry {name_id}")

    return {
        "family": first(1),
        "fullName": first(4),
        "version": first(5),
        "postScriptName": first(6),
    }


def render(font_path: Path, postscript_name: str, output_path: Path) -> None:
    environment = os.environ.copy()
    sdk = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
    if sdk.is_dir():
        environment["SDKROOT"] = str(sdk)
    environment["SWIFT_MODULECACHE_PATH"] = "/private/tmp/noisy-mono-swift-cache"
    environment["CLANG_MODULE_CACHE_PATH"] = "/private/tmp/noisy-mono-clang-cache"
    subprocess.run(
        [
            "swift",
            str(SWIFT_RENDERER),
            str(font_path),
            postscript_name,
            str(output_path),
        ],
        check=True,
        env=environment,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--berkeley",
        type=Path,
        required=True,
        help="Path to a locally licensed BerkeleyMono-Regular TTF.",
    )
    args = parser.parse_args()
    berkeley_path = args.berkeley.expanduser().resolve()

    if not berkeley_path.is_file():
        parser.error(f"Berkeley font not found: {berkeley_path}")

    noisy_metadata = font_names(NOISY_WOFF2)
    berkeley_metadata = font_names(berkeley_path)

    if noisy_metadata["family"] != "Noisy Mono":
        raise RuntimeError(f"unexpected Noisy family: {noisy_metadata['family']}")
    if berkeley_metadata["family"] != "Berkeley Mono":
        raise RuntimeError(
            f"expected Berkeley Mono, found {berkeley_metadata['family']}"
        )

    with tempfile.TemporaryDirectory(prefix="noisy-mono-specimen-") as temp_dir:
        temp = Path(temp_dir)
        noisy_ttf = temp / "NoisyMono-Regular.ttf"
        noisy_font = TTFont(NOISY_WOFF2)
        noisy_font.flavor = None
        noisy_font.save(noisy_ttf)

        outputs = {
            "NoisyMono.png": (
                noisy_ttf,
                noisy_metadata["postScriptName"],
            ),
            "BerkeleyMono.png": (
                berkeley_path,
                berkeley_metadata["postScriptName"],
            ),
        }

        for filename, (font_path, postscript_name) in outputs.items():
            rendered = temp / filename
            render(font_path, postscript_name, rendered)
            shutil.copyfile(rendered, ROOT / "site/imgs" / filename)
            shutil.copyfile(rendered, ROOT / "assets" / filename)

    provenance = {
        "canvas": {"width": 1364, "height": 984},
        "fonts": {
            "BerkeleyMono.png": berkeley_metadata,
            "NoisyMono.png": noisy_metadata,
        },
        "fontSettings": "Regular weight with each font's default OpenType features",
        "palette": "Flexoki Dark",
        "renderer": "macOS Core Text",
        "source": "scripts/render-comparison.swift",
    }
    (ROOT / "site/imgs/comparison-provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
