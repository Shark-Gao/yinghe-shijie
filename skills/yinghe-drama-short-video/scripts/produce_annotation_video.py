#!/usr/bin/env python3
"""只生成保留原声、没有烧录文字的清剪版 MP4。"""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SHORT_VIDEO_SCRIPTS = PROJECT_ROOT / "skills" / "yinghe-short-video" / "scripts"
BUILD_SCRIPT = SHORT_VIDEO_SCRIPTS / "build_short_video.py"
PREFLIGHT_SCRIPT = SHORT_VIDEO_SCRIPTS / "validate_preflight_review.py"
ANNOTATION_VALIDATOR = (
    PROJECT_ROOT
    / "skills"
    / "generate-narration-audio"
    / "scripts"
    / "validate_annotations_json.py"
)

sys.path.insert(0, str(SHORT_VIDEO_SCRIPTS))
from build_short_video import seconds, validate  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, help="annotation_only 电视剧剪辑计划 JSON。")
    parser.add_argument("--annotations", help="由 build_timeline_annotations.py 生成的注释 JSON。")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def resolve_path(value: str, plan_path: Path) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate.resolve()
    local = (plan_path.parent / candidate).resolve()
    if local.exists():
        return local
    return (PROJECT_ROOT / candidate).resolve()


def run_checked(command: list[str]) -> None:
    subprocess.run(command, check=True)


def validate_annotation_bindings(annotations: list[dict], clips: list[dict]) -> None:
    """确认每条剧情注释只属于一个成片片段，且没有跨切点。"""
    annotation_by_id = {
        str(item.get("id")): item
        for item in annotations
        if isinstance(item, dict) and item.get("id")
    }
    used_ids: dict[str, str] = {}
    output_cursor = 0.0
    for clip_index, clip in enumerate(clips, start=1):
        clip_start = output_cursor
        clip_end = output_cursor + seconds(clip["source_end"]) - seconds(clip["source_start"])
        output_cursor = clip_end
        if not clip.get("high_energy"):
            continue
        annotation_ids = clip.get("annotation_ids")
        if not isinstance(annotation_ids, list) or not annotation_ids:
            raise SystemExit(f"高能片段 clip_{clip_index:02} 缺少 annotation_ids。")
        for annotation_id in annotation_ids:
            annotation_id = str(annotation_id)
            previous_clip = used_ids.get(annotation_id)
            if previous_clip:
                raise SystemExit(
                    f"剧情注释 {annotation_id} 被重复绑定到 {previous_clip} 和 clip_{clip_index:02}。"
                )
            used_ids[annotation_id] = f"clip_{clip_index:02}"
            annotation = annotation_by_id.get(annotation_id)
            if not annotation:
                raise SystemExit(
                    f"高能片段 clip_{clip_index:02} 引用了不存在的剧情注释 {annotation_id}。"
                )
            annotation_start = seconds(annotation["start"])
            annotation_end = seconds(annotation["end"])
            if annotation_start < clip_start - 0.05 or annotation_end > clip_end + 0.05:
                raise SystemExit(
                    f"剧情注释 {annotation_id} 跨越了片段切点："
                    f"注释 {annotation_start:.3f}-{annotation_end:.3f}s，"
                    f"clip_{clip_index:02} 成片范围 {clip_start:.3f}-{clip_end:.3f}s。"
                )


def main() -> None:
    args = parse_args()
    plan_path = Path(args.plan).resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if not plan.get("annotation_only"):
        raise SystemExit("电视剧注释模式必须在计划中设置 annotation_only=true。")

    annotation_value = args.annotations or plan.get("annotation_file")
    if not annotation_value:
        raise SystemExit("计划缺少 annotation_file，或未提供 --annotations。")
    annotation_path = resolve_path(str(annotation_value), plan_path)
    if not annotation_path.is_file():
        raise SystemExit(f"注释 JSON 不存在：{annotation_path}")

    run_checked([sys.executable, str(PREFLIGHT_SCRIPT), "--plan", str(plan_path)])
    run_checked([sys.executable, str(ANNOTATION_VALIDATOR), str(annotation_path)])

    annotation_data = json.loads(annotation_path.read_text(encoding="utf-8"))
    annotations = annotation_data.get("annotations")
    if not isinstance(annotations, list) or not annotations:
        raise SystemExit("注释 JSON 必须包含非空 annotations 数组。")

    source, output, clips, duration = validate(plan, plan_path)
    validate_annotation_bindings(annotations, clips)
    timeline_segments: list[dict] = []
    for index, annotation in enumerate(annotations, start=1):
        text = str(annotation.get("text") or "").strip()
        if not text:
            raise SystemExit(f"注释 anno_{index:03} 缺少单行剧情简介。")
        start = seconds(annotation["start"])
        end = seconds(annotation["end"])
        if start < 0 or end <= start or end > duration + 0.05:
            raise SystemExit(
                f"注释 anno_{index:03} 超出成片时间线：{start:.3f}-{end:.3f}s，成片 {duration:.3f}s。"
            )
        timeline_segments.append({"start": annotation["start"], "end": annotation["end"], "text": text})

    render_plan = copy.deepcopy(plan)
    render_plan["source_video"] = str(source)
    render_plan["output_video"] = str(output)
    render_plan["caption_mode"] = "plot_summary"
    # 注释只交给 jianying_assistant 写入剪映草稿，绝不烧录进视频。
    render_plan["burn_captions"] = False
    render_plan["write_subtitles"] = False
    render_plan.pop("background_music", None)
    render_plan.pop("narration_audio", None)
    render_plan["narration"] = {}
    render_plan["mix"] = {
        "source_audio_mode": "keep_source",
        "source_volume": 1.0,
        "narration_volume": 0.0,
        "music_volume": 0.0,
    }

    with tempfile.TemporaryDirectory(prefix="yinghe-drama-annotation-") as temp_dir:
        temp_plan = Path(temp_dir) / "render_plan.json"
        temp_plan.write_text(json.dumps(render_plan, ensure_ascii=False, indent=2), encoding="utf-8")
        command = [sys.executable, str(BUILD_SCRIPT), "--plan", str(temp_plan)]
        if args.dry_run:
            print(" ".join(command))
            return
        run_checked(command)

    print(f"Clean edited video: {output}")
    print("注释未烧录；请使用 jianying_assistant 将 annotation_file 写入剪映草稿。")


if __name__ == "__main__":
    main()
