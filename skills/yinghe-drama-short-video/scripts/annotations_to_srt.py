#!/usr/bin/env python3
"""将屏幕剧情注释 JSON 转换为旁车 SRT。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def to_ms(value: str) -> int:
    parts = value.replace(",", ".").split(":")
    if len(parts) == 3:
        hours, minutes, seconds = parts
    elif len(parts) == 2:
        hours, minutes, seconds = "0", parts[0], parts[1]
    else:
        hours, minutes, seconds = "0", "0", parts[0]
    whole, _, fraction = seconds.partition(".")
    return (int(hours) * 3600 + int(minutes) * 60 + int(whole)) * 1000 + int((fraction + "000")[:3])


def srt_time(milliseconds: int) -> str:
    milliseconds = max(0, milliseconds)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1_000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="注释 JSON 路径。")
    parser.add_argument("--output", required=True, help="SRT 输出路径。")
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    blocks = []
    for index, item in enumerate(data.get("annotations", []), start=1):
        blocks.append(
            f"{index}\n"
            f"{srt_time(to_ms(item['start']))} --> {srt_time(to_ms(item['end']))}\n"
            f"{item['text']}\n"
        )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(blocks) + ("\n" if blocks else ""), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
