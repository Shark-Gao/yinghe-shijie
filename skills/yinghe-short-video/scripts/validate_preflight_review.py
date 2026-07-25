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


def validate_preflight_review(plan: dict) -> dict:
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
    drama = plan.get("drama")
    if drama is not None:
        if not isinstance(drama, dict):
            raise SystemExit("禁止渲染：drama 必须是对象，不能用非结构化备注代替剧情审核。")
        for field in DRAMA_REQUIRED_TEXT_FIELDS:
            value = drama.get(field)
            if not isinstance(value, str) or not value.strip():
                raise SystemExit(f"禁止渲染：影视解说计划缺少有效字段 drama.{field}。")
        mix = plan.get("mix")
        if not isinstance(mix, dict) or mix.get("source_audio_mode") != "play_between_narration":
            raise SystemExit(
                "禁止渲染：影视解说计划必须启用 mix.source_audio_mode=play_between_narration。"
            )
    return review


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, help="编辑计划 JSON 路径。")
    args = parser.parse_args()
    plan_path = Path(args.plan).resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    validate_preflight_review(plan)
    print(f"Preflight review passed: {plan_path}")


if __name__ == "__main__":
    main()
