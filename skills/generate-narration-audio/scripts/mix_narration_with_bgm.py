#!/usr/bin/env python3
"""Mix a narration MP3 with looped background music at the project defaults."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


DEFAULT_MUSIC = Path("music/硬核视界_通用BGM_舒缓科普探索_CC0.mp3")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--narration", required=True, help="Narration MP3 path.")
    parser.add_argument("--music", default=str(DEFAULT_MUSIC), help="Loopable background music path.")
    parser.add_argument("--output", help="Output MP3 path.")
    parser.add_argument("--music-volume", type=float, default=0.45)
    parser.add_argument("--narration-volume", type=float, default=1.0)
    return parser.parse_args()


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def duration(path: Path) -> float:
    result = run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ])
    return float(result.stdout.strip())


def derive_output_path(narration: Path) -> Path:
    stem = narration.stem.removesuffix("_Yunyang")
    return narration.with_name(f"{stem}_背景音乐_正式版.mp3")


def create_mix(
    narration: Path, music: Path, output: Path, mix_duration: float,
    music_volume: float, narration_volume: float,
) -> None:
    duration_text = f"{mix_duration:.3f}"
    filters = (
        f"[0:a]aresample=44100,volume={music_volume},atrim=0:{duration_text},asetpts=N/SR/TB[music];"
        f"[1:a]aresample=44100,apad,atrim=0:{duration_text},asetpts=N/SR/TB,"
        f"volume={narration_volume}[voice];"
        "[music][voice]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]"
    )
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-stream_loop", "-1", "-i", str(music), "-i", str(narration),
        "-filter_complex", filters, "-map", "[a]", "-vn", "-map_metadata", "-1",
        "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-b:a", "192k", str(output),
    ])


def main() -> int:
    args = parse_args()
    narration, music = Path(args.narration), Path(args.music)
    output = Path(args.output) if args.output else derive_output_path(narration)
    if not narration.is_file():
        raise SystemExit(f"Narration file does not exist: {narration}")
    if not music.is_file():
        raise SystemExit(f"Background music file does not exist: {music}")
    output.parent.mkdir(parents=True, exist_ok=True)
    narration_duration = duration(narration)
    create_mix(narration, music, output, narration_duration, args.music_volume, args.narration_volume)
    print(f"Wrote mix: {output}")
    print(f"Duration: {duration(output):.3f}s")
    print(f"Music volume: {args.music_volume}")
    print(f"Narration volume: {args.narration_volume}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
