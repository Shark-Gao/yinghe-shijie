#!/usr/bin/env python3
"""Export Chinese narration subtitles from a narration timeline JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeline", required=True, help="Narration timeline JSON path.")
    parser.add_argument("--output", help="Output .srt path.")
    parser.add_argument(
        "--chinese-only",
        action="store_true",
        help="Write only Chinese narration lines, omitting english_text translations.",
    )
    return parser.parse_args()


def time_to_ms(value: str) -> int:
    hours, minutes, seconds = value.replace(",", ".").split(":")
    second, _, milliseconds = seconds.partition(".")
    return (int(hours) * 3600 + int(minutes) * 60 + int(second)) * 1000 + int((milliseconds + "000")[:3])


def srt_time(value: float) -> str:
    milliseconds = round(value)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    seconds, milliseconds = divmod(milliseconds, 1_000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def build_srt(timeline: dict, chinese_only: bool = False) -> str:
    rows: list[str] = []
    subtitle_id = 1
    previous_start = -1
    for segment in timeline.get("segments", []):
        text = str(segment.get("text", "")).strip()
        if not text:
            continue
        english_text = str(segment.get("english_text", "")).strip()
        if not chinese_only and not english_text:
            raise ValueError(
                f"Narration segment is missing english_text: {segment.get('id', '<unknown>')}"
            )
        start, end = time_to_ms(segment["start"]), time_to_ms(segment["end"])
        if start < previous_start or end <= start:
            raise ValueError(f"Invalid segment timing: {segment.get('id', '<unknown>')}")
        previous_start = start
        rows.extend([str(subtitle_id), f"{srt_time(start)} --> {srt_time(end)}", text])
        if not chinese_only:
            rows.append(english_text)
        rows.append("")
        subtitle_id += 1
    if subtitle_id == 1:
        raise ValueError("Timeline has no non-empty narration segments.")
    return "\n".join(rows)


def default_output_path(timeline: Path) -> Path:
    stem = timeline.stem.removesuffix("_等长解说时间线")
    return timeline.with_name(f"{stem}_中文解说.srt")


def main() -> None:
    args = parse_args()
    timeline_path = Path(args.timeline)
    data = json.loads(timeline_path.read_text(encoding="utf-8"))
    output = Path(args.output) if args.output else default_output_path(timeline_path)
    try:
        contents = build_srt(data, chinese_only=args.chinese_only)
    except (KeyError, ValueError) as error:
        raise SystemExit(str(error)) from error
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(contents, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
