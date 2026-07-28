#!/usr/bin/env python3
"""只重生成关系图开头口播，并复用已验收的后续解说音频。"""
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--old-audio", required=True)
    parser.add_argument("--output-audio", required=True)
    parser.add_argument("--output-timing", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    plan_path = Path(args.plan).resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    output_audio = Path(args.output_audio).resolve()
    output_timing = Path(args.output_timing).resolve()
    old_audio = Path(args.old_audio).resolve()
    if not old_audio.is_file():
        raise SystemExit(f"已验收的旧解说音频不存在：{old_audio}")

    project_root = Path(__file__).resolve().parents[3]
    renderer = project_root / "skills" / "generate-narration-audio" / "scripts" / "render_cosyvoice_timeline.py"
    cosyvoice_python = project_root / "tools" / "CosyVoice" / ".venv" / "Scripts" / "python.exe"
    duration = max(float(item["end"].split(":")[-1]) for item in plan["narration"]["segments"])
    if len(plan["narration"]["segments"]) > 1:
        last = plan["narration"]["segments"][-1]["end"].split(":")
        duration = int(last[0]) * 3600 + int(last[1]) * 60 + float(last[2])
    intro = plan["narration"]["segments"][0]
    timeline_data = {
        "version": 1,
        "source_plan": plan_path.name,
        "output_audio": str(output_audio),
        "mode": "short_video_chinese_narration",
        "provider": "cosyvoice",
        "voice": plan["narration"].get("voice", "中文女"),
        "rate": plan["narration"].get("rate", "+12%"),
        "video_duration": f"{duration:.3f}",
        "cosyvoice_model_dir": plan["narration"].get("model_dir", "tools/CosyVoice/pretrained_models/CosyVoice-300M-SFT"),
        "cosyvoice_mode": plan["narration"].get("mode", "sft"),
        "speed": plan["narration"].get("speed", 1.12),
        "segments": [{"id": "seg_001", **intro}],
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
        temp_timeline = Path(handle.name)
        json.dump(timeline_data, handle, ensure_ascii=False, indent=2)
    temp_manifest = output_timing.with_name(output_timing.stem + "_intro_only.json")
    try:
        subprocess.run(
            [
                str(cosyvoice_python),
                str(renderer),
                "--timeline",
                str(temp_timeline),
                "--segment-manifest",
                str(temp_manifest),
            ],
            check=True,
        )
        intro_manifest = json.loads(temp_manifest.read_text(encoding="utf-8"))
        old_timing_path = old_audio.with_name(old_audio.stem + "分段时长.json")
        if not old_timing_path.is_file():
            raise SystemExit(f"旧解说时长清单不存在：{old_timing_path}")
        old_timing = json.loads(old_timing_path.read_text(encoding="utf-8"))
        old_first = dict(old_timing["segments"][0])
        old_first["start"] = "00:00:16.000"
        old_first["end"] = "00:00:26.000"
        merged = {
            "version": 1,
            "timeline": str(plan_path.with_name(plan_path.stem + "_中文解说时间线.json")),
            "provider": "cosyvoice",
            "output_audio": str(output_audio),
            "segments": intro_manifest["segments"] + [old_first] + old_timing["segments"][1:],
        }
        output_timing.parent.mkdir(parents=True, exist_ok=True)
        output_timing.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

        duration_arg = f"{duration:.3f}"
        first_duration = float(old_timing["segments"][0].get("audio_duration", 8.1))
        filter_complex = (
            f"[0:a]volume='if(between(t,0,18),0,1)'[old];"
            f"[0:a]atrim=start=8:end={8 + first_duration:.3f},asetpts=PTS-STARTPTS,adelay=8000|8000[plotintro];"
            f"[1:a]atrim=duration={duration_arg},apad[intro];"
            "[old][plotintro][intro]amix=inputs=3:duration=longest:normalize=0[mix]"
        )
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(old_audio),
                "-i",
                str(output_audio),
                "-filter_complex",
                filter_complex,
                "-map",
                "[mix]",
                "-t",
                duration_arg,
                "-ac",
                "2",
                "-ar",
                "44100",
                "-codec:a",
                "libmp3lame",
                "-b:a",
                "192k",
                str(output_audio.with_suffix(".merged.mp3")),
            ],
            check=True,
        )
        merged_audio = output_audio.with_suffix(".merged.mp3")
        merged_audio.replace(output_audio)
        print(output_audio)
        print(output_timing)
    finally:
        temp_timeline.unlink(missing_ok=True)
        temp_manifest.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
