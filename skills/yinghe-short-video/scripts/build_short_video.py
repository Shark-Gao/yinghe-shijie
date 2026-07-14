#!/usr/bin/env python3
"""Build a 9:16 short-video MP4 from an editable JSON plan and FFmpeg."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, help="Edit-plan JSON.")
    parser.add_argument("--narration-audio", help="Override narration_audio in the plan.")
    parser.add_argument("--subtitles-only", action="store_true", help="Write the sidecar SRT without rendering video.")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def seconds(value: str | float | int) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if ":" not in value:
        return float(value)
    h, m, s = value.replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def srt_time(value: float) -> str:
    ms = round(value * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def esc_filter_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace(":", r"\:").replace("'", r"\'")


def write_srt(plan: dict, path: Path) -> None:
    segments = plan.get("narration", {}).get("segments", [])
    rows = []
    subtitle_id = 1
    for segment in segments:
        text = segment.get("text", "").strip()
        if not text:
            continue
        pieces = [part.strip() for part in re.split(r"(?<=[。！？；])", text) if part.strip()]
        compact = []
        for piece in pieces:
            if len(piece) <= 22:
                compact.append(piece)
                continue
            compact.extend(part.strip() for part in re.split(r"(?<=[，、：])", piece) if part.strip())
        start, end = seconds(segment["start"]), seconds(segment["end"])
        weights = [max(1, len(re.sub(r"[，。！？；、：]", "", part))) for part in compact]
        total_weight = sum(weights)
        current = start
        for index, part in enumerate(compact):
            next_time = end if index == len(compact) - 1 else current + (end - start) * weights[index] / total_weight
            rows.extend([str(subtitle_id), f"{srt_time(current)} --> {srt_time(next_time)}", part, ""])
            subtitle_id += 1
            current = next_time
    path.write_text("\n".join(rows), encoding="utf-8")


def validate(plan: dict, plan_path: Path) -> tuple[Path, Path, list[dict], float]:
    for key in ("source_video", "output_video", "clips"):
        if not plan.get(key):
            raise SystemExit(f"Plan is missing {key}.")
    source = Path(plan["source_video"])
    if not source.is_absolute():
        source = (plan_path.parent / source).resolve()
    output = Path(plan["output_video"])
    if not output.is_absolute():
        output = (plan_path.parent / output).resolve()
    if not source.is_file():
        raise SystemExit(f"Source video does not exist: {source}")
    clips = plan["clips"]
    default_layout = plan.get("layout", "source")
    if default_layout not in {"source", "contain_blur", "fill_crop"}:
        raise SystemExit("layout must be source, contain_blur, or fill_crop.")
    duration = 0.0
    for index, clip in enumerate(clips, 1):
        try:
            start, end = seconds(clip["source_start"]), seconds(clip["source_end"])
        except KeyError as exc:
            raise SystemExit(f"Clip {index} is missing {exc.args[0]}.") from exc
        if end <= start:
            raise SystemExit(f"Clip {index} ends before it starts.")
        focus = float(clip.get("focus_x", 0.5))
        if not 0 <= focus <= 1:
            raise SystemExit(f"Clip {index} focus_x must be between 0 and 1.")
        if clip.get("layout", default_layout) not in {"source", "contain_blur", "fill_crop"}:
            raise SystemExit(f"Clip {index} has an unsupported layout.")
        duration += end - start
    return source, output, clips, duration


def main() -> None:
    args = parse_args()
    plan_path = Path(args.plan).resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    source, output, clips, duration = validate(plan, plan_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    narration = args.narration_audio or plan.get("narration_audio")
    narration_path = Path(narration) if narration else None
    if narration_path and not narration_path.is_absolute():
        narration_path = ((Path.cwd() if args.narration_audio else plan_path.parent) / narration_path).resolve()
    if narration_path and not narration_path.is_file():
        raise SystemExit(f"Narration audio does not exist: {narration_path}")
    music = plan.get("background_music")
    music_path = Path(music) if music else None
    if music_path and not music_path.is_absolute():
        project_relative = (Path.cwd() / music_path).resolve()
        music_path = project_relative if project_relative.is_file() else (plan_path.parent / music_path).resolve()
    if music_path and not music_path.is_file():
        raise SystemExit(f"Background music does not exist: {music_path}")
    srt_path = output.with_suffix(".srt")
    write_subtitles = plan.get("write_subtitles", True) and bool(plan.get("narration", {}).get("segments"))
    if write_subtitles:
        write_srt(plan, srt_path)
    if args.subtitles_only:
        if not write_subtitles:
            raise SystemExit("No narration segments are available for subtitle generation.")
        print(srt_path)
        return

    mix = plan.get("mix", {})
    background = float(mix.get("source_volume", 0.0))
    narration_volume = float(mix.get("narration_volume", 1.0))
    music_volume = float(mix.get("music_volume", 1.0))
    music_fade = float(mix.get("music_fade_seconds", 0.0))
    include_source_audio = not narration_path or background > 0
    filters, concat_inputs = [], []
    for i, clip in enumerate(clips):
        start, end = seconds(clip["source_start"]), seconds(clip["source_end"])
        focus = float(clip.get("focus_x", 0.5))
        layout = clip.get("layout", plan.get("layout", "contain_blur"))
        base = f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS,fps=30"
        if layout == "source":
            filters.append(f"{base},setsar=1,format=yuv420p[v{i}]")
        elif layout == "fill_crop":
            filters.append(f"{base},scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920:(in_w-out_w)*{focus}:0,setsar=1,format=yuv420p[v{i}]")
        else:
            filters.extend([
                f"{base},split=2[bgsrc{i}][fgsrc{i}]",
                f"[bgsrc{i}]scale=180:320:force_original_aspect_ratio=increase,crop=180:320,boxblur=10:5,scale=1080:1920[bg{i}]",
                f"[fgsrc{i}]scale=1080:1920:force_original_aspect_ratio=decrease[fg{i}]",
                f"[bg{i}][fg{i}]overlay=(W-w)/2:(H-h)/2,setsar=1,format=yuv420p[v{i}]",
            ])
        if include_source_audio:
            filters.append(f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}]")
            concat_inputs.append(f"[v{i}][a{i}]")
        else:
            concat_inputs.append(f"[v{i}]")
    if include_source_audio:
        filters.append("".join(concat_inputs) + f"concat=n={len(clips)}:v=1:a=1[vbase][abase]")
    else:
        filters.append("".join(concat_inputs) + f"concat=n={len(clips)}:v=1:a=0[vbase]")

    narration_input = 1 if narration_path else None
    music_input = (1 if narration_input is None else 2) if music_path else None
    music_label = None
    if music_path:
        music_filter = f"[{music_input}:a]atrim=duration={duration},asetpts=PTS-STARTPTS"
        if music_fade > 0:
            fade_out_start = max(0.0, duration - music_fade)
            music_filter += f",afade=t=in:st=0:d={music_fade},afade=t=out:st={fade_out_start}:d={music_fade}"
        filters.append(music_filter + f",volume={music_volume}[music]")
        music_label = "music"

    final_video, final_audio = "vbase", "abase"
    if narration_path:
        narration_filter = f"[{narration_input}:a]atrim=duration={duration},apad,volume={narration_volume}"
        filters.append(narration_filter + "[narr]")
        if background <= 0 and not music_label:
            filters.append("[narr]anull[aout]")
        elif background <= 0:
            filters.extend([
                "[music][narr]amix=inputs=2:duration=first:normalize=0[aout]",
            ])
        else:
            filters.append(f"[abase]volume={background}[sourcebg]")
            if music_label:
                filters.append("[sourcebg][music]amix=inputs=2:duration=first:normalize=0[bed]")
            else:
                filters.append("[sourcebg]anull[bed]")
            filters.extend([
                "[bed][narr]amix=inputs=2:duration=first:normalize=0[aout]",
            ])
        final_audio = "aout"
    elif music_label:
        if include_source_audio and background > 0:
            filters.append(f"[abase]volume={background}[sourcebg]")
            filters.append("[sourcebg][music]amix=inputs=2:duration=first:normalize=0[aout]")
            final_audio = "aout"
        else:
            final_audio = music_label

    if plan.get("burn_captions", False) and write_subtitles:
        style = "FontName=Microsoft YaHei,FontSize=11,PrimaryColour=&H00FFFFFF,OutlineColour=&H00101010,BorderStyle=1,Outline=1.5,Shadow=0,Alignment=2,MarginV=100"
        filters.append(f"[{final_video}]subtitles=filename='{esc_filter_path(srt_path)}':charenc=UTF-8:force_style='{style}'[vout]")
        final_video = "vout"

    temporary_output = output.with_name(f"{output.stem}.{os.getpid()}.partial{output.suffix}")
    cmd = ["ffmpeg", "-y", "-i", str(source)]
    if narration_path:
        cmd.extend(["-i", str(narration_path)])
    if music_path:
        cmd.extend(["-stream_loop", "-1", "-i", str(music_path)])
    cmd.extend(["-filter_complex", ";".join(filters), "-map", f"[{final_video}]", "-map", f"[{final_audio}]", "-t", f"{duration:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k", str(temporary_output)])
    if args.dry_run:
        print(" ".join(cmd))
        return
    subprocess.run(cmd, check=True)
    temporary_output.replace(output)
    print(output)
    if srt_path.exists():
        print(srt_path)


if __name__ == "__main__":
    main()
