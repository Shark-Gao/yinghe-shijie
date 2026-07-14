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
    # Longer subtitle tracks can contain hundreds of small cues. A modest
    # concurrency limit plus retries is kinder to the remote Edge TTS service
    # and prevents one transient websocket timeout from losing the whole job.
    semaphore = asyncio.Semaphore(4)

    async def generate_one(segment: dict) -> Path | None:
        text = segment["text"].strip()
        if not text:
            return None
        path = build_dir / f"{segment['id']}.mp3"
        async with semaphore:
            for attempt in range(3):
                try:
                    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, volume="+0%")
                    await communicate.save(str(path))
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    await asyncio.sleep(1.5 * (2 ** attempt))
        return path

    rendered = await asyncio.gather(*(generate_one(segment) for segment in data["segments"]))
    return [path for path in rendered if path is not None]


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
    # A full subtitle track can have hundreds of cues. Passing both all input
    # paths and a giant filter expression on the Windows command line exceeds
    # CreateProcess's command-length limit, so keep the filter graph in a file.
    filter_script = build_dir / "filter_complex.txt"
    filter_script.write_text(filter_complex, encoding="utf-8")
    cmd = [
        "ffmpeg",
        "-y",
        *inputs,
        "-filter_complex_script",
        str(filter_script),
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
    # Keep temporary paths short: full subtitle tracks may pass hundreds of
    # segment files to ffmpeg, and Windows limits the total command length.
    short_temp_root = Path("C:/t")
    short_temp_root.mkdir(parents=True, exist_ok=True)
    build_dir = Path(tempfile.mkdtemp(prefix="x", dir=short_temp_root))
    try:
        asyncio.run(generate_segments(data, build_dir))
        print(render(data, timeline_path, args.output, build_dir))
    finally:
        shutil.rmtree(build_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
