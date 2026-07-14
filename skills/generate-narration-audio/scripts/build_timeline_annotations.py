#!/usr/bin/env python3
"""Build compact, validated overlay annotations from a narration timeline."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create overlay annotations from a narration timeline JSON.")
    parser.add_argument("--timeline", required=True, help="Source narration timeline JSON.")
    parser.add_argument("--output", required=True, help="Output annotation JSON.")
    parser.add_argument("--target-video", default="", help="Optional target video path.")
    return parser.parse_args()


def to_ms(value: str) -> int:
    hours, minutes, seconds = value.split(":")
    sec, millis = seconds.split(".")
    return ((int(hours) * 60 + int(minutes)) * 60 + int(sec)) * 1000 + int(millis)


def to_time(value: int) -> str:
    hours, remain = divmod(value, 3_600_000)
    minutes, remain = divmod(remain, 60_000)
    seconds, millis = divmod(remain, 1_000)
    return f"{hours:02}:{minutes:02}:{seconds:02}.{millis:03}"


def label(text: str) -> str:
    text = re.split(r"[。！？，、；：]", text.strip(), maxsplit=1)[0]
    return text[:14] or "关键结构说明"


def alternate_label(text: str) -> str:
    parts = [part.strip() for part in re.split(r"[。！？，、；：]", text) if part.strip()]
    return (parts[1] if len(parts) > 1 else parts[0])[:14] or "关键结构说明"


def minimum_annotation_count(video_duration_ms: int) -> int:
    minutes = video_duration_ms / 60_000
    if minutes <= 8:
        return 12
    if minutes <= 15:
        return 24
    if minutes <= 25:
        return 45
    return 75


def main() -> None:
    args = parse_args()
    timeline_path = Path(args.timeline)
    data = json.loads(timeline_path.read_text(encoding="utf-8"))
    annotations = []
    for index, segment in enumerate(data["segments"], start=1):
        start = to_ms(segment["start"])
        end = min(start + 4_000, to_ms(segment["end"]))
        if end - start < 1_500:
            end = start + 1_500
        annotations.append({
            "id": f"anno_{index:03}",
            "start": segment["start"],
            "end": to_time(end),
            "type": "chapter" if index in {1, 2, 11, 19, 24, 31, 35, 39, 45} else "principle",
            "text": label(segment["text"]),
            "subtext": "",
            "position": "top_center" if index % 2 else "center",
            "x": 0,
            "y": 520 if index % 2 else 260,
            "layer": 10,
            "style": "tech_label",
            "motion": "fade",
            "visual_hint": "在对应的神经网络结构、节点连线或公式动画中显示",
            "avoid": ["subtitle", "core_subject"],
        })
    target_count = minimum_annotation_count(to_ms(data["video_duration"]))
    for index, segment in enumerate(data["segments"]):
        if len(annotations) >= target_count:
            break
        start, end = to_ms(segment["start"]), to_ms(segment["end"])
        midpoint = start + (end - start) // 2
        extra_start = min(midpoint, end - 1_500)
        extra_end = min(extra_start + 3_500, end)
        annotations.append({
            "id": f"anno_{len(annotations) + 1:03}",
            "start": to_time(extra_start),
            "end": to_time(extra_end),
            "type": "callout",
            "text": alternate_label(segment["text"]),
            "subtext": "",
            "position": "center",
            "x": 0,
            "y": 260,
            "layer": 10,
            "style": "tech_label",
            "motion": "fade",
            "visual_hint": "在对应的神经网络结构、节点连线或公式动画中显示",
            "avoid": ["subtitle", "core_subject"],
        })
    annotations.sort(key=lambda item: to_ms(item["start"]))
    for index, annotation in enumerate(annotations, start=1):
        annotation["id"] = f"anno_{index:03}"
    output = {
        "version": 1,
        "source_subtitle": data["source_subtitle"],
        "target_video": args.target_video,
        "notes": "等长全程版视频文字注释，由解说时间线自动生成，可按画面微调。",
        "annotations": annotations,
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
