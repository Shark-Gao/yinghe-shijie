#!/usr/bin/env python3
"""阻止没有通过成片前内容审查的短视频计划进入渲染。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_CHECKS = (
    "position_and_fact",
    "emotional_value",
    "conflict_and_hook",
    "answer_timing",
    "visual_evidence",
    "title_script_consistency",
    "safety_and_attribution",
)
REQUIRED_TEXT_FIELDS = (
    "one_line_question",
    "one_line_answer",
    "conflict",
    "emotional_value",
)
DRAMA_REQUIRED_TEXT_FIELDS = (
    "opening_stance_hook",
    "commentary_viewpoint",
    "discussion_conflict",
    "emotional_value",
)


def _seconds(value: str | float | int) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if ":" not in value:
        return float(value)
    hours, minutes, seconds = value.replace(",", ".").split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def _validate_drama_edit_integrity(plan: dict, plan_path: Path | None) -> None:
    clips = plan.get("clips")
    if not isinstance(clips, list) or not clips:
        raise SystemExit("禁止渲染：影视计划必须包含非空 clips 数组。")

    if bool(plan.get("annotation_only")):
        if plan.get("burn_captions"):
            raise SystemExit(
                "禁止渲染：annotation_only 电视剧计划不能把注释烧录进视频；请使用 jianying_assistant 添加可编辑注释。"
            )
        if plan.get("annotation_file") is None:
            raise SystemExit("禁止渲染：annotation_only 计划缺少 annotation_file。")
        edit_rules = plan.get("edit_rules")
        if not isinstance(edit_rules, dict):
            raise SystemExit("禁止渲染：annotation_only 计划缺少 edit_rules。")
        if edit_rules.get("source_overlap") is not False:
            raise SystemExit("禁止渲染：剧情注释模式必须设置 edit_rules.source_overlap=false。")
        if edit_rules.get("source_reuse") is not False:
            raise SystemExit("禁止渲染：剧情注释模式必须设置 edit_rules.source_reuse=false。")
        if edit_rules.get("direct_cut") is not True:
            raise SystemExit("禁止渲染：剧情注释模式必须设置 edit_rules.direct_cut=true。")

    source_ranges: list[tuple[float, float, dict, int]] = []
    output_ranges: list[tuple[float, float, dict, int]] = []
    output_cursor = 0.0
    for index, clip in enumerate(clips, start=1):
        if not isinstance(clip, dict):
            raise SystemExit(f"禁止渲染：clips[{index}] 必须是对象。")
        try:
            source_start = _seconds(clip["source_start"])
            source_end = _seconds(clip["source_end"])
        except (KeyError, TypeError, ValueError) as exc:
            raise SystemExit(f"禁止渲染：clips[{index}] 的源时间码无效。") from exc
        if source_end <= source_start:
            raise SystemExit(f"禁止渲染：clips[{index}] 的 source_end 必须晚于 source_start。")
        duration = source_end - source_start
        source_ranges.append((source_start, source_end, clip, index))
        output_ranges.append((output_cursor, output_cursor + duration, clip, index))
        output_cursor += duration

    for left_index, (left_start, left_end, left_clip, left_number) in enumerate(source_ranges):
        for right_start, right_end, right_clip, right_number in source_ranges[left_index + 1 :]:
            overlap = min(left_end, right_end) - max(left_start, right_start)
            if overlap <= 1e-6:
                continue
            raise SystemExit(
                "禁止渲染：片段存在源时间重叠，可能造成情节重复："
                f"clips[{left_number}] 与 clips[{right_number}] 重叠 {overlap:.3f} 秒。"
            )

    if not bool(plan.get("annotation_only")):
        return

    annotation_path = Path(str(plan.get("annotation_file")))
    if not annotation_path.is_absolute() and plan_path is not None:
        annotation_path = (plan_path.parent / annotation_path).resolve()
    if not annotation_path.is_file():
        raise SystemExit(f"禁止渲染：高能片段注释文件不存在：{annotation_path}")
    try:
        annotation_data = json.loads(annotation_path.read_text(encoding="utf-8"))
        annotations = annotation_data.get("annotations")
    except (OSError, json.JSONDecodeError, AttributeError) as exc:
        raise SystemExit(f"禁止渲染：无法读取 annotation_file：{annotation_path}") from exc
    if not isinstance(annotations, list):
        raise SystemExit("禁止渲染：annotation_file.annotations 必须是数组。")
    annotation_by_id = {
        item.get("id"): item for item in annotations if isinstance(item, dict) and item.get("id")
    }
    for output_start, output_end, clip, clip_number in output_ranges:
        if not clip.get("high_energy"):
            continue
        annotation_ids = clip.get("annotation_ids")
        if not isinstance(annotation_ids, list) or not annotation_ids:
            raise SystemExit(
                f"禁止渲染：高能片段 clips[{clip_number}] 必须绑定 annotation_ids，说明对应剧情。"
            )
        covered = False
        for annotation_id in annotation_ids:
            item = annotation_by_id.get(annotation_id)
            if not isinstance(item, dict):
                raise SystemExit(
                    f"禁止渲染：高能片段 clips[{clip_number}] 引用了不存在的注释 {annotation_id}。"
                )
            try:
                annotation_start = _seconds(item["start"])
                annotation_end = _seconds(item["end"])
            except (KeyError, TypeError, ValueError) as exc:
                raise SystemExit(f"禁止渲染：注释 {annotation_id} 的时间码无效。") from exc
            if annotation_end > output_start and annotation_start < output_end:
                covered = True
        if not covered:
            raise SystemExit(
                f"禁止渲染：高能片段 clips[{clip_number}] 的绑定注释没有落在该片段时间内。"
            )


def validate_preflight_review(plan: dict, plan_path: Path | None = None) -> dict:
    review = plan.get("preflight_review")
    if not isinstance(review, dict):
        raise SystemExit(
            "禁止渲染：编辑计划缺少 preflight_review。请先完成成片前内容审查。"
        )
    if review.get("status") != "passed":
        raise SystemExit(
            "禁止渲染：preflight_review.status 不是 passed。请先修订计划并完成内容预审。"
        )
    if review.get("review_scope") != "content_before_render":
        raise SystemExit(
            "禁止渲染：预审必须标记为 content_before_render，不能用成片后的复盘代替。"
        )
    for field in REQUIRED_TEXT_FIELDS:
        value = review.get(field)
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f"禁止渲染：preflight_review 缺少有效字段 {field}。")
    checks = review.get("checks")
    if not isinstance(checks, dict):
        raise SystemExit("禁止渲染：preflight_review.checks 缺失。")
    failed = [name for name in REQUIRED_CHECKS if checks.get(name) != "pass"]
    if failed:
        raise SystemExit(
            "禁止渲染：以下预审项目未通过：" + ", ".join(failed)
        )
    alignment = plan.get("visual_alignment")
    if isinstance(alignment, dict) and alignment.get("required"):
        anchors = alignment.get("anchors")
        if not isinstance(anchors, list) or not anchors:
            raise SystemExit("禁止渲染：visual_alignment.required=true，但没有画面锚点。")
        required_anchor_fields = ("id", "anchor_text", "visual_start", "visual_end", "segment_id", "source_evidence")
        for index, anchor in enumerate(anchors, start=1):
            if not isinstance(anchor, dict):
                raise SystemExit(f"禁止渲染：画面锚点 {index} 不是对象。")
            missing = [field for field in required_anchor_fields if not str(anchor.get(field, "")).strip()]
            if missing:
                raise SystemExit(
                    f"禁止渲染：画面锚点 {anchor.get('id', index)} 缺少字段：{', '.join(missing)}。"
                )
    drama = plan.get("drama")
    if drama is not None:
        if not isinstance(drama, dict):
            raise SystemExit("禁止渲染：drama 必须是对象，不能用非结构化备注代替剧情审核。")
        for field in DRAMA_REQUIRED_TEXT_FIELDS:
            value = drama.get(field)
            if not isinstance(value, str) or not value.strip():
                raise SystemExit(f"禁止渲染：影视解说计划缺少有效字段 drama.{field}。")
        mix = plan.get("mix")
        annotation_only = bool(plan.get("annotation_only"))
        required_audio_mode = "keep_source" if annotation_only else "play_between_narration"
        if not isinstance(mix, dict) or mix.get("source_audio_mode") != required_audio_mode:
            raise SystemExit(
                "禁止渲染：影视计划必须启用 "
                f"mix.source_audio_mode={required_audio_mode}。"
            )
        narration = plan.get("narration")
        if annotation_only and isinstance(narration, dict) and narration.get("segments"):
            raise SystemExit("禁止渲染：annotation_only 计划不能包含中文配音 narration.segments。")
        _validate_drama_edit_integrity(plan, plan_path)
    return review


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, help="编辑计划 JSON 路径。")
    args = parser.parse_args()
    plan_path = Path(args.plan).resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    validate_preflight_review(plan, plan_path)
    print(f"Preflight review passed: {plan_path}")


if __name__ == "__main__":
    main()
