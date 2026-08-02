"""将源片 SRT 按短视频 clips 重新映射到成片时间轴。"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


TIME_RE = re.compile(r"(\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2},\d{3})")


def parse_time(value: str) -> float:
    hours, minutes, seconds = value.replace(",", ".").split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def format_time(value: float) -> str:
    millis = max(0, int(round(value * 1000)))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    seconds, millis = divmod(millis, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"


def parse_srt(path: Path) -> list[tuple[float, float, str]]:
    blocks = re.split(r"\r?\n\r?\n+", path.read_text(encoding="utf-8-sig"))
    result = []
    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 3:
            continue
        match = TIME_RE.search(lines[1])
        if not match:
            continue
        text = "\n".join(lines[2:]).strip()
        if text:
            result.append((parse_time(match.group(1)), parse_time(match.group(2)), text))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--source-srt", required=True)
    parser.add_argument("--output-srt", required=True)
    args = parser.parse_args()

    plan_path = Path(args.plan).resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    source_cues = parse_srt(Path(args.source_srt).resolve())
    output_cues: list[tuple[float, float, str]] = []
    output_cursor = 0.0

    for clip in plan["clips"]:
        clip_start = parse_time(str(clip["source_start"]))
        clip_end = parse_time(str(clip["source_end"]))
        for cue_start, cue_end, text in source_cues:
            overlap_start = max(clip_start, cue_start)
            overlap_end = min(clip_end, cue_end)
            if overlap_end - overlap_start < 0.12:
                continue
            mapped_start = output_cursor + overlap_start - clip_start
            mapped_end = output_cursor + overlap_end - clip_start
            output_cues.append((mapped_start, mapped_end, text))
        output_cursor += clip_end - clip_start

    output_cues.sort(key=lambda item: (item[0], item[1]))
    blocks = []
    for index, (start, end, text) in enumerate(output_cues, start=1):
        blocks.append(f"{index}\n{format_time(start)} --> {format_time(end)}\n{text}")
    output_path = Path(args.output_srt).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
