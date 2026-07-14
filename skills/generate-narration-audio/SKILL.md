---
name: generate-narration-audio
description: Use when the user asks to generate source-length Chinese narration, 等长解说, 字幕解说音频, Yunyang MP3, automatic ducked audio mix, or JSON video text annotations from SRT/VTT/TXT subtitles for 硬核视界 videos.
---

# Generate Narration Audio

## Overview

Turn bilingual or English/Chinese subtitles into source-length Chinese narration for 硬核视界: timeline JSON, a bilingual Chinese-narration SRT, a rewritten `zh-CN-YunyangNeural` narration MP3, a verbatim Chinese-subtitle MP3, a Chinese-subtitle-plus-BGM MP3, machine-readable overlay annotation JSON, and auto-ducked mixed MP3 for Jianying/CapCut.

Only use 等长全程 mode. Do not create short remix or intermittent guide tracks.

Default style: calm documentary male narration, tech/engineering focus, natural Chinese口播, no marketing hype, no direct subtitle line-by-line translation.

## Workflow

1. Read the provided subtitle file (`.srt`, `.vtt`, or `.txt`) with `Get-Content -Raw`.
2. Prefer existing Chinese subtitle meaning, but use English lines to correct mistranslations.
3. Rewrite into full source-length Chinese narration, not a literal subtitle translation. For every narration segment, also write an accurate natural English translation in `english_text`; it is used only by the bilingual Chinese-narration SRT, never read by TTS.
4. Remove creator calls-to-action, sponsor thanks, long filler, platform-specific ending cards, and low-value tangents unless the user asks to keep them.
5. Keep the original video duration and chapter order. Use the original subtitle time ranges as alignment anchors.
6. Save all generated files under `outputs/audio/`.
7. Name every generated file from the source subtitle stem, preserving the Chinese title.
8. Locate the original video in `videos/raw/` before rendering. The project convention is that every original video is placed in this directory. Match its filename to the subtitle stem after removing a trailing timeline suffix such as `_时间线01`; for example, `二战战机 为何封神？_时间线01.srt` maps to `videos/raw/二战战机 为何封神？.mp4`. If multiple media extensions match, prefer `.mp4`.
9. Generate these outputs:
   - Timeline JSON: `outputs/audio/<字幕主名>_等长解说时间线.json`
   - Narration MP3: `outputs/audio/<字幕主名>_等长_Yunyang.mp3`
   - Chinese narration SRT: `outputs/audio/<字幕主名>_中文解说.srt`
   - Verbatim Chinese-subtitle timeline JSON: `outputs/audio/<字幕主名>_中文字幕直读时间线.json`
   - Verbatim Chinese-subtitle MP3: `outputs/audio/<字幕主名>_中文字幕直读_Yunyang.mp3`
   - Chinese-subtitle + BGM MP3: `outputs/audio/<字幕主名>_中文字幕直读_背景音乐_正式版.mp3`
   - Text annotations: `outputs/audio/<字幕主名>_等长文本注释.json`
   - Auto mixed MP3, when the source video is available: `outputs/audio/<字幕主名>_等长_自动混音_正式版.mp3`
10. Build `*_中文字幕直读时间线.json` with `scripts/build_subtitle_tts_timeline.py`. It retains only Chinese subtitle lines and their original timecodes; it does not rewrite or translate the wording. An English-only subtitle file cannot produce this track.
11. Export `*_中文解说.srt` from the rewritten narration timeline with `scripts/timeline_to_srt.py`. Each SRT cue contains the Chinese narration and its `english_text` translation on the next line, using exactly the corresponding narration time range. Do not overwrite the original bilingual subtitle file.
12. Generate both the rewritten narration MP3 and the verbatim Chinese-subtitle MP3 from their respective timeline JSON files with `scripts/render_timeline_tts.py`.
13. Mix the verbatim Chinese-subtitle MP3 with the default BGM using `scripts/mix_narration_with_bgm.py`. Use the project defaults: `music/硬核视界_通用BGM_舒缓科普探索_CC0.mp3`, music volume `0.45`, narration volume `1.0`, no ducking, no narration boost, no limiter, and no fade.
14. Generate auto-ducked mixed MP3 with `scripts/auto_mix_audio.py` using the rewritten narration MP3 and the matched `videos/raw/` file. Only skip it when no matching source video exists.
15. Validate `*_等长文本注释.json` with `scripts/validate_annotations_json.py`.
16. Delete temporary test/smoke outputs before the final response. Remove files in `outputs/` or `outputs/audio/` whose names contain `_测试版_`, `_test`, or `_smoke`, while preserving formal output files.
17. Report both timeline JSON files, Chinese narration SRT, annotation JSON, both pure-voice MP3 files, the BGM MP3, mixed MP3, duration, voice, and rate.

