#!/usr/bin/env python3
"""Create a deterministic ZIP archive from a directory tree."""

from __future__ import annotations

import argparse
from pathlib import Path
import time
import zipfile


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--source-date-epoch", type=int, required=True)
    args = parser.parse_args()

    if not args.source.is_dir():
        raise SystemExit(f"source directory not found: {args.source}")
    files = sorted(path for path in args.source.rglob("*") if path.is_file())
    if not files:
        raise SystemExit(f"source directory is empty: {args.source}")

    timestamp = time.gmtime(args.source_date_epoch)
    if timestamp.tm_year < 1980:
        raise SystemExit("SOURCE_DATE_EPOCH must be representable in ZIP")
    args.destination.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(
        args.destination,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in files:
            archive_path = path.relative_to(args.source).as_posix()
            info = zipfile.ZipInfo(archive_path, timestamp[:6])
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())

    print(f"wrote {args.destination} ({len(files)} files)")


if __name__ == "__main__":
    main()
