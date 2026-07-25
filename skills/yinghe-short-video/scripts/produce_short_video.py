#!/usr/bin/env python3
"""根据一份剪辑计划 JSON 生成中文解说并构建最终竖版 MP4。"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from build_short_video import seconds, validate
from validate_preflight_review import validate_preflight_review


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, help="包含解说分段的剪辑计划 JSON。")
    parser.add_argument("--tts-renderer", help="render_timeline_tts.py 路径，通常从项目根目录自动推断。")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def resolve_project_path(value: str, plan_path: Path) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    for parent in (plan_path.parent, *plan_path.parents):
        resolved = (parent / candidate).resolve()
        if resolved.exists():
            return resolved
    return (plan_path.parent / candidate).resolve()


def find_tts_renderer(plan_path: Path, supplied: str | None, provider: str) -> Path:
    if supplied:
        candidate = Path(supplied).resolve()
        if candidate.is_file():
            return candidate
    if provider == "cosyvoice":
        for parent in (plan_path.parent, *plan_path.parents):
            candidate = parent / "skills" / "generate-narration-audio" / "scripts" / "render_cosyvoice_timeline.py"
            if candidate.is_file():
                return candidate
        raise SystemExit("找不到 render_cosyvoice_timeline.py。请确认项目技能文件完整。")
    for parent in (plan_path.parent, *plan_path.parents):
        candidate = parent / "skills" / "generate-narration-audio" / "scripts" / "render_timeline_tts.py"
        if candidate.is_file():
            return candidate
    raise SystemExit("Cannot find render_timeline_tts.py. Pass --tts-renderer with its path.")


def find_tts_python(plan_path: Path, provider: str, narration: dict) -> Path:
    if provider != "cosyvoice":
        return Path(sys.executable)
    configured = narration.get("python") or narration.get("python_path")
    if configured:
        candidate = resolve_project_path(str(configured), plan_path)
        if candidate.is_file():
            return candidate
        raise SystemExit(f"CosyVoice Python 不存在：{candidate}")
    for parent in (plan_path.parent, *plan_path.parents):
        candidate = parent / "tools" / "CosyVoice" / ".venv" / "Scripts" / "python.exe"
        if candidate.is_file():
            return candidate
    raise SystemExit("找不到 CosyVoice 虚拟环境 Python。请在 narration.python 中填写路径。")


def main() -> None:
    args = parse_args()
    plan_path = Path(args.plan).resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    validate_preflight_review(plan)
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
    timing = output.with_name(f"{output.stem}_中文解说分段时长.json")
    provider = str(narration.get("provider") or "edge").lower()
    if provider not in {"edge", "cosyvoice"}:
        raise SystemExit("narration.provider 只支持 edge 或 cosyvoice。")
    cosyvoice_model_dir = narration.get("model_dir") or narration.get("cosyvoice_model_dir")
    if provider == "cosyvoice" and not cosyvoice_model_dir:
        raise SystemExit("使用 CosyVoice 时，narration.model_dir 不能为空。")
    default_voice = "中文男" if provider == "cosyvoice" else "zh-CN-YunyangNeural"
    data = {
        "version": 1,
        "source_plan": plan_path.name,
        "output_audio": str(audio),
        "mode": "short_video_chinese_narration",
        "provider": provider,
        "voice": narration.get("voice", default_voice),
        "rate": narration.get("rate", "+0%"),
        "video_duration": f"{duration:.3f}",
        "segments": [{"id": f"seg_{index:03}", **segment} for index, segment in enumerate(segments, 1)],
    }
    if provider == "cosyvoice":
        data.update(
            {
                "cosyvoice_model_dir": str(cosyvoice_model_dir),
                "cosyvoice_mode": narration.get("mode", "sft"),
                "speed": narration.get("speed"),
                "prompt_audio": narration.get("prompt_audio"),
                "prompt_text": narration.get("prompt_text"),
                "instruction": narration.get("instruction"),
            }
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    timeline.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    renderer = find_tts_renderer(plan_path, args.tts_renderer, provider)
    tts_python = find_tts_python(plan_path, provider, narration)
    render = [
        str(tts_python),
        str(renderer),
        "--timeline",
        str(timeline),
        "--segment-manifest",
        str(timing),
    ]
    build = [
        sys.executable,
        str(Path(__file__).with_name("build_short_video.py")),
        "--plan",
        str(plan_path),
        "--narration-audio",
        str(audio),
        "--narration-timing",
        str(timing),
    ]
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
