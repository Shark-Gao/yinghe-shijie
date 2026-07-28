#!/usr/bin/env python3
"""移除已有混音中的第一段人物关系口播，只保留剧情解说。"""
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
    return parser.parse_args()


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
    first = segments[0]
    first_start = first["start"]
    first_end = first["end"]
    output_audio.parent.mkdir(parents=True, exist_ok=True)
    output_timing.parent.mkdir(parents=True, exist_ok=True)
    filter_audio = f"volume='if(between(t,{_seconds(first_start):.3f},{_seconds(first_end):.3f}),0,1)'"
    temporary = output_audio.with_suffix(".partial.mp3")
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(input_audio),
            "-af", filter_audio, "-t", "163.000", "-ac", "2", "-ar", "44100",
            "-codec:a", "libmp3lame", "-b:a", "192k", str(temporary),
        ],
        check=True,
    )
    temporary.replace(output_audio)
    merged = dict(timing)
    merged["output_audio"] = str(output_audio)
    merged["segments"] = segments[1:]
    output_timing.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output_audio)
    print(output_timing)


def _seconds(value: str) -> float:
    parts = value.split(":")
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])


if __name__ == "__main__":
    main()