## Script Management

- Reuse the fixed tools in this skill's `scripts/` directory. Do not recreate, copy, or rewrite these Python scripts for each video run.
- Never create one-off Python helper scripts under `outputs/`, `outputs/audio/`, temporary folders, or project root just to build, retime, or mix one video.
- If a repeatable capability is missing (for example, creating a timeline from SRT or shifting all timecodes after a front cut), add or update one stable, parameterized script under `skills/generate-narration-audio/scripts/`, then call it with arguments.
- Treat output JSON and audio files as data artifacts, not executable code. Keep temporary media only for the duration of a command and delete it before finishing.

## Narration Rules

- Use natural Chinese口播, not translationese.
- Keep most sentences under 15-25 Chinese characters.
- Use commas, periods, and paragraph breaks to create TTS pauses.
- Convert digits to spoken Chinese when it improves TTS, such as `550` -> `五百五十`.
- Keep key facts and numbers from the source.
- Do not invent facts. If adding a simple explanation, keep it faithful to the source and visual context.
- Prefer "低沉、平稳、纪录片风格男声".
- Avoid: `家人们`, `震惊`, `太离谱了`, `看到最后`, exaggerated claims, and sales pitch tone.

## Timeline JSON

Use many shorter timeline segments, usually 20-80 segments for a 20-30 minute video. Each segment must have `id`, `start`, `end`, `text`, and `english_text`. Keep segment starts increasing and make the final `end` equal the source video duration when the video file is available.

The timeline JSON is the source of truth for both the narration text and timing. Do not create a separate human-readable script file by default.

Shape:

```json
{
  "version": 1,
  "source_subtitle": "星链如何把网络送到全球_时间线01.srt",
  "output_audio": "星链如何把网络送到全球_时间线01_等长_Yunyang.mp3",
  "mode": "source_length_full_narration",
  "voice": "zh-CN-YunyangNeural",
  "rate": "-8%",
  "video_duration": "00:28:08.400",
  "segments": [
    {
      "id": "seg_001",
      "start": "00:00:00.000",
      "end": "00:00:18.000",
      "text": "这里是一段适合这个时间窗口的中文解说。",
      "english_text": "This is Chinese narration written to fit this time window."
    }
  ]
}
```

Before generating the MP3, check that:

- `segments` are sorted by `start`.
- Every `end` is later than `start`.
- Every non-empty `text` has a concise, accurate `english_text` translation. Do not copy the original English subtitle unless it accurately translates the rewritten Chinese narration.
- The final segment plus tail padding reaches `video_duration`.

## Video Text Annotation Rules

Always generate duration-scaled low-effort overlay annotations unless the user says not to. These are not full subtitles; they are occasional on-screen value-add labels.

Choose the annotation count by video length:

- `0-8 minutes`: 12-24 annotations.
- `8-15 minutes`: 24-45 annotations.
- `15-25 minutes`: 45-75 annotations.
- `25+ minutes`: 75-120 annotations.

Do not add annotations only to hit a quota. Prefer useful labels over decorative clutter. A good rhythm is roughly 2-5 short annotations per minute, plus labels at major chapters, important numbers, or visual explanations.

If there is no strong visual callout, generate a short narration-derived annotation from the Chinese narration timeline. Compress one useful narration idea into a compact screen label. Do not copy a whole subtitle sentence. Examples:

