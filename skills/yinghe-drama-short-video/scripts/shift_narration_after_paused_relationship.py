#!/usr/bin/env python3
"""把已有中文解说拆成关系图段和剧情段，并将剧情段整体后移。"""
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
    parser.add_argument("--pause-seconds", type=float, required=True)
    parser.add_argument("--relationship-start-seconds", type=float, default=0.5)
    return parser.parse_args()


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def seconds(value: str) -> float:
    parts = value.split(":")
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])


def hms(value: float) -> str:
    total_ms = round(value * 1000)
    hours, total_ms = divmod(total_ms, 3_600_000)
    minutes, total_ms = divmod(total_ms, 60_000)
    secs, millis = divmod(total_ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def main() -> None:
    args = parse_args()
    input_audio = Path(args.input_audio).resolve()
    input_timing = Path(args.input_timing).resolve()
    output_audio = Path(args.output_audio).resolve()
    output_timing = Path(args.output_timing).resolve()
    pause = max(0.0, float(args.pause_seconds))
    if not input_audio.is_file():
        raise SystemExit(f"输入解说音频不存在：{input_audio}")
    if not input_timing.is_file():
        raise SystemExit(f"输入解说时长清单不存在：{input_timing}")
    timing = json.loads(input_timing.read_text(encoding="utf-8"))
    old_duration = probe_duration(input_audio)
    first_segment = timing.get("segments", [])[0]
    source_relationship_start = seconds(first_segment["start"])
    source_relationship_end = seconds(first_segment["end"])
    relationship_start = max(0.0, float(args.relationship_start_seconds))
    shifted_segments = []
    for index, segment in enumerate(timing.get("segments", [])):
        item = dict(segment)
        if index == 0:
            item["start"] = hms(relationship_start)
            item["end"] = hms(relationship_start + float(item.get("audio_duration", 0.0)))
        else:
            item["start"] = hms(seconds(item["start"]) + pause)
            item["end"] = hms(seconds(item["end"]) + pause)
        shifted_segments.append(item)

    output_audio.parent.mkdir(parents=True, exist_ok=True)
    output_timing.parent.mkdir(parents=True, exist_ok=True)
    delay_ms = round(pause * 2 * 1000)
    filter_complex = (
        f"[0:a]atrim=start={source_relationship_start:.3f}:end={source_relationship_end:.3f},"
        f"asetpts=PTS-STARTPTS,adelay={round(relationship_start * 1000)}|{round(relationship_start * 1000)}[relationship];"
        f"[0:a]atrim=start={pause:.3f}:end={old_duration:.3f},"
        f"asetpts=PTS-STARTPTS,adelay={delay_ms}|{delay_ms}[plot];"
        "[relationship][plot]amix=inputs=2:duration=longest:normalize=0,"
        "aresample=async=1:first_pts=0,asetpts=N/SR/TB[mix]"
    )
    temporary = output_audio.with_suffix(".partial.mp3")
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(input_audio),
            "-filter_complex", filter_complex, "-map", "[mix]",
            "-t", f"{old_duration + pause:.3f}", "-ac", "2", "-ar", "44100",
            "-codec:a", "libmp3lame", "-b:a", "192k", str(temporary),
        ],
        check=True,
    )
    temporary.replace(output_audio)
    merged = dict(timing)
    merged["output_audio"] = str(output_audio)
    merged["pause_seconds"] = pause
    merged["segments"] = shifted_segments
    output_timing.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output_audio)
    print(output_timing)


if __name__ == "__main__":
    main()
