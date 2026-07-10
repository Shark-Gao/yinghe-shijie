#!/usr/bin/env python3
"""Render a timeline JSON into one padded Yunyang narration MP3."""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import edge_tts

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render timeline TTS segments into one MP3.")
    parser.add_argument("--timeline", required=True, help="Timeline JSON path.")
    parser.add_argument("--output", help="Override output .mp3 path.")
    return parser.parse_args()


def hms_to_ms(value: str) -> int:
    h, m, rest = value.split(":")
    if "." in rest:
        s, ms = rest.split(".", 1)
        ms = (ms + "000")[:3]
    else:
        s, ms = rest, "000"
    return (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms)


async def generate_segments(data: dict, build_dir: Path) -> list[Path]:
    voice = data.get("voice") or "zh-CN-YunyangNeural"
    rate = data.get("rate") or "-8%"
    paths: list[Path] = []
    for segment in data["segments"]:
        text = segment["text"].strip()
        if not text:
            continue
        path = build_dir / f"{segment['id']}.mp3"
        communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, volume="+0%")
        await communicate.save(str(path))
        paths.append(path)
    return paths


def validate_timeline(data: dict) -> None:
    if not data.get("segments"):
        raise SystemExit("Timeline has no segments.")
    previous = -1
    for segment in data["segments"]:
        start = hms_to_ms(segment["start"])
        if start < previous:
            raise SystemExit(f"Segment starts are not increasing at {segment.get('id')}.")
        previous = start
        if not segment.get("text", "").strip():
            raise SystemExit(f"Segment has empty text: {segment.get('id')}")


def render(data: dict, timeline_path: Path, output_override: str | None, build_dir: Path) -> Path:
    output_name = output_override or data.get("output_audio")
    if not output_name:
        output_name = f"{timeline_path.stem}_Yunyang.mp3"
    output_path = Path(output_name)
    if not output_path.is_absolute():
        output_path = timeline_path.parent / output_path

    inputs: list[str] = []
    filters: list[str] = []
    labels: list[str] = []
    used_index = 0
    for segment in data["segments"]:
        segment_path = build_dir / f"{segment['id']}.mp3"
        if not segment_path.exists():
            continue
        inputs.extend(["-i", str(segment_path)])
        delay = hms_to_ms(segment["start"])
        label = f"a{used_index}"
        filters.append(f"[{used_index}:a]adelay={delay}|{delay},volume=1[{label}]")
        labels.append(f"[{label}]")
        used_index += 1

    if not labels:
        raise SystemExit("No segment audio files were generated.")

    filter_complex = ";".join(filters) + ";" + "".join(labels)
    filter_complex += f"amix=inputs={len(labels)}:duration=longest:normalize=0,apad[mix]"
    cmd = [
        "ffmpeg",
        "-y",
        *inputs,
        "-filter_complex",
        filter_complex,
        "-map",
        "[mix]",
        "-t",
        data["video_duration"],
        "-ac",
        "2",
        "-ar",
        "44100",
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "192k",
        str(output_path),
    ]
    subprocess.run(cmd, check=True)
    return output_path


def main() -> None:
    args = parse_args()
    timeline_path = Path(args.timeline)
    data = json.loads(timeline_path.read_text(encoding="utf-8"))
    validate_timeline(data)
    build_dir = Path(tempfile.mkdtemp(prefix="timeline_tts_"))
    try:
        asyncio.run(generate_segments(data, build_dir))
        print(render(data, timeline_path, args.output, build_dir))
    finally:
        shutil.rmtree(build_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