- Narration idea: "坦克并不是一辆披着装甲的卡车，而是一套复杂机器。" -> annotation: `复杂战斗平台` / `不是装甲卡车`
- Narration idea: "乘员可能要在里面待上几百个小时。" -> annotation: `长时间封闭作战`
- Narration idea: "四个人必须像一个系统一样协作。" -> annotation: `四人协同`

Use annotations for:

- Key numbers: altitude, speed, size, cost, scale, time.
- Term explanations: one technical term in plain Chinese.
- Visual callouts: identify parts shown on screen.
- Principle summaries: one-sentence "what is happening here".
- Comparisons: before/after, old/new, traditional/new technology.
- Narration-derived tips: compact summaries from the Chinese narration when no stronger visual label exists.

Save annotations as UTF-8 JSON, not freeform text. The JSON must be a single object, not a markdown code block, not JSONL, and not a list at the top level.

Shape:

```json
{
  "version": 1,
  "source_subtitle": "星链如何把网络送到全球_时间线01.srt",
  "target_video": "videos/exports/星链如何把网络送到全球.mp4",
  "notes": "等长全程版视频文字注释，用于后续程序自动生成覆盖文字。时间点按等长解说时间线配置，可按画面微调。",
  "annotations": [
    {
      "id": "anno_001",
      "start": "00:00:02.000",
      "end": "00:00:07.000",
      "type": "chapter",
      "text": "星链怎么联网",
      "subtext": "从屋顶天线到低轨卫星",
      "position": "top_center",
      "x": 0,
      "y": 520,
      "layer": 10,
      "style": "tech_label",
      "motion": "fade",
      "visual_hint": "开头出现星链天线、地球、卫星或网络连接示意时使用",
      "avoid": ["subtitle", "core_subject"]
    }
  ]
}
```

Top-level schema rules:

- `version`: integer, currently `1`.
- `source_subtitle`: source subtitle filename only.
- `target_video`: target video filename/path if known; otherwise use an empty string.
- `notes`: short string for import/adjustment notes.
- `annotations`: array with 8-120 annotation objects, selected by video duration.
- Do not add extra top-level keys unless the downstream program schema has been updated.

Annotation object rules:

- `id`: stable `anno_001` style string.
- `start` and `end`: `HH:MM:SS.mmm`; `end` must be later than `start`.
- `type`: one of `data`, `term`, `callout`, `principle`, `comparison`, or `chapter`.
- `text`: main overlay text.
- `subtext`: optional secondary line. Use an empty string if not needed.
- `position`: one of `top_center` or `center`. Prefer `top_center` for chapter/data labels and `center` for principle/callout labels.
- `x` and `y`: Jianying/CapCut text coordinates. Use `x: 0, y: 520` for `top_center`; use `x: 0, y: 260` for `center`. Downstream import code should apply these coordinates directly and should not place annotations near the subtitle area.
- `layer`: integer overlay layer. Default `10`.
- `style`: default `tech_label`; use `data_badge` or `arrow_callout` when useful. Do not use bottom-oriented styles.
- `motion`: default `fade`; use `none` for static labels.
- `visual_hint`: concise Chinese hint for matching the overlay to the video frame.
- `avoid`: array of areas not to cover, such as `subtitle`, `face`, `map`, `diagram`, `core_subject`.
- Do not add extra annotation keys unless the downstream program schema has been updated.

Keep screen text compact:

- Main line: 6-14 Chinese characters when possible.
- Optional subline: 8-20 Chinese characters.
- Stay on screen for 2-4 seconds when possible. The validator allows 1.5-5 seconds.
- Do not place annotations at the bottom of the frame. Use the approved `top_center` or `center` coordinates to keep text away from subtitles.
- Avoid covering faces, core machinery, maps, or diagrams.

Validate:

```powershell
python "G:/workspace/yinghe-shijie/skills/generate-narration-audio/scripts/validate_annotations_json.py" `
  "G:/workspace/yinghe-shijie/outputs/audio/星链如何把网络送到全球_时间线01_等长文本注释.json"
