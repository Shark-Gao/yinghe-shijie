#!/usr/bin/env python3
"""Prepare lightweight visual and subtitle review assets for a long video."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


TIME = re.compile(r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--subtitle", required=True)
    parser.add_argument("--output-dir")
    parser.add_argument("--interval", type=float, default=5.0, help="Seconds between review frames.")
    return parser.parse_args()


def timestamp_to_seconds(value: str) -> float:
    h, m, s = value.replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def subtitle_cues(path: Path) -> list[dict]:
    content = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    matches = list(TIME.finditer(content))
    cues = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        lines = [line.strip() for line in content[match.end():end].splitlines() if line.strip()]
        if lines and lines[-1].isdigit():
            lines.pop()
        text = " ".join(lines)
        cues.append({"start": match.group(1).replace(",", "."), "end": match.group(2).replace(",", "."), "text": text})
    return cues


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    video, subtitle = Path(args.video).resolve(), Path(args.subtitle).resolve()
    if not video.is_file() or not subtitle.is_file():
        raise SystemExit("Video or subtitle file does not exist.")
    output = Path(args.output_dir).resolve() if args.output_dir else video.parent / f"{video.stem}_review"
    output.mkdir(parents=True, exist_ok=True)
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate", "-of", "json", str(video)], check=True, capture_output=True, text=True, encoding="utf-8")
    metadata = json.loads(probe.stdout)
    duration = float(metadata["format"]["duration"])
    cues = subtitle_cues(subtitle)
    (output / "subtitle_cues.json").write_text(json.dumps(cues, ensure_ascii=False, indent=2), encoding="utf-8")
    frames = output / "contact_sheet_%03d.jpg"
    vf = f"fps=1/{args.interval},scale=320:-2,tile=4x4:padding=4:margin=4"
    subprocess.run(["ffmpeg", "-y", "-i", str(video), "-vf", vf, "-q:v", "3", str(frames)], check=True)
    sheet_count = len(list(output.glob("contact_sheet_*.jpg")))
    index = {
        "video": str(video), "subtitle": str(subtitle), "duration_seconds": duration,
        "interval_seconds": args.interval, "grid": "4x4", "sheet_count": sheet_count,
        "note": "Each tile advances by interval_seconds, left-to-right then top-to-bottom. Use as a visual index; confirm selected timecodes against source video."
    }
    (output / "review_index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
