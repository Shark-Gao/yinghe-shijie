#!/usr/bin/env python3
"""Build a verbatim Chinese-subtitle TTS timeline from SRT or VTT cues."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


TIME_RANGE = re.compile(
    r"(?P<start>(?:\d{1,2}:)?\d{2}:\d{2}[,.]\d{1,3})\s+-->\s+"
    r"(?P<end>(?:\d{1,2}:)?\d{2}:\d{2}[,.]\d{1,3})"
)
TAG = re.compile(r"<[^>]+>|\{\\[^}]+\}")
HAN = re.compile(r"[\u3400-\u9fff]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a verbatim Chinese-subtitle TTS timeline from SRT or VTT."
    )
    parser.add_argument("--subtitle", required=True, help="Input .srt or .vtt subtitle file.")
    parser.add_argument("--output", required=True, help="Output timeline JSON path.")
    parser.add_argument("--audio-output", help="MP3 path written into the timeline JSON.")
    parser.add_argument("--video", help="Optional source video used to determine the final duration.")
    parser.add_argument("--voice", default="zh-CN-YunyangNeural")
    parser.add_argument("--rate", default="+0%")
    return parser.parse_args()


def time_to_ms(value: str) -> int:
    parts = value.replace(",", ".").split(":")
    if len(parts) == 2:
        hours, minutes, seconds = "0", *parts
    elif len(parts) == 3:
        hours, minutes, seconds = parts
    else:
        raise ValueError(f"Invalid subtitle timestamp: {value}")
    second, dot, fraction = seconds.partition(".")
    milliseconds = (fraction + "000")[:3] if dot else "000"
    return (int(hours) * 3600 + int(minutes) * 60 + int(second)) * 1000 + int(milliseconds)


def ms_to_time(value: int) -> str:
    hours, remaining = divmod(value, 3_600_000)
    minutes, remaining = divmod(remaining, 60_000)
    seconds, milliseconds = divmod(remaining, 1_000)
    return f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"


def chinese_text(lines: list[str]) -> str:
    """Return the Chinese subtitle line(s), preserving their caption wording."""
    selected = []
    for line in lines:
        cleaned = TAG.sub("", line).strip()
        if HAN.search(cleaned):
            selected.append(cleaned)
    return " ".join(selected)


def parse_cues(source: str) -> list[dict[str, str]]:
    lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    cues: list[dict[str, str]] = []
    time_rows = [(index, TIME_RANGE.search(line)) for index, line in enumerate(lines)]
    time_rows = [(index, match) for index, match in time_rows if match]
    for position, (index, match) in enumerate(time_rows):
        start, end = time_to_ms(match.group("start")), time_to_ms(match.group("end"))
        next_index = time_rows[position + 1][0] if position + 1 < len(time_rows) else len(lines)
        # Some downloaded SRT files omit blank lines between cues. The next
        # timestamp is therefore the reliable boundary; any numeric cue ID in
        # the intervening rows is ignored because it contains no Chinese text.
        caption_lines = lines[index + 1:next_index]
        text = chinese_text(caption_lines)
        if text:
            cues.append({"start": ms_to_time(start), "end": ms_to_time(end), "text": text})
    return cues


def video_duration(video: Path) -> str:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(video),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return ms_to_time(round(float(result.stdout.strip()) * 1000))


def build_timeline(
    subtitle: Path, output: Path, audio_output: str | None, video: Path | None,
    voice: str, rate: str,
) -> dict:
    cues = parse_cues(subtitle.read_text(encoding="utf-8-sig"))
    if not cues:
        raise ValueError("No Chinese subtitle cues found. Provide a Chinese or bilingual SRT/VTT file.")
    output_audio = audio_output or f"{subtitle.stem}_中文字幕直读_Yunyang.mp3"
    duration = video_duration(video) if video else cues[-1]["end"]
    return {
        "version": 1,
        "source_subtitle": subtitle.name,
        "output_audio": output_audio,
        "mode": "verbatim_chinese_subtitle_audio",
        "voice": voice,
        "rate": rate,
        "video_duration": duration,
        "segments": [
            {"id": f"subtitle_{number:03}", **cue}
            for number, cue in enumerate(cues, start=1)
        ],
    }


def main() -> None:
    args = parse_args()
    subtitle, output = Path(args.subtitle), Path(args.output)
    if subtitle.suffix.lower() not in {".srt", ".vtt"}:
        raise SystemExit("Direct subtitle audio requires an .srt or .vtt file with time cues.")
    video = Path(args.video) if args.video else None
    if video and not video.is_file():
        raise SystemExit(f"Video file does not exist: {video}")
    try:
        timeline = build_timeline(subtitle, output, args.audio_output, video, args.voice, args.rate)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
