#!/usr/bin/env python3
"""根据解说时间线生成紧凑、可校验的画面注释。"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="根据解说时间线 JSON 创建画面注释。")
    parser.add_argument("--timeline", required=True, help="源解说时间线 JSON。")
    parser.add_argument("--output", required=True, help="输出注释 JSON。")
    parser.add_argument("--target-video", default="", help="可选目标视频路径。")
    parser.add_argument(
        "--format",
        choices=("label", "plot_summary"),
        default="label",
        help="注释格式；plot_summary 只输出一条接下来剧情简介，不生成副行。",
    )
    return parser.parse_args()


def to_ms(value: str | int | float) -> int:
    """把时间码或数值秒统一转换成毫秒。"""
    if isinstance(value, (int, float)):
        return round(float(value) * 1000)
    text = str(value).replace(",", ".")
    if ":" not in text:
        return round(float(text) * 1000)
    hours, minutes, seconds = text.split(":")
    return round((int(hours) * 3600 + int(minutes) * 60 + float(seconds)) * 1000)


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


def plot_summary(text: str) -> str:
    """保留一条可直接覆盖在画面上的剧情简介，不拆成主行和副行。"""
    cleaned = re.sub(r"\s+", "", text.strip())
    if not cleaned:
        return "剧情继续推进"
    sentences = [part.strip() for part in re.split(r"(?<=[。！？；])", cleaned) if part.strip()]
    candidate = sentences[0] if sentences else cleaned
    has_chinese_quotes = cleaned.startswith("“") and cleaned.endswith("”")
    candidate = candidate.rstrip("。！？；：，、,.!?;:")
    if has_chinese_quotes and not candidate.endswith("”"):
        candidate += "”"
    if len(candidate) > 30:
        closing_quote = "”" if has_chinese_quotes else ""
        body = candidate[:-1] if closing_quote and candidate.endswith(closing_quote) else candidate
        candidate = body[:29 - len(closing_quote)].rstrip("，、：；") + "…" + closing_quote
    return candidate or "剧情继续推进"


def ensure_annotation_quotes(text: str) -> str:
    """为每条视频注释补齐外层中文双引号，避免与台词引用混淆。"""
    cleaned = re.sub(r"\s+", "", text.strip())
    if not cleaned:
        return "“剧情继续推进”"
    if cleaned.startswith("“") and cleaned.endswith("”"):
        return cleaned
    cleaned = cleaned.replace("“", "‘").replace("”", "’")
    return f"“{cleaned}”"


def minimum_annotation_count(video_duration_ms: int) -> int:
    minutes = video_duration_ms / 60_000
    if minutes <= 8:
        return 12
    if minutes <= 15:
        return 24
    if minutes <= 25:
        return 45
    return 75


def select_annotation_segments(segments: list[dict], maximum: int = 120) -> list[dict]:
    """将过长的字幕轨限制在注释结构允许的最大数量内。"""
    if len(segments) <= maximum:
        return segments
    last = len(segments) - 1
    indices = {
        round(position * last / (maximum - 1))
        for position in range(maximum)
    }
    return [segment for index, segment in enumerate(segments) if index in indices]


def main() -> None:
    args = parse_args()
    timeline_path = Path(args.timeline)
    data = json.loads(timeline_path.read_text(encoding="utf-8"))
    annotations = []
    segments = select_annotation_segments(data["segments"])
    for index, segment in enumerate(segments, start=1):
        start = to_ms(segment["start"])
        end = min(start + 4_000, to_ms(segment["end"]))
        if end - start < 1_500:
            end = start + 1_500
        text = plot_summary(segment["text"]) if args.format == "plot_summary" else label(segment["text"])
        text = ensure_annotation_quotes(text)
        annotations.append({
            "id": f"anno_{index:03}",
            "start": segment["start"],
            "end": to_time(end),
            "type": "chapter" if index in {1, 2, 11, 19, 24, 31, 35, 39, 45} else ("callout" if args.format == "plot_summary" else "principle"),
            "text": text,
            "subtext": "",
            "position": "top_center" if index % 2 else "center",
            "x": 0,
            "y": 520 if index % 2 else 260,
            "layer": 10,
            "style": "arrow_callout" if args.format == "plot_summary" else "tech_label",
            "motion": "fade",
            "visual_hint": "在下一段剧情即将发生或正在发生的对应画面中显示",
            "avoid": ["subtitle", "face"],
        })
    if args.format != "plot_summary":
        target_count = minimum_annotation_count(to_ms(data["video_duration"]))
        for index, segment in enumerate(segments):
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
                "text": ensure_annotation_quotes(alternate_label(segment["text"])),
                "subtext": "",
                "position": "center",
                "x": 0,
                "y": 260,
                "layer": 10,
                "style": "tech_label",
                "motion": "fade",
                "visual_hint": "在对应的结构、节点连线或公式动画中显示",
                "avoid": ["subtitle", "core_subject"],
            })
    annotations.sort(key=lambda item: to_ms(item["start"]))
    for index, annotation in enumerate(annotations, start=1):
        annotation["id"] = f"anno_{index:03}"
    output = {
        "version": 1,
        "source_subtitle": data.get("source_subtitle", data.get("source_plan", "")),
        "target_video": args.target_video,
        "notes": "由时间线生成的单行屏幕注释；plot_summary 模式只显示接下来剧情简介，不显示副行。",
        "annotations": annotations,
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
