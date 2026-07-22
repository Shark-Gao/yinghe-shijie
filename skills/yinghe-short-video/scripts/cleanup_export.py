#!/usr/bin/env python3
"""Prune a short-video export directory down to its final delivery files."""
from __future__ import annotations

import argparse
from pathlib import Path


FINAL_SUFFIXES = (
    ".mp4",
    ".srt",
    "_封面_16x9_设计版.png",
    "_封面_4x3_设计版.png",
    "_封面_9x16_设计版.png",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", required=True, help="Dedicated <topic>_短视频 export directory.")
    options = parser.parse_args()
    export_dir = Path(options.export_dir).resolve()
    if not export_dir.is_dir():
        raise SystemExit(f"Export directory does not exist: {export_dir}")

    removed: list[str] = []
    for path in export_dir.iterdir():
        if path.is_file() and not path.name.endswith(FINAL_SUFFIXES):
            path.unlink()
            removed.append(path.name)

    print("Removed:")
    print("\n".join(removed) if removed else "(none)")
    print("Kept:")
    print("\n".join(path.name for path in sorted(export_dir.iterdir()) if path.is_file()))


if __name__ == "__main__":
    main()
