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