```

## Chinese Narration SRT Rules

Always export a separate `*_中文解说.srt` from the rewritten `*_等长解说时间线.json`. It is an import-ready bilingual subtitle track for the generated Chinese narration, not a replacement for the original bilingual subtitle file.

- Use the rewritten Chinese narration `text`, its `english_text` translation, and its timeline timecodes.
- Each SRT cue has two lines: Chinese narration first and English translation second. Keep one cue per narration segment so both lines remain synchronized with the spoken audio.
- Write concise natural English that preserves the Chinese narration's facts, tone, and intent; do not add information.
- Save as UTF-8 SRT in `outputs/audio/`.
- Keep the source subtitle unchanged, so the editor can choose either the original Chinese-English subtitle track or this Chinese narration subtitle track.

## Auto Mixed Audio Rules

When the original video file is available, generate a Jianying-friendly MP3 that already contains:

- Original video audio as background.
- Chinese narration as foreground.
- Automatic ducking: lower original audio when narration speaks, restore original audio during narration gaps.

Use `scripts/auto_mix_audio.py` after the narration MP3 exists. Prefer MP3 over M4A for Jianying compatibility. Do not repeatedly overwrite an imported Jianying asset during testing; use a new filename or re-import the final file.

Default output names:

- Formal mix: `outputs/audio/<字幕主名>_等长_自动混音_正式版.mp3`

Mixing defaults inside the script:

- Original video audio base volume: `0.35`
- Chinese narration volume: `4.0`
- Sidechain compression: threshold `0.003`, ratio `16`, attack `35ms`, release `900ms`
- Output: clean MP3, `44100Hz`, stereo, `192kbps`, no inherited video metadata

After generation, verify the mixed MP3 duration equals the video duration with `ffprobe`. In Jianying, mute the original video track or set it to `0`, then use the `*_自动混音_正式版.mp3` file as the main audio track.

## Verbatim Chinese-subtitle Audio Rules

Always create a second, pure-voice MP3 from the original Chinese subtitle track. This gives the editor an alternative to the rewritten narration and auto-mixed tracks:

- `*_中文字幕直读_Yunyang.mp3`: original Chinese subtitle wording only, aligned to the subtitle timestamps, with no source audio or BGM.
- `*_中文字幕直读_背景音乐_正式版.mp3`: the same direct Chinese-subtitle voice, mixed with the standard loopable CC0 BGM.
- `*_等长_Yunyang.mp3`: rewritten documentary-style Chinese narration, with no source audio or BGM.
- `*_等长_自动混音_正式版.mp3`: rewritten narration plus ducked original video audio.

For bilingual subtitles, read only the Chinese line(s) in each cue. Preserve their wording other than removing subtitle markup. Do not use the English line or rewrite the Chinese copy. Use the default `+0%` rate so that the spoken track follows the original subtitle rhythm as closely as possible.

For the BGM version, use exactly the existing short-video mix convention: BGM at `0.45`, narration at `1.0`, and no ducking, gain boost, limiter, or fade. This version contains no original source audio.

## Defaults

| Item | Default |
| --- | --- |
| Mode | `等长全程` only |
| Voice | `zh-CN-YunyangNeural` |
| Rate | `-8%` |
| Output dir | `outputs/audio/` |
| Chinese narration subtitles | Always generate bilingual `*_中文解说.srt` from the rewritten narration timeline |
| Direct subtitle audio | Always generate `*_中文字幕直读_Yunyang.mp3` from Chinese SRT/VTT cues |
| Direct subtitle + BGM | Always generate `*_中文字幕直读_背景音乐_正式版.mp3` at music `0.45` / narration `1.0` |
| Naming | Preserve the source subtitle stem, mainly Chinese |
| Text annotations | 8-120 JSON overlay annotations, scaled by video duration |
| Auto mixed audio | Generate when source video path is available |

If the source video already has English narration, keep it only as low background through the auto mix. If the English voice remains distracting, recommend muting source audio and using light technology BGM instead.

## Script Commands

Generate the source-length narration MP3 from timeline JSON:

```powershell
python "G:/workspace/yinghe-shijie/skills/generate-narration-audio/scripts/render_timeline_tts.py" `
  --timeline "G:/workspace/yinghe-shijie/outputs/audio/星链如何把网络送到全球_时间线01_等长解说时间线.json"
```

