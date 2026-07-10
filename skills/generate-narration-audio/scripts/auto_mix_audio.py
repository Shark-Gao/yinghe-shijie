#!/usr/bin/env python3
"""Create a Jianying-friendly auto-ducked MP3 mix."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def ffprobe_duration(path: Path) -> float:
    result = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
    )
    return float(result.stdout.strip())


def derive_output_path(narration: Path) -> Path:
    stem = narration.stem
    if stem.endswith("_Yunyang"):
        stem = stem[: -len("_Yunyang")]
    return narration.with_name(f"{stem}_自动混音_正式版.mp3")


def create_mix(video: Path, narration: Path, output: Path, duration: float, bg_volume: float, voice_volume: float) -> None:
    duration_text = f"{duration:.3f}"
    filter_complex = (
        f"[0:a]aresample=44100,atrim=0:{duration_text},asetpts=N/SR/TB,volume={bg_volume}[bg_in];"
        f"[1:a]aresample=44100,apad,atrim=0:{duration_text},asetpts=N/SR/TB,volume={voice_volume},"
        "asplit=2[voice_side][voice_mix];"
        "[bg_in][voice_side]sidechaincompress=threshold=0.003:ratio=16:attack=35:release=900:makeup=1[bg_ducked];"
        "[bg_ducked][voice_mix]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
        f"dynaudnorm=f=150:g=11:p=0.90,alimiter=limit=0.95,apad,atrim=0:{duration_text}[a]"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(video),
            "-i",
            str(narration),
            "-filter_complex",
            filter_complex,
            "-map",
            "[a]",
            "-vn",
            "-map_metadata",
            "-1",
            "-ar",
            "44100",
            "-ac",
            "2",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(output),
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True, help="Source video with original audio")
    parser.add_argument("--narration", required=True, help="Chinese narration MP3")
    parser.add_argument("--output", help="Output mixed MP3 path")
    parser.add_argument("--bg-volume", type=float, default=0.35, help="Original video audio base volume, default 0.35")
    parser.add_argument("--voice-volume", type=float, default=4.0, help="Chinese narration volume, default 4.0")
    args = parser.parse_args()

    video = Path(args.video)
    narration = Path(args.narration)
    output = Path(args.output) if args.output else derive_output_path(narration)

    if not video.exists():
        print(f"Video not found: {video}", file=sys.stderr)
        return 2
    if not narration.exists():
        print(f"Narration not found: {narration}", file=sys.stderr)
        return 2

    output.parent.mkdir(parents=True, exist_ok=True)
    duration = ffprobe_duration(video)
    create_mix(video, narration, output, duration, args.bg_volume, args.voice_volume)
    mixed_duration = ffprobe_duration(output)

    print(f"Wrote mix: {output}")
    print(f"Video duration: {duration:.3f}s")
    print(f"Mix duration: {mixed_duration:.3f}s")
    print(f"Background volume: {args.bg_volume}")
    print(f"Voice volume: {args.voice_volume}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
