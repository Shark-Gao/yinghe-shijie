#!/usr/bin/env python3
"""按中文停顿和最大字数拆分 SRT 字幕，并把时间按字数重新分配。"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


TIME_RE = re.compile(
    r"(?P<start>\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*"
    r"(?P<end>\d{2}:\d{2}:\d{2}[,.]\d{3})"
)
PAUSE_RE = re.compile(r"(?<=[。！？；：，、,.!?;:])")
SPACE_RE = re.compile(r"\s+")
TRAILING_PUNCTUATION_RE = re.compile(r"[，。！？；：、,.!?;:…]+$")


@dataclass
class Cue:
    start_ms: int
    end_ms: int
    text: str


def parse_time(value: str) -> int:
    hours, minutes, rest = value.replace(",", ".").split(":")
    seconds, millis = rest.split(".")
    return int(hours) * 3_600_000 + int(minutes) * 60_000 + int(seconds) * 1_000 + int(millis)


def format_time(value_ms: int) -> str:
    hours, remainder = divmod(max(0, value_ms), 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def parse_srt(path: Path) -> list[Cue]:
    source = path.read_text(encoding="utf-8-sig")
    blocks = re.split(r"\n\s*\n", source.replace("\r\n", "\n").replace("\r", "\n").strip())
    cues: list[Cue] = []
    for block in blocks:
        lines = [line.strip() for line in block.split("\n")]
        time_index = 1 if lines and lines[0].isdigit() else 0
        if time_index >= len(lines):
            continue
        match = TIME_RE.search(lines[time_index])
        text = SPACE_RE.sub(" ", " ".join(lines[time_index + 1 :])).strip()
        if not match or not text:
            continue
        cues.append(Cue(parse_time(match.group("start")), parse_time(match.group("end")), text))
    return cues


def hard_split(text: str, max_chars: int) -> list[str]:
    pieces: list[str] = []
    remaining = text.strip()
    while len(remaining) > max_chars:
        # 只略超上限时整句保留，避免最后只剩一两个字单独闪现。
        if len(remaining) <= max_chars + 6:
            pieces.append(remaining)
            return pieces
        cut = max_chars
        punctuation = re.search(r"[。！？；：，、,.!?;:]", remaining[: max_chars + 1])
        if punctuation:
            cut = punctuation.end()
        pieces.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    if remaining:
        pieces.append(remaining)
    return pieces


def split_text(text: str, max_chars: int) -> list[str]:
    clauses = [part.strip() for part in PAUSE_RE.split(text) if part.strip()]
    pieces: list[str] = []
    for clause in clauses:
        pieces.extend(hard_split(clause, max_chars))

    grouped: list[str] = []
    current = ""
    for piece in pieces:
        candidate = f"{current}{piece}" if current else piece
        if current and len(candidate) > max_chars:
            if len(current) <= 6:
                # “因此，”和“接下来，”这类引导词不要单独闪现。
                current = candidate
            else:
                grouped.append(current)
                current = piece
        else:
            current = candidate
        if current and re.search(r"[。！？；]$", current):
            grouped.append(current)
            current = ""
    if current:
        grouped.append(current)
    return grouped or [text.strip()]


def split_cue(cue: Cue, max_chars: int) -> list[Cue]:
    parts = split_text(cue.text, max_chars)
    if len(parts) == 1:
        return [cue]
    duration = max(1, cue.end_ms - cue.start_ms)
    weights = [max(1, len(re.sub(r"[\s，。！？；：、,.!?;:]", "", part))) for part in parts]
    total_weight = sum(weights)
    result: list[Cue] = []
    cursor = cue.start_ms
    for index, (part, weight) in enumerate(zip(parts, weights)):
        if index == len(parts) - 1:
            end = cue.end_ms
        else:
            end = cursor + round(duration * weight / total_weight)
            end = min(end, cue.end_ms - (len(parts) - index - 1))
        result.append(Cue(cursor, end, part))
        cursor = end
    return result


def strip_trailing_punctuation(text: str) -> str:
    """去掉字幕显示末尾标点，保留句内标点作为阅读停顿。"""
    return TRAILING_PUNCTUATION_RE.sub("", text).rstrip()


def build_srt(cues: list[Cue], max_chars: int) -> tuple[str, int]:
    rows: list[str] = []
    subtitle_id = 1
    total = 0
    for cue in cues:
        for part in split_cue(cue, max_chars):
            rows.extend(
                [
                    str(subtitle_id),
                    f"{format_time(part.start_ms)} --> {format_time(part.end_ms)}",
                    strip_trailing_punctuation(part.text),
                    "",
                ]
            )
            subtitle_id += 1
            total += 1
    return "\n".join(rows).rstrip() + "\n", total


def main() -> int:
    parser = argparse.ArgumentParser(description="按中文停顿拆分 SRT 字幕并重新分配时间。")
    parser.add_argument("--input", required=True, help="输入 UTF-8 SRT 文件。")
    parser.add_argument("--output", required=True, help="输出 UTF-8 SRT 文件。")
    parser.add_argument("--max-chars", type=int, default=20, help="每条字幕最多显示的汉字数，默认 20。")
    args = parser.parse_args()
    if args.max_chars < 8:
        parser.error("--max-chars 不能小于 8。")
    input_path = Path(args.input)
    output_path = Path(args.output)
    cues = parse_srt(input_path)
    if not cues:
        raise SystemExit(f"未找到有效字幕段：{input_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    contents, total = build_srt(cues, args.max_chars)
    output_path.write_text(contents, encoding="utf-8")
    print(f"Split {len(cues)} cues into {total} cues: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