Export the bilingual Chinese-narration subtitle track:

```powershell
python "G:/workspace/yinghe-shijie/skills/generate-narration-audio/scripts/timeline_to_srt.py" `
  --timeline "G:/workspace/yinghe-shijie/outputs/audio/星链如何把网络送到全球_时间线01_等长解说时间线.json" `
  --output "G:/workspace/yinghe-shijie/outputs/audio/星链如何把网络送到全球_时间线01_中文解说.srt"
```

Build and render the direct Chinese-subtitle audio:

```powershell
python "G:/workspace/yinghe-shijie/skills/generate-narration-audio/scripts/build_subtitle_tts_timeline.py" `
  --subtitle "G:/workspace/yinghe-shijie/星链如何把网络送到全球_时间线01.srt" `
  --video "G:/workspace/yinghe-shijie/videos/raw/星链如何把网络送到全球.mp4" `
  --output "G:/workspace/yinghe-shijie/outputs/audio/星链如何把网络送到全球_时间线01_中文字幕直读时间线.json" `
  --audio-output "星链如何把网络送到全球_时间线01_中文字幕直读_Yunyang.mp3"

python "G:/workspace/yinghe-shijie/skills/generate-narration-audio/scripts/render_timeline_tts.py" `
  --timeline "G:/workspace/yinghe-shijie/outputs/audio/星链如何把网络送到全球_时间线01_中文字幕直读时间线.json"

python "G:/workspace/yinghe-shijie/skills/generate-narration-audio/scripts/mix_narration_with_bgm.py" `
  --narration "G:/workspace/yinghe-shijie/outputs/audio/星链如何把网络送到全球_时间线01_中文字幕直读_Yunyang.mp3" `
  --output "G:/workspace/yinghe-shijie/outputs/audio/星链如何把网络送到全球_时间线01_中文字幕直读_背景音乐_正式版.mp3"
```

Generate auto-ducked mixed MP3 after the narration MP3 exists:

```powershell
python "G:/workspace/yinghe-shijie/skills/generate-narration-audio/scripts/auto_mix_audio.py" `
  --video "G:/workspace/yinghe-shijie/videos/exports/星链如何把网络送到全球.mp4" `
  --narration "G:/workspace/yinghe-shijie/outputs/audio/星链如何把网络送到全球_时间线01_等长_Yunyang.mp3"
```

If the original video audio is still too quiet after mixing, increase `--bg-volume`, for example:

```powershell
python "G:/workspace/yinghe-shijie/skills/generate-narration-audio/scripts/auto_mix_audio.py" `
  --video "G:/workspace/yinghe-shijie/videos/exports/星链如何把网络送到全球.mp4" `
  --narration "G:/workspace/yinghe-shijie/outputs/audio/星链如何把网络送到全球_时间线01_等长_Yunyang.mp3" `
  --bg-volume 0.45
```

## Output Response

Keep the final response short:

- Link the等长解说时间线 JSON.
- Link the中文解说 SRT.
- Link the中文字幕直读时间线 JSON.
- Link the等长文本注释 JSON.
- Link the等长 Yunyang MP3.
- Link the中文字幕直读 Yunyang MP3.
- Link the中文字幕直读背景音乐 MP3.
- Link the auto mixed MP3 when generated.
- Include duration when checked.
- Mention the voice and rate.
- Tell the user that they can choose the original bilingual subtitle file or the bilingual 中文解说 SRT in Jianying, and choose the direct-subtitle voice-only MP3, direct-subtitle+BGM MP3, or formal mixed MP3 as the main audio; mute the original video track when using any of them.
