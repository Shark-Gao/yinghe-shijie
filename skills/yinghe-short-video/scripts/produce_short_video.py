#!/usr/bin/env python3
"""Render narration and build a finished vertical MP4 from one edit-plan JSON."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from build_short_video import seconds, validate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, help="Edit-plan JSON with narration segments.")
    parser.add_argument("--tts-renderer", help="Path to render_timeline_tts.py. Usually inferred from the project root.")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def find_tts_renderer(plan_path: Path, supplied: str | None) -> Path:
    if supplied:
        candidate = Path(supplied).resolve()
        if candidate.is_file():
            return candidate
    for parent in (plan_path.parent, *plan_path.parents):
        candidate = parent / "skills" / "generate-narration-audio" / "scripts" / "render_timeline_tts.py"
        if candidate.is_file():
            return candidate
    raise SystemExit("Cannot find render_timeline_tts.py. Pass --tts-renderer with its path.")


def main() -> None:
    args = parse_args()
    plan_path = Path(args.plan).resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    source, output, clips, duration = validate(plan, plan_path)
    narration = plan.get("narration", {})
    segments = narration.get("segments", [])
    if not segments:
        raise SystemExit("The plan needs narration.segments to create a Chinese narration track.")
    final_end = max(seconds(segment["end"]) for segment in segments)
    if final_end > duration + 0.05:
        raise SystemExit("Narration extends beyond the assembled video duration.")

    timeline = output.with_name(f"{output.stem}_中文解说时间线.json")
    audio = output.with_name(f"{output.stem}_中文解说.mp3")
    data = {
        "version": 1,
        "source_plan": plan_path.name,
        "output_audio": str(audio),
        "mode": "short_video_chinese_narration",
        "voice": narration.get("voice", "zh-CN-YunyangNeural"),
        "rate": narration.get("rate", "+0%"),
        "video_duration": f"{duration:.3f}",
        "segments": [{"id": f"seg_{index:03}", **segment} for index, segment in enumerate(segments, 1)],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    timeline.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    renderer = find_tts_renderer(plan_path, args.tts_renderer)
    render = [sys.executable, str(renderer), "--timeline", str(timeline)]
    build = [sys.executable, str(Path(__file__).with_name("build_short_video.py")), "--plan", str(plan_path), "--narration-audio", str(audio)]
    if args.dry_run:
        print(" ".join(render))
        print(" ".join(build))
        return
    subprocess.run(render, check=True)
    subprocess.run(build, check=True)
    check = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(output)], check=True, capture_output=True, text=True)
    print(f"Final video: {output}")
    print(f"Duration: {check.stdout.strip()} seconds")


if __name__ == "__main__":
    main()
