---
name: yinghe-short-video
description: Analyze a long-form source video together with SRT, VTT, or subtitle text and turn it into a Chinese short video with narration, sidecar subtitles, and AI-generated 16:9 plus 9:16 upload-ready covers. Use when the user provides a source video and subtitles and asks to find strong clips, create a Chinese short-video script, automatically reorder clips, add narration, generate a cover, generate a vertical 快手/抖音/视频号 cover, or export a finished short-video MP4 for 硬核视界.
---

# 硬核短视频工坊

Analyze the original video together with its original subtitles, then export every original, self-contained Chinese short video that meets the editorial standard. Treat the source as a visual library, not as a sequence to shorten. Do not ask the user to choose among candidates unless they explicitly request options. Do not pre-set the number of exports: if one story qualifies, export one; if several independent stories qualify, export each of them.

## Workflow

1. Confirm that the user owns or may reuse the source. Locate the video and subtitle file. Keep the original files unchanged.
2. Run `scripts/prepare_review_assets.py` to create metadata, subtitle cues, and contact sheets. Inspect the original video contact sheets and the original subtitle cues before proposing or planning clips. Base candidate selection on these local original assets only; do not search the web for replacement footage or supplementary source material unless the user explicitly asks.
3. Identify every candidate story and score each one: visual impact 30%, stand-alone clarity 25%, Chinese audience relevance 20%, sufficient footage 15%, and safe 9:16 framing 10%. Export every candidate that is high-scoring and can stand alone; do not stop after choosing a single "best" story and do not impose a fixed maximum number of shorts. Create one separate short-video plan and export folder per qualifying story. Reject a candidate only when it lacks a clear question/result, enough usable footage, or materially overlaps another selected story. Use distinct primary footage and avoid substantially repeating source ranges across exports. Prefer 35–60 seconds per short; only make 20–30 seconds when one visual idea is genuinely sufficient.
4. Write a non-literal Chinese narration for each selected story: hook (0–2 s), explanation, and a concrete consequence. Use complete sentences or natural verbal units as narration segments; do not create a segment boundary in the middle of a phrase. Reserve enough time for the actual TTS reading speed plus a small buffer. Do not invent facts. Do not translate creator promotions, sponsorships, or calls to action.
5. Create four distribution titles for every selected story and include them in the edit-plan JSON as `platform_titles`: `bilibili`, `douyin`, `kuaishou`, and `xiaohongshu`. Set the plan's existing `title` field to the Bilibili title. In the final delivery, list all four titles separately for every exported short.
   - `bilibili`: 18–28 Chinese characters where possible. Make the subject and viewing payoff clear, and lead with conflict, scale, cost, scarcity, or a mainstream question.
   - `douyin`: short, spoken, and immediately curiosity-inducing. Lead with a striking visual, fact, or counterintuitive question; never use empty shock words.
   - `kuaishou`: conversational and direct. Ask a concrete question or show an everyday consequence; avoid formal, explanatory wording.
   - `xiaohongshu`: searchable and save-worthy. Include the core technical keyword and a clear learning benefit such as `看懂`, `图解`, or `3分钟了解`; do not force emojis or hashtags into the title.
   - `cover_headline` and `cover_subhead` remain platform-independent, concise cover copy. Derive them from the strongest verified hook, rather than copying any title verbatim.
