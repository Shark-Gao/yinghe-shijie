#!/usr/bin/env python3
"""根据可编辑 JSON 计划和 FFmpeg 构建 9:16 短视频 MP4。"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, help="剪辑计划 JSON。")
    parser.add_argument("--narration-audio", help="覆盖计划中的 narration_audio。")
    parser.add_argument("--narration-timing", help="包含每段 TTS 实测时长的 JSON 清单。")
    parser.add_argument("--subtitles-only", action="store_true", help="只写旁车 SRT，不渲染视频。")
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


TRAILING_SUBTITLE_PUNCTUATION = re.compile(
    r"[\s，。！？；：、,.!?;:…“”‘’\"'「」『』（）()【】\[\]《》]+$"
)


def subtitle_display_text(text: str) -> str:
    """清理字幕显示文本，但不改变 TTS 使用的标点。"""
    return TRAILING_SUBTITLE_PUNCTUATION.sub("", text.strip()).strip()


def load_narration_timing(path: Path | None) -> list[dict] | None:
    if not path:
        return None
    if not path.is_file():
        raise SystemExit(f"Narration timing manifest does not exist: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    segments = data.get("segments")
    if not isinstance(segments, list):
        raise SystemExit("Narration timing manifest needs a segments array.")
    return segments


def narration_windows(plan: dict, timing_segments: list[dict] | None) -> list[tuple[float, float]]:
    """返回成片时间线上的实际解说区间，优先使用 TTS 实测时长。"""
    planned = plan.get("narration", {}).get("segments", [])
    scheduled = timing_segments or planned
    windows: list[tuple[float, float]] = []
    for index, segment in enumerate(scheduled):
        if "start" not in segment:
            continue
        start = seconds(segment["start"])
        measured = float(segment.get("audio_duration", 0.0) or 0.0)
        if measured > 0:
            end = start + measured
        else:
            fallback = segment.get("end")
            if fallback is None and index < len(planned):
                fallback = planned[index].get("end")
            if fallback is None:
                continue
            end = seconds(fallback)
        if end > start:
            windows.append((max(0.0, start), end))
    return windows


def audio_envelope_expression(
    windows: list[tuple[float, float]],
    duration: float,
    fade_seconds: float,
) -> str:
    """为每个实际解说区间生成带淡入淡出的音量包络。"""
    terms: list[str] = []
    fade = max(0.0, float(fade_seconds))
    for start, end in windows:
        start = max(0.0, min(duration, start))
        end = max(0.0, min(duration, end))
        if end <= start:
            continue
        if fade <= 0:
            terms.append(f"if(between(t,{start:.3f},{end:.3f}),1,0)")
            continue
        edge = min(fade, (end - start) / 2.0)
        in_end = start + edge
        out_start = end - edge
        terms.append(
            "if(lt(t,{start:.3f}),0,"
            "if(lt(t,{in_end:.3f}),(t-{start:.3f})/{edge:.3f},"
            "if(lt(t,{out_start:.3f}),1,"
            "if(lt(t,{end:.3f}),({end:.3f}-t)/{edge:.3f},0))))".format(
                start=start,
                in_end=in_end,
                out_start=out_start,
                end=end,
                edge=edge,
            )
        )
    if not terms:
        return "0"
    expression = terms[0]
    for term in terms[1:]:
        expression = f"max({expression},{term})"
    return expression


def add_source_audio_ducking(
    filters: list[str],
    source_label: str,
    windows: list[tuple[float, float]],
    source_volume: float,
    duration: float,
    fade_seconds: float,
    source_under_narration_volume: float = 0.0,
) -> str:
    """保留非解说时段的原声，并在交界处用短淡入淡出切换。"""
    current = "sourcegap0"
    envelope = audio_envelope_expression(windows, duration, fade_seconds)
    under_volume = max(0.0, min(float(source_volume), float(source_under_narration_volume)))
    source_expression = f"({source_volume})*(1-({envelope}))+({under_volume})*({envelope})"
    filters.append(
        f"[{source_label}]volume='{source_expression}':eval=frame[{current}]"
    )
    return current


def validate_intro_source_audio(
    windows: list[tuple[float, float]],
    duration: float,
    deadline: float,
    minimum_gap: float,
) -> None:
    """确保开头 deadline 秒内有一段可听见的原视频音频。"""
    limit = min(duration, max(0.0, deadline))
    cursor = 0.0
    for start, end in windows:
        start = max(0.0, min(limit, start))
        end = max(0.0, min(limit, end))
        if start - cursor >= minimum_gap:
            return
        cursor = max(cursor, end)
    if limit - cursor >= minimum_gap:
        return
    raise SystemExit(
        f"The first {deadline:g} seconds need at least {minimum_gap:g} seconds of original audio between narration segments."
    )


def write_srt(plan: dict, path: Path, timing_segments: list[dict] | None = None) -> None:
    segments = plan.get("narration", {}).get("segments", [])
    plot_summary_mode = plan.get("caption_mode") == "plot_summary"
    rows = []
    subtitle_id = 1
    for segment_index, segment in enumerate(segments):
        text = segment.get("text", "").strip()
        if not text:
            continue
        if plot_summary_mode:
            compact = [subtitle_display_text(text)]
        else:
            # 不把小数点和型号中的句点拆开，例如 1.8%、ID.3、ID.4。
            pieces = [part.strip() for part in re.split(r"(?<=[。！？；…!?;])", text) if part.strip()]
            compact = []
            for piece in pieces:
                if len(piece) <= 22:
                    compact.append(piece)
                    continue
                compact.extend(part.strip() for part in re.split(r"(?<=[，、：,:])", piece) if part.strip())
            compact = [subtitle_display_text(part) for part in compact]
        compact = [part for part in compact if part]
        if not compact:
            continue
        start, end = seconds(segment["start"]), seconds(segment["end"])
        if timing_segments and segment_index < len(timing_segments):
            measured = float(timing_segments[segment_index].get("audio_duration", 0.0))
            if measured > 0:
                end = min(end, start + measured)
        if end <= start:
            continue
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
    timing_path = Path(args.narration_timing).resolve() if args.narration_timing else None
    timing_segments = load_narration_timing(timing_path)
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
        write_srt(plan, srt_path, timing_segments)
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
    source_audio_mode = str(mix.get("source_audio_mode", "static"))
    transition_fade = max(0.0, float(mix.get("audio_transition_fade_seconds", 0.0)))
    dynamic_source_audio = bool(narration_path and source_audio_mode == "play_between_narration")
    if source_audio_mode not in {"static", "play_between_narration", "keep_source"}:
        raise SystemExit("mix.source_audio_mode must be static, play_between_narration, or keep_source.")
    if plan.get("drama") and narration_path and source_audio_mode != "play_between_narration":
        raise SystemExit("Drama plans require mix.source_audio_mode=play_between_narration.")
    source_gap_volume = (
        float(mix["source_gap_volume"])
        if "source_gap_volume" in mix
        else (1.0 if dynamic_source_audio else background)
    )
    video_transition_fade = max(0.0, float(mix.get("video_transition_fade_seconds", 0.0)))
    output_resolution = str(plan.get("output_resolution", "")).strip()
    if output_resolution and not re.fullmatch(r"\d+[:x]\d+", output_resolution):
        raise SystemExit("output_resolution must look like 1920:1080 or 1920x1080.")
    output_scale = f",scale={output_resolution.replace('x', ':')}:flags=lanczos" if output_resolution else ""
    source_windows = narration_windows(plan, timing_segments) if dynamic_source_audio else []
    if dynamic_source_audio:
        validate_intro_source_audio(
            source_windows,
            duration,
            float(mix.get("source_audio_intro_deadline_seconds", 10.0)),
            float(mix.get("source_audio_intro_min_seconds", 0.5)),
        )
    include_source_audio = not narration_path or background > 0 or dynamic_source_audio
    filters, concat_inputs = [], []
    for i, clip in enumerate(clips):
        start, end = seconds(clip["source_start"]), seconds(clip["source_end"])
        focus = float(clip.get("focus_x", 0.5))
        layout = clip.get("layout", plan.get("layout", "contain_blur"))
        clip_duration = max(0.0, end - start)
        fade_in = bool(i > 0 and clips[i - 1].get("transition_after", False))
        fade_out = bool(clip.get("transition_after", False))
        fade_duration = min(video_transition_fade, clip_duration / 2.0)
        video_effects = ""
        if fade_duration > 0:
            if fade_in:
                video_effects += f",fade=t=in:st=0:d={fade_duration:.3f}:color=black"
            if fade_out:
                fade_start = max(0.0, clip_duration - fade_duration)
                video_effects += f",fade=t=out:st={fade_start:.3f}:d={fade_duration:.3f}:color=black"
        base = f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS,fps=30{video_effects}"
        if layout == "source":
            filters.append(f"{base}{output_scale},setsar=1,format=yuv420p[v{i}]")
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
        narration_filter = f"[{narration_input}:a]atrim=duration={duration},apad"
        if dynamic_source_audio and transition_fade > 0:
            narration_envelope = audio_envelope_expression(
                source_windows,
                duration,
                transition_fade,
            )
            narration_expression = f"({narration_volume})*({narration_envelope})"
            narration_filter += f",volume='{narration_expression}':eval=frame"
        else:
            narration_filter += f",volume={narration_volume}"
        filters.append(narration_filter + "[narr]")
        if dynamic_source_audio:
            source_label = add_source_audio_ducking(
                filters,
                "abase",
                source_windows,
                source_gap_volume,
                duration,
                transition_fade,
                float(mix.get("source_audio_under_narration_volume", 0.0)),
            )
            if music_label:
                filters.append(f"[{source_label}][music]amix=inputs=2:duration=first:normalize=0[bed]")
                source_label = "bed"
            filters.append(f"[{source_label}][narr]amix=inputs=2:duration=first:normalize=0[aout]")
        elif background <= 0 and not music_label:
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
        if plan.get("caption_mode") == "plot_summary":
            style = "FontName=Microsoft YaHei,FontSize=14,PrimaryColour=&H00FFFFFF,OutlineColour=&H00101010,BorderStyle=1,Outline=1.5,Shadow=0,Alignment=7,MarginL=80,MarginR=80,MarginV=40"
        else:
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
