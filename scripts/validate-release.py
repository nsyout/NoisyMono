#!/usr/bin/env python3
"""Validate every archive in a Noisy Mono release candidate."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import stat
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from fontTools.ttLib import TTFont


WEIGHTS = {100, 200, 300, 350, 400, 500, 600, 700, 800, 900}
WIDTH_CLASSES = {
    "Normal": 5,
    "SemiCondensed": 4,
    "Condensed": 3,
}
REQUIRED_CODEPOINTS = {
    0x0030: "digit zero",
    0x0041: "Latin capital A",
    0x0067: "Latin small g",
    0x00E9: "Latin small e with acute",
    0x2192: "rightwards arrow",
    0x2500: "box drawings light horizontal",
}
LIGATION_FEATURES = {"calt", "dlig", "liga"}
VERSION_PATTERN = re.compile(r"^v\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")


@dataclass(frozen=True)
class ArchiveRule:
    groups: dict[str, int]
    suffix: str
    family_fragment: str
    feature_mode: str
    strictly_monospaced: bool = False
    extra_files: frozenset[str] = frozenset({"LICENSE", "FONTLOG.txt"})


ARCHIVES = {
    "NoisyMono.zip": ArchiveRule(
        groups={
            f"{width}/{hinting}/": 20
            for width in WIDTH_CLASSES
            for hinting in ("Hinted", "Unhinted")
        },
        suffix=".ttf",
        family_fragment="Noisy Mono",
        feature_mode="standard",
    ),
    "NoisyMono-NerdFont.zip": ArchiveRule(
        groups={f"{width}/": 20 for width in WIDTH_CLASSES},
        suffix=".ttf",
        family_fragment="Noisy",
        feature_mode="standard",
        strictly_monospaced=True,
    ),
    "NoisyMono-Term.zip": ArchiveRule(
        groups={
            f"{width}/{hinting}/": 20
            for width in WIDTH_CLASSES
            for hinting in ("Hinted", "Unhinted")
        },
        suffix=".ttf",
        family_fragment="Noisy Mono Term",
        feature_mode="standard",
        strictly_monospaced=True,
    ),
    "NoisyMono-Term-NerdFont.zip": ArchiveRule(
        groups={f"{width}/": 20 for width in WIDTH_CLASSES},
        suffix=".ttf",
        family_fragment="Noisy",
        feature_mode="standard",
        strictly_monospaced=True,
    ),
    "NoisyMono-NL.zip": ArchiveRule(
        groups={
            f"{width}/{hinting}/": 20
            for width in WIDTH_CLASSES
            for hinting in ("Hinted", "Unhinted")
        },
        suffix=".ttf",
        family_fragment="Noisy Mono NL",
        feature_mode="no-ligatures",
    ),
    "NoisyMono-NL-NerdFont.zip": ArchiveRule(
        groups={f"{width}/": 20 for width in WIDTH_CLASSES},
        suffix=".ttf",
        family_fragment="Noisy",
        feature_mode="no-ligatures",
        strictly_monospaced=True,
    ),
    "NoisyMono-Web.zip": ArchiveRule(
        groups={"fonts/": 60},
        suffix=".woff2",
        family_fragment="Noisy Mono",
        feature_mode="standard",
        extra_files=frozenset(
            {"LICENSE", "FONTLOG.txt", "README.md", "noisy-mono.css"}
        ),
    ),
    "NoisyMono-Web-Full.zip": ArchiveRule(
        groups={"WOFF2/": 60, "WOFF2-Unhinted/": 60},
        suffix=".woff2",
        family_fragment="Noisy Mono",
        feature_mode="standard",
    ),
}


def fail(message: str) -> None:
    raise ValueError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def names(font: TTFont, name_id: int) -> set[str]:
    values = set()
    for record in font["name"].names:
        if record.nameID == name_id:
            try:
                values.add(record.toUnicode())
            except UnicodeDecodeError:
                continue
    return values


def feature_tags(font: TTFont) -> set[str]:
    if "GSUB" not in font or font["GSUB"].table.FeatureList is None:
        return set()
    return {
        record.FeatureTag
        for record in font["GSUB"].table.FeatureList.FeatureRecord
    }


def face_key(font: TTFont) -> tuple[int, int, bool]:
    os2 = font["OS/2"]
    italic = bool(os2.fsSelection & 0x01)
    return os2.usWidthClass, os2.usWeightClass, italic


def validate_font(
    archive_name: str,
    member_name: str,
    data: bytes,
    rule: ArchiveRule,
) -> tuple[tuple[int, int, bool], set[str], set[str]]:
    font = TTFont(io.BytesIO(data), lazy=True)
    try:
        if rule.suffix == ".woff2" and font.flavor != "woff2":
            fail(f"{archive_name}:{member_name} is not WOFF2")
        if rule.suffix == ".ttf" and font.flavor is not None:
            fail(f"{archive_name}:{member_name} is not a plain sfnt font")

        all_names = {
            value
            for name_id in (1, 2, 4, 5, 6, 16, 17)
            for value in names(font, name_id)
        }
        joined_names = " | ".join(sorted(all_names))
        if rule.family_fragment not in joined_names:
            fail(
                f"{archive_name}:{member_name} does not identify as "
                f"{rule.family_fragment}"
            )
        if "Ioskeley" in joined_names:
            fail(f"{archive_name}:{member_name} contains the former family name")
        if "NerdFont" in archive_name and "Nerd Font" not in joined_names:
            fail(f"{archive_name}:{member_name} lacks Nerd Font naming")

        key = face_key(font)
        width_class, weight, _ = key
        if width_class not in WIDTH_CLASSES.values():
            fail(
                f"{archive_name}:{member_name} has unexpected width class "
                f"{width_class}"
            )
        if weight not in WEIGHTS:
            fail(f"{archive_name}:{member_name} has unexpected weight {weight}")

        cmap = font.getBestCmap() or {}
        for codepoint, label in REQUIRED_CODEPOINTS.items():
            if codepoint not in cmap:
                fail(
                    f"{archive_name}:{member_name} is missing {label} "
                    f"(U+{codepoint:04X})"
                )

        tags = feature_tags(font)
        if rule.feature_mode == "standard" and "calt" not in tags:
            fail(f"{archive_name}:{member_name} is missing default ligatures")
        if rule.feature_mode == "no-ligatures":
            unexpected = tags & LIGATION_FEATURES
            if unexpected:
                fail(
                    f"{archive_name}:{member_name} unexpectedly contains "
                    f"ligature features: {', '.join(sorted(unexpected))}"
                )

        ascii_glyphs = {
            cmap[codepoint]
            for codepoint in range(0x21, 0x7F)
            if codepoint in cmap
        }
        ascii_widths = {
            font["hmtx"].metrics[glyph_name][0]
            for glyph_name in ascii_glyphs
        }
        if len(ascii_widths) != 1:
            fail(
                f"{archive_name}:{member_name} has multiple printable ASCII "
                f"advance widths: {sorted(ascii_widths)}"
            )

        if rule.strictly_monospaced:
            nonzero_widths = {
                advance
                for advance, _ in font["hmtx"].metrics.values()
                if advance != 0
            }
            if len(nonzero_widths) != 1:
                fail(
                    f"{archive_name}:{member_name} is not strictly monospaced; "
                    f"advance widths: {sorted(nonzero_widths)}"
                )
            if font["post"].isFixedPitch != 1:
                fail(f"{archive_name}:{member_name} does not set isFixedPitch")
            if font["OS/2"].panose.bProportion != 9:
                fail(
                    f"{archive_name}:{member_name} does not set monospaced Panose"
                )

        return key, names(font, 5), names(font, 6)
    finally:
        font.close()


def group_for(member_name: str, groups: dict[str, int]) -> str | None:
    matches = [prefix for prefix in groups if member_name.startswith(prefix)]
    if len(matches) != 1:
        return None
    return matches[0]


def validate_archive(path: Path, rule: ArchiveRule) -> dict[str, object]:
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        member_names = [info.filename for info in infos]
        if len(member_names) != len(set(member_names)):
            fail(f"{path.name} contains duplicate member names")

        files = []
        for info in infos:
            member = PurePosixPath(info.filename)
            if member.is_absolute() or ".." in member.parts:
                fail(f"{path.name} contains unsafe path {info.filename}")
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                fail(f"{path.name} contains symlink {info.filename}")
            if not info.is_dir():
                files.append(info.filename)

        font_members = sorted(
            name for name in files if name.endswith(rule.suffix)
        )
        expected_font_count = sum(rule.groups.values())
        if len(font_members) != expected_font_count:
            fail(
                f"{path.name} contains {len(font_members)} fonts; "
                f"expected {expected_font_count}"
            )

        non_font_files = set(files) - set(font_members)
        if non_font_files != set(rule.extra_files):
            fail(
                f"{path.name} non-font files differ: "
                f"expected {sorted(rule.extra_files)}, "
                f"found {sorted(non_font_files)}"
            )

        members_by_group: dict[str, list[str]] = {
            prefix: [] for prefix in rule.groups
        }
        for member_name in font_members:
            group = group_for(member_name, rule.groups)
            if group is None:
                fail(f"{path.name} has font outside its package layout: {member_name}")
            members_by_group[group].append(member_name)

        versions: set[str] = set()
        postscript_names: set[str] = set()
        for group, expected_count in rule.groups.items():
            members = members_by_group[group]
            if len(members) != expected_count:
                fail(
                    f"{path.name}:{group} contains {len(members)} fonts; "
                    f"expected {expected_count}"
                )

            keys = set()
            for member_name in members:
                key, font_versions, font_postscript_names = validate_font(
                    path.name,
                    member_name,
                    archive.read(member_name),
                    rule,
                )
                if key in keys:
                    fail(f"{path.name}:{group} duplicates face {key}")
                keys.add(key)
                versions.update(font_versions)
                postscript_names.update(font_postscript_names)

            group_width = PurePosixPath(group).parts[0]
            if group_width in WIDTH_CLASSES:
                expected_width = WIDTH_CLASSES[group_width]
                if {key[0] for key in keys} != {expected_width}:
                    fail(
                        f"{path.name}:{group} does not use width class "
                        f"{expected_width}"
                    )
                combinations = {(key[1], key[2]) for key in keys}
                expected_combinations = {
                    (weight, italic)
                    for weight in WEIGHTS
                    for italic in (False, True)
                }
                if combinations != expected_combinations:
                    fail(f"{path.name}:{group} has incomplete weight/style coverage")
            else:
                expected_keys = {
                    (width, weight, italic)
                    for width in WIDTH_CLASSES.values()
                    for weight in WEIGHTS
                    for italic in (False, True)
                }
                if keys != expected_keys:
                    fail(f"{path.name}:{group} has incomplete face coverage")

    return {
        "bytes": path.stat().st_size,
        "fontCount": expected_font_count,
        "sha256": sha256(path),
        "fontVersions": sorted(versions),
        "postScriptNameCount": len(postscript_names),
    }


def write_checksums(path: Path, archive_results: dict[str, dict[str, object]]) -> None:
    lines = [
        f"{result['sha256']}  {name}"
        for name, result in sorted(archive_results.items())
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("release_dir", type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--write-manifest", type=Path)
    parser.add_argument("--write-checksums", type=Path)
    args = parser.parse_args()

    if not VERSION_PATTERN.fullmatch(args.version):
        parser.error(
            "--version must look like v1.2.3 or v1.2.3-rc.1"
        )
    if not re.fullmatch(r"[0-9a-f]{40}", args.source_sha):
        parser.error("--source-sha must be a 40-character lowercase Git SHA")

    release_dir = args.release_dir.resolve()
    toolchain_path = Path(__file__).resolve().parents[1] / ".github/font-toolchain.json"
    toolchain = json.loads(toolchain_path.read_text(encoding="utf-8"))

    candidate_archives = {
        path.name
        for path in release_dir.glob("NoisyMono*.zip")
    }
    if candidate_archives != set(ARCHIVES):
        fail(
            "release archive set differs: "
            f"expected {sorted(ARCHIVES)}, found {sorted(candidate_archives)}"
        )

    results = {}
    for archive_name, rule in ARCHIVES.items():
        archive_path = release_dir / archive_name
        results[archive_name] = validate_archive(archive_path, rule)
        print(
            f"Validated {archive_name}: "
            f"{results[archive_name]['fontCount']} fonts"
        )

    if args.write_checksums:
        write_checksums(args.write_checksums, results)

    manifest = {
        "schemaVersion": 1,
        "releaseVersion": args.version,
        "sourceCommit": args.source_sha,
        "toolchain": toolchain,
        "archives": results,
    }
    if args.write_manifest:
        args.write_manifest.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    print(
        f"Release candidate {args.version} is structurally valid "
        f"({sum(result['fontCount'] for result in results.values())} fonts)"
    )


if __name__ == "__main__":
    main()
