#!/usr/bin/env python3
"""Validate 硬核视界 overlay annotation JSON files."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


TIME_RE = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}$")
ID_RE = re.compile(r"^anno_\d{3}$")

TOP_LEVEL_KEYS = {"version", "source_subtitle", "target_video", "notes", "annotations"}
ANNOTATION_KEYS = {
    "id",
    "start",
    "end",
    "type",
    "text",
    "subtext",
    "position",
    "x",
    "y",
    "layer",
    "style",
    "motion",
    "visual_hint",
    "avoid",
}
TYPES = {"data", "term", "callout", "principle", "comparison", "chapter"}
POSITIONS = {"top_center", "center"}
STYLES = {"tech_label", "data_badge", "arrow_callout"}
MOTIONS = {"fade", "none"}
AVOID_VALUES = {"subtitle", "face", "map", "diagram", "core_subject"}
MIN_ANNOTATIONS = 8
MAX_ANNOTATIONS = 120
MIN_DURATION_MS = 1_500
MAX_DURATION_MS = 5_000


def parse_time(value: str) -> int:
    hours, minutes, rest = value.split(":")
    seconds, millis = rest.split(".")
    return (
        int(hours) * 3_600_000
        + int(minutes) * 60_000
        + int(seconds) * 1_000
        + int(millis)
    )


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return [f"invalid JSON: {exc}"]

    require(isinstance(data, dict), errors, "top level must be an object")
    if not isinstance(data, dict):
        return errors

    missing_top = sorted(TOP_LEVEL_KEYS - set(data))
    extra_top = sorted(set(data) - TOP_LEVEL_KEYS)
    require(not missing_top, errors, f"missing top-level keys: {missing_top}")
    require(not extra_top, errors, f"extra top-level keys: {extra_top}")
    require(data.get("version") == 1, errors, "version must be integer 1")
    require(isinstance(data.get("source_subtitle"), str) and data.get("source_subtitle"), errors, "source_subtitle must be a non-empty string")
    require(isinstance(data.get("target_video"), str), errors, "target_video must be a string")
    require(isinstance(data.get("notes"), str), errors, "notes must be a string")

    annotations = data.get("annotations")
    require(isinstance(annotations, list), errors, "annotations must be an array")
    if not isinstance(annotations, list):
        return errors
    require(
        MIN_ANNOTATIONS <= len(annotations) <= MAX_ANNOTATIONS,
        errors,
        f"annotations must contain {MIN_ANNOTATIONS}-{MAX_ANNOTATIONS} items",
    )

    seen_ids: set[str] = set()
    previous_start = -1
    for index, item in enumerate(annotations, start=1):
        prefix = f"annotations[{index}]"
        require(isinstance(item, dict), errors, f"{prefix} must be an object")
        if not isinstance(item, dict):
            continue

        missing = sorted(ANNOTATION_KEYS - set(item))
        extra = sorted(set(item) - ANNOTATION_KEYS)
        require(not missing, errors, f"{prefix} missing keys: {missing}")
        require(not extra, errors, f"{prefix} extra keys: {extra}")

        anno_id = item.get("id")
        require(isinstance(anno_id, str) and bool(ID_RE.match(anno_id)), errors, f"{prefix}.id must match anno_001")
        require(anno_id not in seen_ids, errors, f"{prefix}.id is duplicated")
        if isinstance(anno_id, str):
            seen_ids.add(anno_id)

        start = item.get("start")
        end = item.get("end")
        require(isinstance(start, str) and bool(TIME_RE.match(start)), errors, f"{prefix}.start must be HH:MM:SS.mmm")
        require(isinstance(end, str) and bool(TIME_RE.match(end)), errors, f"{prefix}.end must be HH:MM:SS.mmm")
        if isinstance(start, str) and isinstance(end, str) and TIME_RE.match(start) and TIME_RE.match(end):
            start_ms = parse_time(start)
            end_ms = parse_time(end)
            duration_ms = end_ms - start_ms
            require(end_ms > start_ms, errors, f"{prefix}.end must be later than start")
            require(
                MIN_DURATION_MS <= duration_ms <= MAX_DURATION_MS,
                errors,
                f"{prefix} duration must be {MIN_DURATION_MS / 1000:g}-{MAX_DURATION_MS / 1000:g} seconds",
            )
            require(start_ms >= previous_start, errors, f"{prefix}.start must be sorted ascending")
            previous_start = start_ms

        require(item.get("type") in TYPES, errors, f"{prefix}.type has unsupported value")
        require(isinstance(item.get("text"), str) and item.get("text"), errors, f"{prefix}.text must be a non-empty string")
        require(isinstance(item.get("subtext"), str), errors, f"{prefix}.subtext must be a string")
        require(item.get("position") in POSITIONS, errors, f"{prefix}.position must be top_center or center")
        require(isinstance(item.get("x"), int), errors, f"{prefix}.x must be an integer Jianying coordinate")
        require(isinstance(item.get("y"), int), errors, f"{prefix}.y must be an integer Jianying coordinate")
        require(isinstance(item.get("layer"), int), errors, f"{prefix}.layer must be an integer")
        require(item.get("style") in STYLES, errors, f"{prefix}.style has unsupported value")
        require(item.get("motion") in MOTIONS, errors, f"{prefix}.motion has unsupported value")
        require(isinstance(item.get("visual_hint"), str), errors, f"{prefix}.visual_hint must be a string")

        avoid = item.get("avoid")
        require(isinstance(avoid, list), errors, f"{prefix}.avoid must be an array")
        if isinstance(avoid, list):
            for value in avoid:
                require(value in AVOID_VALUES, errors, f"{prefix}.avoid has unsupported value: {value}")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_annotations_json.py <annotation-json>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    errors = validate(path)
    if errors:
        print(f"INVALID: {path}")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"OK: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
