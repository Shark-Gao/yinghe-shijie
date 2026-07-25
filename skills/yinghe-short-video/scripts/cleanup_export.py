#!/usr/bin/env python3
"""将短视频输出目录清理为最终交付文件。"""
from __future__ import annotations

import argparse
from pathlib import Path


FINAL_SUFFIXES = (
    ".mp4",
    ".srt",
    ".json",
    "_封面_16x9_设计版.png",
    "_封面_4x3_设计版.png",
    "_封面_9x16_设计版.png",
)


def is_final_file(path: Path) -> bool:
    if path.name.endswith(FINAL_SUFFIXES):
        if path.suffix != ".json":
            return True
        intermediate_markers = ("时间线", "时长", "注释", "分段")
        return not any(marker in path.stem for marker in intermediate_markers)
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", required=True, help="专用的 <topic>_短视频 输出目录。")
    options = parser.parse_args()
    export_dir = Path(options.export_dir).resolve()
    if not export_dir.is_dir():
        raise SystemExit(f"Export directory does not exist: {export_dir}")

    removed: list[str] = []
    for path in export_dir.iterdir():
        if path.is_file() and not is_final_file(path):
            path.unlink()
            removed.append(path.name)

    print("Removed:")
    print("\n".join(removed) if removed else "(none)")
    print("Kept:")
    print("\n".join(path.name for path in sorted(export_dir.iterdir()) if path.is_file()))


if __name__ == "__main__":
    main()
