#!/usr/bin/env python3
"""把纯剧情解说的第一段提前到视频开头，保留后续口播原时间。"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-audio", required=True)
    parser.add_argument("--input-timing", required=True)
    parser.add_argument("--output-audio", required=True)
    parser.add_argument("--output-timing", required=True)
    parser.add_argument("--source-start", type=float, default=16.0)
    parser.add_argument("--source-end", type=float, default=26.0)
    parser.add_argument("--target-start", type=float, default=0.5)
    return parser.parse_args()


def seconds(value: str) -> float:
    parts = value.split(":")
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])


def hms(value: float) -> str:
    total_ms = round(value * 1000)
    hours, total_ms = divmod(total_ms, 3_600_000)
    minutes, total_ms = divmod(total_ms, 60_000)
    secs, millis = divmod(total_ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def main() -> None:
    args = parse_args()
    input_audio = Path(args.input_audio).resolve()
    input_timing = Path(args.input_timing).resolve()
    output_audio = Path(args.output_audio).resolve()
    output_timing = Path(args.output_timing).resolve()
    timing = json.loads(input_timing.read_text(encoding="utf-8"))
    segments = timing.get("segments", [])
    if not segments:
        raise SystemExit("输入时长清单没有解说段。")
    old_duration = probe_duration(input_audio)
    first_duration = float(segments[0].get("audio_duration", args.source_end - args.source_start))
    output_audio.parent.mkdir(parents=True, exist_ok=True)
    output_timing.parent.mkdir(parents=True, exist_ok=True)
    rest_delay = round(args.source_end * 1000)
    first_delay = round(args.target_start * 1000)
    filter_complex = (
        f"[0:a]atrim=start={args.source_start:.3f}:end={args.source_end:.3f},"
        f"asetpts=PTS-STARTPTS,adelay={first_delay}|{first_delay}[first];"
        f"[0:a]atrim=start={args.source_end:.3f}:end={old_duration:.3f},"
        f"asetpts=PTS-STARTPTS,adelay={rest_delay}|{rest_delay}[rest];"
        "[first][rest]amix=inputs=2:duration=longest:normalize=0,"
        "aresample=async=1:first_pts=0,asetpts=N/SR/TB[mix]"
    )
    temporary = output_audio.with_suffix(".partial.mp3")
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(input_audio),
            "-filter_complex", filter_complex, "-map", "[mix]", "-t", f"{old_duration:.3f}",
            "-ac", "2", "-ar", "44100", "-codec:a", "libmp3lame", "-b:a", "192k", str(temporary),
        ],
        check=True,
    )
    temporary.replace(output_audio)
    shifted = []
    for index, segment in enumerate(segments):
        item = dict(segment)
        if index == 0:
            item["start"] = hms(args.target_start)
            item["end"] = hms(args.target_start + first_duration)
        shifted.append(item)
    merged = dict(timing)
    merged["output_audio"] = str(output_audio)
    merged["segments"] = shifted
    output_timing.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output_audio)
    print(output_timing)


if __name__ == "__main__":
    main()
