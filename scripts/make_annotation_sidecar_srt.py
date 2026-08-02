"""把 annotations.json 转成可单独导入剪辑软件的注释文本 SRT。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def srt_time(value: str) -> str:
    value = str(value).strip()
    if len(value.split(":")) == 2:
        value = "00:" + value
    if "." in value:
        head, fraction = value.rsplit(".", 1)
        value = f"{head},{fraction[:3].ljust(3, '0')}"
    elif "," not in value:
        value = value + ",000"
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotations", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    data = json.loads(args.annotations.read_text(encoding="utf-8"))
    annotations = data.get("annotations", [])
    rows = []
    for index, item in enumerate(annotations, 1):
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        rows.extend(
            [
                str(index),
                f"{srt_time(item['start'])} --> {srt_time(item['end'])}",
                text,
                "",
            ]
        )
    args.output.write_text("\n".join(rows), encoding="utf-8-sig")
    print(args.output)


if __name__ == "__main__":
    main()
