#!/usr/bin/env python3
"""把原片字幕按剪辑计划映射到成片时间轴。"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


TIME_RE = re.compile(
    r"(?P<start>\d{2}:\d{2}:\d{2}[,.]\d{3})\s+-->\s+(?P<end>\d{2}:\d{2}:\d{2}[,.]\d{3})"
)


def to_seconds(value: str) -> float:
    h, m, s = value.replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def to_time(value: float) -> str:
    ms = round(value * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def parse_srt(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n\s*\n", text.strip())
    rows: list[dict] = []
    for block in blocks:
        match = TIME_RE.search(block)
        if not match:
            continue
        body = block[match.end():].strip().splitlines()
        if body and body[0].strip().isdigit():
            body = body[1:]
        body = [line.strip() for line in body if line.strip()]
        if not body:
            continue
        rows.append({
            "start": to_seconds(match.group("start")),
            "end": to_seconds(match.group("end")),
            "text": "\n".join(body),
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subtitle", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    subtitle_path = Path(args.subtitle).resolve()
    plan_path = Path(args.plan).resolve()
    output_path = Path(args.output).resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    source_cues = parse_srt(subtitle_path)
    rows: list[tuple[float, float, str]] = []
    cursor = 0.0
    for clip in plan["clips"]:
        source_start = float(clip["source_start"]) if isinstance(clip["source_start"], (int, float)) else to_seconds(str(clip["source_start"]))
        source_end = float(clip["source_end"]) if isinstance(clip["source_end"], (int, float)) else to_seconds(str(clip["source_end"]))
        duration = source_end - source_start
        for cue in source_cues:
            if cue["start"] < source_start - 0.001 or cue["end"] > source_end + 0.001:
                continue
            start = cursor + cue["start"] - source_start
            end = cursor + cue["end"] - source_start
            if end > start:
                rows.append((start, end, cue["text"]))
        cursor += duration

    output_path.parent.mkdir(parents=True, exist_ok=True)
    blocks: list[str] = []
    for index, (start, end, text) in enumerate(rows, 1):
        blocks.extend([str(index), f"{to_time(start)} --> {to_time(end)}", text, ""])
    output_path.write_text("\n".join(blocks), encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
