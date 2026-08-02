"""将按成片时间轴映射好的 SRT 烧录到注释版视频。"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


STYLE = (
    "FontName=Microsoft YaHei,FontSize=18,"
    "PrimaryColour=&H00FFFFFF,OutlineColour=&H00101010,"
    "BorderStyle=1,Outline=1.5,Shadow=0,Alignment=2,"
    "MarginL=30,MarginR=30,MarginV=8"
)


def escape_filter_path(path: Path) -> str:
    """转成 subtitles filter 可接受的 Windows 路径。"""
    return str(path.resolve()).replace("\\", "/").replace(":", r"\:")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--srt", required=True, type=Path)
    args = parser.parse_args()

    for path in (args.input, args.srt):
        if not path.is_file():
            raise SystemExit(f"文件不存在：{path}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(f"{args.output.stem}.subtitle-rebuild.partial{args.output.suffix}")
    if temporary.exists():
        temporary.unlink()

    subtitle_filter = (
        f"subtitles=filename='{escape_filter_path(args.srt)}':"
        f"charenc=UTF-8:force_style='{STYLE}'"
    )
    command = [
        "ffmpeg", "-y", "-hide_banner",
        "-i", str(args.input),
        "-vf", subtitle_filter,
        "-map", "0:v:0", "-map", "0:a:0?",
        "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
        str(temporary),
    ]
    try:
        subprocess.run(command, check=True)
        temporary.replace(args.output)
    finally:
        if temporary.exists():
            temporary.unlink()

    print(args.output)


if __name__ == "__main__":
    main()
