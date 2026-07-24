#!/usr/bin/env python3
"""Create the seven non-curated Noisy Mono release archives."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import time
import zipfile


WIDTHS = ("Normal", "SemiCondensed", "Condensed")
EXPECTED_PER_WIDTH = 20


@dataclass(frozen=True)
class Member:
    source: Path
    archive_path: str


def width_for(filename: str) -> str:
    if "SemiCondensed" in filename:
        return "SemiCondensed"
    if "Condensed" in filename:
        return "Condensed"
    return "Normal"


def family_members(
    iosevka_root: Path,
    family: str,
) -> list[Member]:
    members: list[Member] = []
    for hinting, directory_name in (
        ("Hinted", "TTF"),
        ("Unhinted", "TTF-Unhinted"),
    ):
        directory = iosevka_root / "dist" / family / directory_name
        fonts = sorted(directory.glob(f"{family}-*.ttf"))
        if len(fonts) != EXPECTED_PER_WIDTH * len(WIDTHS):
            raise ValueError(
                f"{family} {hinting}: expected 60 faces, found {len(fonts)}"
            )
        members.extend(
            Member(font, f"{width_for(font.name)}/{hinting}/{font.name}")
            for font in fonts
        )
    return members


def nerd_members(patched_root: Path, directory_name: str) -> list[Member]:
    members: list[Member] = []
    for width in WIDTHS:
        directory = patched_root / directory_name / width
        fonts = sorted(directory.glob("*.ttf"))
        if len(fonts) != EXPECTED_PER_WIDTH:
            raise ValueError(
                f"{directory_name} {width}: expected 20 faces, "
                f"found {len(fonts)}"
            )
        members.extend(
            Member(font, f"{width}/{font.name}") for font in fonts
        )
    return members


def full_web_members(iosevka_root: Path) -> list[Member]:
    members: list[Member] = []
    for directory_name in ("WOFF2", "WOFF2-Unhinted"):
        directory = iosevka_root / "dist" / "NoisyMono" / directory_name
        fonts = sorted(directory.glob("*.woff2"))
        if len(fonts) != EXPECTED_PER_WIDTH * len(WIDTHS):
            raise ValueError(
                f"{directory_name}: expected 60 faces, found {len(fonts)}"
            )
        members.extend(
            Member(font, f"{directory_name}/{font.name}") for font in fonts
        )
    return members


def write_archive(
    destination: Path,
    members: list[Member],
    timestamp: tuple[int, ...],
) -> None:
    seen: set[str] = set()
    with zipfile.ZipFile(
        destination,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for member in sorted(members, key=lambda item: item.archive_path):
            if member.archive_path in seen:
                raise ValueError(
                    f"duplicate archive path: {member.archive_path}"
                )
            seen.add(member.archive_path)

            info = zipfile.ZipInfo(member.archive_path, timestamp[:6])
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, member.source.read_bytes())
    print(f"wrote {destination}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("iosevka_root", type=Path)
    parser.add_argument("patched_root", type=Path)
    parser.add_argument("output_root", type=Path)
    parser.add_argument("--source-date-epoch", type=int, required=True)
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
    )
    args = parser.parse_args()

    timestamp = time.gmtime(args.source_date_epoch)
    if timestamp.tm_year < 1980:
        raise SystemExit("SOURCE_DATE_EPOCH must be representable in ZIP")
    args.output_root.mkdir(parents=True, exist_ok=True)

    common = [
        Member(args.repository_root / "LICENSE", "LICENSE"),
        Member(args.repository_root / "FONTLOG.txt", "FONTLOG.txt"),
    ]
    archives = {
        "NoisyMono.zip": family_members(args.iosevka_root, "NoisyMono"),
        "NoisyMono-Term.zip": family_members(
            args.iosevka_root, "NoisyMonoTerm"
        ),
        "NoisyMono-NL.zip": family_members(
            args.iosevka_root, "NoisyMonoNL"
        ),
        "NoisyMono-NerdFont.zip": nerd_members(
            args.patched_root, "patched-fonts"
        ),
        "NoisyMono-Term-NerdFont.zip": nerd_members(
            args.patched_root, "patched-fonts-term"
        ),
        "NoisyMono-NL-NerdFont.zip": nerd_members(
            args.patched_root, "patched-fonts-nl"
        ),
        "NoisyMono-Web-Full.zip": full_web_members(args.iosevka_root),
    }
    for archive_name, members in archives.items():
        write_archive(
            args.output_root / archive_name,
            members + common,
            timestamp,
        )


if __name__ == "__main__":
    main()
