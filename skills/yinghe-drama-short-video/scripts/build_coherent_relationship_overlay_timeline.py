#!/usr/bin/env python3
"""生成少切段、原创视觉叠加原视频的电视剧解说时间线。"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from build_original_led_evidence_timeline import (
    FPS,
    HEIGHT,
    SAMPLE_RATE,
    WIDTH,
    hms,
    make_relationship,
    make_source_segment,
    quote_concat_path,
    run,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-video", required=True)
    parser.add_argument("--source-subtitle", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--base-name", required=True)
    parser.add_argument("--output-video", required=True)
    parser.add_argument("--output-plan", required=True)
    parser.add_argument(
        "--relationship-pause-seconds",
        type=float,
        default=0.0,
        help="在剧情时间线前增加暂停的原创说明段；说明段使用冻结画面和静音原声。",
    )
    parser.add_argument(
        "--no-relationship-graph",
        action="store_true",
        help="不生成、不叠加前置原创视觉，也不生成对应的专属口播。",
    )
    return parser.parse_args()


def make_source_with_relationship_overlay(
    source: Path,
    graph: Path,
    output: Path,
    start: float,
    end: float,
    overlay_duration: float,
) -> None:
    duration = end - start
    common_video = (
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS},format=yuv420p"
    )
    graph_filter = (
        "[1:v]scale=1260:-1,format=rgba,colorchannelmixer=aa=0.72[graph];"
        f"[0:v]{common_video}[base];"
        f"[base][graph]overlay=(W-w)/2:(H-h)/2:enable='between(t,0,{overlay_duration:.3f})'[v]"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-ss",
            f"{start:.3f}",
            "-t",
            f"{duration:.3f}",
            "-i",
            str(source),
            "-loop",
            "1",
            "-i",
            str(graph),
            "-filter_complex",
            graph_filter,
            "-map",
            "[v]",
            "-map",
            "0:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            str(SAMPLE_RATE),
            "-ac",
            "2",
            "-t",
            f"{duration:.3f}",
            "-shortest",
            str(output),
        ]
    )


def make_paused_relationship_intro(
    source: Path,
    graph: Path,
    output: Path,
    source_frame_time: float,
    duration: float,
) -> None:
    """生成冻结画面的原创视觉前置段，避免说明时剧情继续播放。"""
    frame_path = output.with_suffix(".freeze.png")
    common_video = (
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p"
    )
    run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-ss", f"{source_frame_time:.3f}",
            "-i", str(source), "-frames:v", "1", "-vf", common_video, str(frame_path),
        ]
    )
    graph_filter = (
        "[0:v]format=rgba[base];"
        "[1:v]scale=1260:-1,format=rgba,colorchannelmixer=aa=0.72[graph];"
        "[base][graph]overlay=(W-w)/2:(H-h)/2[v]"
    )
    try:
        run(
            [
                "ffmpeg", "-y", "-loglevel", "error",
                "-loop", "1", "-i", str(frame_path),
                "-loop", "1", "-i", str(graph),
                "-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate={SAMPLE_RATE}",
                "-filter_complex", graph_filter, "-map", "[v]", "-map", "2:a",
                "-t", f"{duration:.3f}", "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), "-fps_mode", "cfr",
                "-c:a", "aac", "-b:a", "192k",
                "-ar", str(SAMPLE_RATE), "-ac", "2", str(output),
            ]
        )
    finally:
        frame_path.unlink(missing_ok=True)


def main() -> None:
    args = parse_args()
    source = Path(args.source_video).resolve()
    subtitle = Path(args.source_subtitle).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if not source.is_file():
        raise SystemExit(f"原始视频不存在：{source}")
    if not subtitle.is_file():
        raise SystemExit(f"字幕文件不存在：{subtitle}")

    asset_dir = output_dir / f"{args.base_name}_原创图卡"
    work_dir = output_dir / f".{args.base_name}_连贯时间线_work"
    asset_dir.mkdir(parents=True, exist_ok=True)
    if work_dir.exists():
        import shutil

        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    graph_path = asset_dir / "01_人物关系_半透明叠加.png"
    relationship_enabled = not args.no_relationship_graph
    if relationship_enabled:
        make_relationship(graph_path, 1)
    relationship_pause = max(0.0, float(args.relationship_pause_seconds)) if relationship_enabled else 0.0

    # 只保留四个较完整的剧情块，避免每几秒在原剧和图示之间来回跳。
    specs = [
        {
            "key": "01_起因与接手",
            "start": 19 * 60 + 9.566,
            "end": 19 * 60 + 24.800,
            "overlay": True,
        },
        {
            "key": "02_时辰与检查",
            "start": 20 * 60 + 22.133,
            "end": 21 * 60 + 1.000,
            "overlay": False,
        },
        {
            "key": "03_夸赞与指控",
            "start": 21 * 60 + 39.300,
            "end": 22 * 60 + 24.266,
            "overlay": False,
        },
        {
            "key": "04_证据与裁定",
            "start": 24 * 60 + 59.566,
            "end": 26 * 60 + 4.800,
            "overlay": False,
        },
    ]

    concat_files: list[Path] = []
    entries: list[dict] = []
    cursor = 0.0
    if relationship_pause > 0:
        pause_segment = work_dir / "segment_00_relationship_pause.mp4"
        make_paused_relationship_intro(
            source,
            graph_path,
            pause_segment,
            float(specs[0]["start"]),
            relationship_pause,
        )
        concat_files.append(pause_segment)
        entries.append(
            {
                "index": 0,
                "key": "00_人物关系说明（暂停画面）",
                "type": "relationship_pause",
                "start": 0.0,
                "end": round(relationship_pause, 3),
                "source_start": round(float(specs[0]["start"]), 3),
                "source_end": round(float(specs[0]["start"]), 3),
                "duration": round(relationship_pause, 3),
                "audio": False,
                "role": "relationship_explanation_only",
                "relationship_overlay": True,
            }
        )
        cursor += relationship_pause
    for index, spec in enumerate(specs, 1):
        segment = work_dir / f"segment_{index:02d}.mp4"
        duration = float(spec["end"] - spec["start"])
        use_overlay = bool(spec["overlay"]) and relationship_pause <= 0 and relationship_enabled
        if use_overlay:
            make_source_with_relationship_overlay(
                source,
                graph_path,
                segment,
                float(spec["start"]),
                float(spec["end"]),
                overlay_duration=14.0,
            )
        else:
            make_source_segment(source, segment, float(spec["start"]), float(spec["end"]), True)
        concat_files.append(segment)
        entries.append(
            {
                "index": index,
                "key": spec["key"],
                "type": "source",
                "start": round(cursor, 3),
                "end": round(cursor + duration, 3),
                "source_start": round(float(spec["start"]), 3),
                "source_end": round(float(spec["end"]), 3),
                "duration": round(duration, 3),
                "audio": True,
                "role": "long_coherent_evidence",
                "relationship_overlay": use_overlay,
            }
        )
        cursor += duration

    concat_list = work_dir / "concat.txt"
    concat_list.write_text("\n".join(quote_concat_path(path) for path in concat_files), encoding="utf-8")
    timeline_video = output_dir / f"{args.base_name}_连贯原剧时间线.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-fflags",
            "+genpts",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-vf",
            f"fps={FPS},format=yuv420p",
            "-af",
            "aresample=async=1:first_pts=0",
            "-fps_mode",
            "cfr",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            str(SAMPLE_RATE),
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            str(timeline_video),
        ]
    )

    plot_shift = relationship_pause
    narration = []
    if relationship_enabled:
        narration.append((0.500, 9.500, "先认清这几个人：吉祥是绣品染血后求助的人，璎珞负责接手补绣，玲珑负责提出指控，吴总管负责最后核验裁定。"))
    plot_intro_start = 16.000 if relationship_enabled else 0.500
    plot_intro_end = 26.000 if relationship_enabled else 10.500
    narration.extend([
        (plot_intro_start + plot_shift, plot_intro_end + plot_shift, "先把这场接力的起因捋清楚：绣品先出了意外，璎珞是接手补救，不是拿着一幅成品替别人交卷。"),
        (31.000 + plot_shift, 43.000 + plot_shift, "时辰一到，所有人必须停针，所以交接时出现半成品很正常。先被夸的双面绣属于另一位宫女，不是魏璎珞，别把人物记串了。"),
        (52.000 + plot_shift, 64.000 + plot_shift, "玲珑抓住两次换手，把救急接力解释成作弊。听起来气势汹汹，但真正要问的是：交接时有没有人拿到过成品？"),
        (70.000 + plot_shift, 83.000 + plot_shift, "这也是指控最容易混淆的地方。共同把一件绣品做完，和一个人替另一个人完成，是两回事。"),
        (113.000 + plot_shift, 128.000 + plot_shift, "所以璎珞没有只喊冤，而是把现场重新摆出来：第一次交接时，牡丹还差两针；交出去的从一开始就是半成品。"),
        (132.000 + plot_shift, 145.000 + plot_shift, "第二次交接也一样，绣品没有完成。两次都是未完成的状态，替考这个说法，少了最关键的成品证据。"),
        (151.000 + plot_shift, min(163.000 + plot_shift, cursor - 0.5), "吴总管最后认的不是谁更会吵，而是两次交接都能核对。你觉得这是作弊，还是规则内的接力？"),
    ])

    output_video = Path(args.output_video).resolve()
    plan_path = Path(args.output_plan).resolve()
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan = {
        "version": 1,
        "title": "她们被指作弊，但真正要核对的是绣品交接",
        "drama": {
            "work_title": "延禧攻略",
            "episode": "第1集",
            "story_arc": "绣坊考核中，璎珞用两次未完成的交接反证作弊指控",
            "opening_stance_hook": "先看清绣品为什么会被两个人接着绣，再判断这到底是不是作弊。",
            "commentary_viewpoint": "把接力过程和成品证据讲清楚，观众才能看懂这场绣坊争议。",
            "discussion_conflict": "共同完成绣品，究竟是作弊，还是规则内的接力？",
            "emotional_value": "观众从误会和紧张，转为看懂证据如何拆穿一句指控。",
            "rights_note": "沿用项目制作记录中的授权说明，素材仅用于本次影视剧情介绍与讨论。",
        },
        "source_subtitle": str(subtitle),
        "source_video": str(timeline_video),
        "output_video": str(output_video),
        "annotation_only": False,
        "layout": "source",
        "output_resolution": "1920:1080",
        "burn_captions": False,
        "write_subtitles": True,
        "platform_titles": {
            "bilibili": "延禧攻略：两次接力都是半成品，作弊指控为何站不住？",
            "douyin": "她们被指作弊，璎珞直接拿出两次半成品反证",
            "kuaishou": "两个人接着绣，怎么就成作弊了？",
            "xiaohongshu": "延禧攻略绣坊争议：双面绣不是魏璎珞的，这场接力到底算不算作弊？",
        },
        "platform_descriptions": {
            "bilibili": "保留较完整的剧情因果，只用一张半透明原创视觉辅助理解，再用原创解说拆解两次交接为什么都是半成品。",
            "douyin": "别只看谁在喊冤，先看绣品交接时有没有形成成品；双面绣也不是魏璎珞完成的。",
            "kuaishou": "绣品接力为什么被说成作弊？把两次交接看明白，答案就出来了。",
            "xiaohongshu": "用较完整的连续片段梳理《延禧攻略》第一集绣坊争议：双面绣归属、接力过程和作弊指控一次讲清。",
        },
        "edit_rules": {
            "selection_mode": "coherent_original_led_evidence_edit",
            "clip_order": "coherent_scene_then_commentary",
            "source_reuse": False,
            "source_overlap": False,
            "direct_cut": True,
            "transition_policy": "direct_cut_between_coherent_blocks",
            "original_audio_policy": "retain_complete_scene_audio_between_narration",
            "burn_annotations": False,
            "relationship_overlay": "none" if not relationship_enabled else ("semi_transparent_on_paused_opening_frame" if relationship_pause > 0 else "semi_transparent_on_opening_source_block"),
            "relationship_pause": relationship_pause > 0,
            "relationship_pause_policy": "freeze_video_and_mute_original_audio_until_relationship_explanation_finishes" if relationship_pause > 0 else "none",
        },
        "expression_rules": {
            "narration_led": True,
            "source_clip_role": "coherent_evidence_only",
            "original_audio_policy": "quote_and_complete_scene_audio",
            "full_conflict_replay": False,
            "analysis_cards": False,
            "caption_cards": False,
            "original_visuals": False,
            "viewer_can_finish_plot_from_clips": False,
            "relationship_pause_seconds": round(relationship_pause, 3),
        },
        "clips": [
            {
                "id": "少切段连贯原剧证据时间线",
                "source_start": "0.000",
                "source_end": f"{cursor:.3f}",
                "focus_x": 0.5,
                "high_energy": False,
                "source_clip_role": "four_coherent_evidence_blocks",
            }
        ],
        "narration": {
            "provider": "cosyvoice",
            "python": "tools/CosyVoice/.venv/Scripts/python.exe",
            "model_dir": "tools/CosyVoice/pretrained_models/CosyVoice-300M-SFT",
            "mode": "sft",
            "voice": "中文女",
            "speed": 1.12,
            "rate": "+12%",
            "segments": [
                {"start": hms(start), "end": hms(end), "text": text}
                for start, end, text in narration
                if end > start
            ],
        },
        "mix": {
            "source_audio_mode": "play_between_narration",
            "source_gap_volume": 0.48,
            "source_audio_under_narration_volume": 0.12,
            "source_audio_intro_deadline_seconds": 10.0,
            "source_audio_intro_min_seconds": 0.5,
            "narration_volume": 1.25,
            "audio_transition_fade_seconds": 0.12,
            "music_volume": 0.0,
        },
        "original_visual_assets": {
            "directory": str(asset_dir),
            "relationship_overlay_asset": str(graph_path),
            "timeline_manifest": entries,
            "source_visual_seconds": round(cursor, 3),
            "source_audio_seconds": round(cursor, 3),
        },
        "preflight_review": {
            "status": "passed",
            "review_scope": "content_before_render",
            "one_line_question": "共同完成绣品，究竟是作弊还是合理接力？",
            "one_line_answer": "两次交接时绣品都未完成，指控缺少成品这个关键前提。",
            "conflict": "玲珑把璎珞和吉祥的接力解释成作弊，璎珞用两次未完成的交接反证。",
            "emotional_value": "观众从看不清人物关系，转为看懂接力过程和证据链。",
            "checks": {
                "position_and_fact": "pass",
                "emotional_value": "pass",
                "conflict_and_hook": "pass",
                "answer_timing": "pass",
                "visual_evidence": "pass",
                "title_script_consistency": "pass",
                "safety_and_attribution": "pass",
            },
            "risk_notes": [
                "只保留一张原创视觉，并以半透明方式叠加在开头原剧画面上。",
                "原剧改为四个较完整的剧情块，减少碎片化切换；旁白负责解释因果。",
                "双面绣明确归于另一位宫女，不归于魏璎珞；不加入字幕卡和 BGM。",
            ],
        },
    }
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_path = output_dir / f"{args.base_name}_连贯原剧时间线.manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "duration": round(cursor, 3),
                "timeline_video": str(timeline_video),
                "assets": str(asset_dir),
                "entries": entries,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(timeline_video)
    print(plan_path)


if __name__ == "__main__":
    main()