6. Create one edit-plan JSON per qualifying story using [references/edit-plan-schema.md](references/edit-plan-schema.md), then export every completed plan. Put the source timecodes in the selected narrative order, which may differ from source order. Align every source-clip boundary with a narration-segment boundary: never change source footage while a segment is still being spoken. A clip may contain multiple complete narration segments, but its end must coincide with the end of the final segment it contains. Store short-video exports separately from future long-video exports: first create `videos/exports/短视频/<source-video-title>/`, then give every short its own `<topic>_短视频` folder and matching filename prefix inside it: `videos/exports/短视频/<source-video-title>/<topic>_短视频/`. Never mix files from different stories in one short folder, or short folders from different source videos under the same source-title folder. Use `source` layout by default: retain the original source resolution and 16:9 frame with no crop or canvas conversion. Always keep the video in this source layout unless the user explicitly asks for a 9:16 video version; the requirement to generate a vertical cover never authorizes changing the video itself to 9:16. Use `contain_blur` or `fill_crop` only when the user explicitly asks for a 9:16 video version.
7. Set `background_music` to `music/硬核视界_通用BGM_舒缓科普探索_CC0.mp3` by default, with `mix.music_volume` at `0.45`, `mix.narration_volume` at `1.0`, `mix.music_fade_seconds` at `0.0`, and `mix.source_volume` at `0.0`. This is a CC0, loopable synth/piano exploration ambience. Run `scripts/produce_short_video.py --plan <plan.json>` for each plan. It temporarily generates a timed Chinese narration MP3 and timeline JSON, then directly mixes the background music at 45% of its original level under the unchanged Chinese narration—no ducking, no narration boost, no limiter, and no fade—before cutting and reordering the source, preserving the original 16:9 output size, exporting the final MP4, and writing a sidecar SRT in one command. Inspect the generated narration timing before accepting each render: if a TTS segment exceeds its planned time window, or any cumulative clip boundary falls inside a spoken segment, extend or retime the plan and rebuild. Do not burn subtitles into the video unless the user explicitly asks. Do not route the source audio into the output unless the user explicitly requests it.
8. Generate two original upload-ready covers with the image generation tool after each video plan is final. Derive each prompt from the selected story, title, and narration; never use a frame from the source or finished video. Use one clear subject, high contrast, no people unless essential, no logos, no watermark, and no generated text. Save both covers in the matching dedicated export folder:
   - **16:9 landscape editorial cover**: engineering subject on the left, layered cutout/transparent motion echoes or exploded technical layers where relevant, a deep black negative-space title area on the right, and one restrained accent color. Overlay the exact `cover_headline` and `cover_subhead` with `scripts/add_cover_title.py --layout right`.
   - **9:16 vertical short-video cover** (`1080x1920`): generate this cover even when the delivered video remains 16:9. Use a separately generated vertical composition when a crop would compromise the subject or title. Place one clear subject in the lower or middle third, reserve the upper third for copy, and keep all text inside the central 80% safe area. Overlay the same verified copy with `scripts/add_cover_title.py --layout portrait`. Name it `<topic>_封面_9x16_设计版.png`. If the platform requires matching video and cover aspect ratios (for example 快手), do not pair this vertical cover with a 16:9 video; export a separate 9:16 video only when the user asks for it.
   Never rely on generated Chinese text. Name the landscape output `<topic>_封面_16x9_设计版.png`.
9. Verify each resulting MP4 and both covers with `ffprobe` and visual inspection. Check that the frame size matches the source, narration is intelligible, every source transition lands at a completed narration sentence or segment, each story remains distinct, and each cover clearly communicates the story without cropped or cramped text. Adjust only the relevant plan or cover and rebuild.
10. Run `scripts/cleanup_export.py --export-dir <topic_短视频 folder>` only after verification, once for every export folder. Final delivery directories must retain only: the final MP4, its SRT, the final `_封面_16x9_设计版.png`, and the final `_封面_9x16_设计版.png`. Delete AI cover originals, draft covers, narration MP3, timeline JSON, contact sheets, and any other export intermediates. Also delete the matching `videos/raw/<source-stem>_review/` directory created by `prepare_review_assets.py` after all shorts from that source are verified; it contains disposable contact sheets, subtitle cues, and an index. Never delete the original source video or subtitle file.

## Editorial constraints

- Start with the strongest result or scale, not chronological context.
- One video should answer one question. Cut source introductions, outros, repeats, and unsupported claims.
- Use Chinese narration to add explanation and a domestic relevance angle; do not merely replace English subtitles.
- Keep clips moving every 2–5 seconds unless the image itself is changing or a technical diagram needs longer.
- Make the exported work meaningfully transformative. Do not remove copyright notices or imply ownership of someone else's footage.

## Commands

```powershell
python "skills/yinghe-short-video/scripts/prepare_review_assets.py" `
  --video "videos/raw/source.mp4" --subtitle "source.srt"

python "skills/yinghe-short-video/scripts/produce_short_video.py" `
  --plan "outputs/shorts/source-machine-01.json"

python "skills/yinghe-short-video/scripts/cleanup_export.py" `
  --export-dir "videos/exports/短视频/<source-video-title>/source-machine_短视频"
```

Read [references/edit-plan-schema.md](references/edit-plan-schema.md) before writing or changing a plan. Do not hand-edit the video when the plan can be changed and rebuilt.
