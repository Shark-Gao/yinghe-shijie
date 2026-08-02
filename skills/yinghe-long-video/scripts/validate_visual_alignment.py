#!/usr/bin/env python3
"""校验长视频中文解说是否按画面锚点起播。"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PUNCTUATION_RE = re.compile(r"[\s，。！？；：、,.!?;:…“”‘’\"'（）()【】\[\]《》]+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeline", required=True, help="实际配音对齐时间线 JSON")
    parser.add_argument("--max-delta", type=float, default=1.0, help="允许音频起点与画面起点的最大差值，单位秒")
    parser.add_argument("--report", help="可选的校验报告 JSON 路径")
    return parser.parse_args()


def seconds(value: str | float | int) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", ".")
    if ":" not in text:
        return float(text)
    hours, minutes, rest = text.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(rest)


def compact(text: str) -> str:
    return PUNCTUATION_RE.sub("", str(text)).lower()


def load_anchors(data: dict) -> tuple[bool, list[dict], float]:
    alignment = data.get("visual_alignment")
    if not isinstance(alignment, dict):
        return False, [], 1.0
    required = bool(alignment.get("required", False))
    anchors = alignment.get("anchors")
    if anchors is None:
        anchors = data.get("visual_anchors", [])
    if not isinstance(anchors, list):
        raise SystemExit("visual_alignment.anchors 必须是数组。")
    max_delta = float(alignment.get("max_delta_seconds", 1.0))
    return required, anchors, max_delta


def validate(data: dict, cli_max_delta: float | None = None) -> dict:
    required, anchors, configured_max_delta = load_anchors(data)
    if not required:
        raise SystemExit("未启用 visual_alignment.required，不能执行强制画面锚点验收。")
    if not anchors:
        raise SystemExit("visual_alignment.required=true，但没有配置画面锚点。")

    max_delta = configured_max_delta if cli_max_delta is None else cli_max_delta
    alignment = data.get("visual_alignment") or {}
    max_gap = float(alignment.get("max_gap_seconds", 0.8))
    segments = data.get("segments")
    if not isinstance(segments, list) or not segments:
        raise SystemExit("时间线缺少 segments。")
    segment_by_id = {str(item.get("id")): item for item in segments if isinstance(item, dict) and item.get("id")}
    ordered_segments = sorted(
        (item for item in segments if isinstance(item, dict) and item.get("id")),
        key=lambda item: seconds(item.get("start", 0)),
    )
    failures: list[str] = []
    results: list[dict] = []
    previous_visual = -1.0
    previous_audio = -1.0
    previous_segment_end = 0.0

    for item in ordered_segments:
        try:
            segment_start = seconds(item["start"])
            segment_end = seconds(item["end"])
        except (KeyError, TypeError, ValueError) as error:
            failures.append(f"分段 {item.get('id', '<unknown>')} 时间码无效：{error}")
            continue
        gap = segment_start - previous_segment_end
        if gap > max_gap:
            failures.append(
                f"分段 {item.get('id', '<unknown>')} 前存在 {gap:.3f}s 连续空档，超过 {max_gap:.3f}s"
            )
        previous_segment_end = max(previous_segment_end, segment_end)

    for index, anchor in enumerate(anchors, start=1):
        if not isinstance(anchor, dict):
            failures.append(f"锚点 {index} 不是对象")
            continue
        anchor_id = str(anchor.get("id") or f"anchor_{index:03d}")
        required_fields = ("anchor_text", "visual_start", "visual_end", "segment_id", "source_evidence")
        missing = [field for field in required_fields if not str(anchor.get(field, "")).strip()]
        if missing:
            failures.append(f"{anchor_id} 缺少字段：{', '.join(missing)}")
            continue

        segment_id = str(anchor["segment_id"])
        segment = segment_by_id.get(segment_id)
        if segment is None:
            failures.append(f"{anchor_id} 找不到 segment_id={segment_id}")
            continue

        try:
            visual_start = seconds(anchor["visual_start"])
            visual_end = seconds(anchor["visual_end"])
            audio_start = seconds(segment["start"])
            audio_end = seconds(segment["end"])
        except (KeyError, TypeError, ValueError) as error:
            failures.append(f"{anchor_id} 时间码无效：{error}")
            continue

        if visual_end <= visual_start:
            failures.append(f"{anchor_id} 的 visual_end 必须晚于 visual_start")
        if audio_end <= audio_start:
            failures.append(f"{anchor_id} 对应音频段为空：{segment_id}")
        if visual_start < previous_visual:
            failures.append(f"锚点画面时间倒序：{anchor_id}")
        if audio_start < previous_audio:
            failures.append(f"锚点音频时间倒序：{anchor_id}")
        previous_visual = max(previous_visual, visual_start)
        previous_audio = max(previous_audio, audio_start)

        anchor_text = compact(str(anchor["anchor_text"]))
        segment_text = compact(str(segment.get("text", "")))
        if not anchor_text:
            failures.append(f"{anchor_id} 的 anchor_text 为空")
        elif anchor_text not in segment_text:
            failures.append(f"{anchor_id} 的 anchor_text 不在 {segment_id} 文案中")
        elif anchor.get("match_mode", "segment_start") == "segment_start" and not segment_text.startswith(anchor_text):
            failures.append(
                f"{anchor_id} 不是独立锚点段：{segment_id} 必须以 anchor_text 开始，禁止在长段内部估算起点"
            )

        target_start = seconds(segment.get("start", 0))
        earlier_occurrences = [
            str(item.get("id"))
            for item in ordered_segments
            if seconds(item.get("start", 0)) < target_start
            and anchor_text
            and anchor_text in compact(str(item.get("text", "")))
        ]
        if earlier_occurrences:
            failures.append(
                f"{anchor_id} 在目标段之前已出现：{', '.join(earlier_occurrences)}；锚点必须绑定首次出现"
            )

        delta = audio_start - visual_start
        if abs(delta) > max_delta:
            failures.append(
                f"{anchor_id} 错位 {delta:+.3f}s：画面 {visual_start:.3f}s，音频 {audio_start:.3f}s"
            )
        if audio_start >= visual_end or audio_end <= visual_start:
            failures.append(f"{anchor_id} 对应音频没有覆盖画面窗口：{segment_id}")

        results.append(
            {
                "id": anchor_id,
                "segment_id": segment_id,
                "anchor_text": anchor["anchor_text"],
                "visual_start": round(visual_start, 3),
                "visual_end": round(visual_end, 3),
                "audio_start": round(audio_start, 3),
                "audio_end": round(audio_end, 3),
                "delta_seconds": round(delta, 3),
                "status": "passed" if abs(delta) <= max_delta else "failed",
            }
        )

    report = {
        "status": "passed" if not failures else "failed",
        "max_delta_seconds": max_delta,
        "max_gap_seconds": max_gap,
        "anchor_count": len(anchors),
        "failures": failures,
        "anchors": results,
    }
    if failures:
        raise SystemExit("画面锚点验收失败：\n- " + "\n- ".join(failures))
    return report


def main() -> int:
    args = parse_args()
    timeline_path = Path(args.timeline)
    data = json.loads(timeline_path.read_text(encoding="utf-8"))
    report = validate(data, args.max_delta)
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Visual alignment passed: {report['anchor_count']} anchors, max delta {args.max_delta:.3f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
