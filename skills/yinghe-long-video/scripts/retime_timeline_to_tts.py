#!/usr/bin/env python3
"""按 TTS 分段实测时长重建长视频解说时间线。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeline", required=True, help="原始中文解说时间线 JSON")
    parser.add_argument("--manifest", required=True, help="render_timeline_tts.py 生成的分段时长 JSON")
    parser.add_argument("--output", required=True, help="实际配音对齐时间线 JSON")
    parser.add_argument(
        "--allow-truncated",
        action="store_true",
        help="允许实测音频超过视觉窗口；默认发现截断风险时直接失败",
    )
    return parser.parse_args()


def time_to_ms(value: str) -> int:
    hours, minutes, seconds = value.replace(",", ".").split(":")
    second, _, millisecond = seconds.partition(".")
    return (
        int(hours) * 3_600_000
        + int(minutes) * 60_000
        + int(second) * 1_000
        + int((millisecond + "000")[:3])
    )


def format_time(value_ms: int) -> str:
    hours, remainder = divmod(max(0, value_ms), 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def main() -> int:
    args = parse_args()
    timeline_path = Path(args.timeline)
    manifest_path = Path(args.manifest)
    output_path = Path(args.output)
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    durations = {
        item["id"]: float(item["audio_duration"])
        for item in manifest.get("segments", [])
        if item.get("id") and item.get("audio_duration") is not None
    }
    if not durations:
        raise SystemExit(f"未找到有效分段时长：{manifest_path}")

    video_duration_ms = time_to_ms(str(timeline["video_duration"]))
    aligned_segments: list[dict] = []
    truncated: list[str] = []
    for segment in timeline.get("segments", []):
        segment_id = segment.get("id")
        if segment_id not in durations:
            raise SystemExit(f"时间线分段缺少实测音频时长：{segment_id}")
        visual_start_ms = time_to_ms(segment["start"])
        visual_end_ms = time_to_ms(segment["end"])
        measured_ms = round(durations[segment_id] * 1000)
        audio_end_ms = visual_start_ms + measured_ms
        available_end_ms = min(audio_end_ms, video_duration_ms)
        is_truncated = audio_end_ms > video_duration_ms or audio_end_ms > visual_end_ms
        if is_truncated:
            truncated.append(segment_id)
            if not args.allow_truncated:
                raise SystemExit(
                    f"分段 {segment_id} 的实测音频超出可用窗口："
                    f"{durations[segment_id]:.3f}s"
                )
        aligned = dict(segment)
        aligned["visual_start"] = segment["start"]
        aligned["visual_end"] = segment["end"]
        aligned["start"] = format_time(visual_start_ms)
        aligned["end"] = format_time(available_end_ms)
        aligned["audio_duration"] = round(durations[segment_id], 3)
        aligned["audio_window_duration"] = round((available_end_ms - visual_start_ms) / 1000, 3)
        aligned["audio_truncated"] = is_truncated
        aligned_segments.append(aligned)

    output = dict(timeline)
    output["mode"] = "source_length_actual_tts_aligned"
    output["original_timeline"] = str(timeline_path)
    output["audio_manifest"] = str(manifest_path)
    output["alignment_rule"] = "字幕使用每段 TTS 实测时长，visual_start/visual_end 保留原画面窗口"
    output["truncated_segments"] = truncated
    output["segments"] = aligned_segments
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
