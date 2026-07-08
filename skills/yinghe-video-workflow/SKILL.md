---
name: yinghe-video-workflow
description: Use when the user says “推荐”, “推荐一条”, “给我推荐视频”, “选片”, asks to add a YouTube source video to 硬核视界 records, or asks for 硬核视界 recommendation info, title, video description, thumbnail text, or Bilibili cover assets.
---

# 硬核视界视频工作流

## Goal

Recommend one YouTube source video for the 硬核视界 project and keep the project records current.

## Project Context

Use this skill for the project at `G:\workspace\yinghe-shijie` or any checkout containing the same `AGENTS.md`, `data/`, `docs/`, and `prompts/` structure.

Follow the project positioning:

- Audience: male viewers interested in technology, AI, military, business, cars, engineering, documentaries, psychology, men’s health, and relationship science.
- Prefer: strong visuals, high information density, little or no presenter footage.
- Prioritize: 3D animation, engineering visualization, documentary footage, map animation, industrial manufacturing, AI demos, large machinery, infrastructure, data visualization.
- Avoid recommending the same source video twice.
- Keep topics series-friendly instead of jumping randomly between categories.

## Required Workflow

1. Read existing records before recommending or recording a source video:
   - `data/recommended_videos.md`
   - `data/queued_videos.md`
   - `data/completed_videos.md`
2. Search or open current web sources to verify the video exists, the title/channel are correct, and the source URL is not already recorded.
3. Select exactly one video. Prefer videos that fit the current content matrix:
   - 科技纪录片 30%
   - AI 20%
   - 军事 15%
   - 世界冷知识 15%
   - 汽车机械 10%
   - 人体科普 10%
4. Output the recommendation in the exact 11-item format below.
5. Add the video to `data/recommended_videos.md` with today’s date and status `已推荐`.
6. Generate Bilibili cover assets automatically unless the user explicitly says not to.

## Output Format

Use this exact structure:

1. 视频链接
2. 视频标题
3. 频道
4. 内容分类
5. 推荐理由
6. 搬运适合度（★★★★★）
7. 中文字幕难度
8. 国内受众潜力
9. 中文标题建议
10. 封面文案
11. 视频简介

For `视频简介`, write 80-150 Chinese characters suitable for a Bilibili/short-video publishing description. Summarize the core visual hook, what the viewer will understand, and why the topic is worth watching. Do not paste a translated source description verbatim. Do not overpromise with unverifiable claims.

After the 11 fields, mention that the recommendation record was updated, then list the generated cover file paths. Keep the answer concise.

## Cover Workflow

For every recommendation, generate two upload-ready covers:

- 首页推荐封面（4:3）：`1146x860`
- 个人空间封面（16:9）：`1920x1080`

Use `imagegen` for the base raster visual when no suitable project-local image exists. Prompt for a high-impact, no-text visual that matches the video topic and leaves negative space for Chinese title text. Avoid logos, watermarks, people, and brand marks unless the source topic requires them.

Save cover assets under:

```text
covers/<source-video-slug>/
```

Use stable filenames:

```text
base-<topic>.png
<source-video-slug>-cover-4x3.png
<source-video-slug>-cover-16x9.png
```

Overlay text locally after the base image is generated:

- Main title: use item 10 “封面文案” or a punchier two-line version of item 9.
- Subtitle: short value hook such as `3D 剖面看懂原理`, `硬核拆解`, or `一眼看懂`.
- Style: large bold Chinese text, high contrast, black stroke/shadow, engineering/tech visual tone.
- Composition: keep the subject visible after both crops; keep important text away from edges.

Before finishing, inspect both generated cover images. If text is cramped, cropped, unreadable, or overlaps the subject badly, adjust and regenerate the final cover files.

In the final response, show which file goes into each Bilibili upload slot:

```text
首页推荐封面 4:3: covers/<slug>/<slug>-cover-4x3.png
个人空间封面 16:9: covers/<slug>/<slug>-cover-16x9.png
```

## Selection Notes

- Prefer videos that can work with the V1.0 workflow: Telegram download MP4 → 剪映生成中英字幕 → 导出成片.
- Avoid videos that rely heavily on talking-head performance, podcast-style discussion, or visual context that cannot be understood with subtitles.
- Prefer visually self-explanatory source videos where subtitles alone can carry the Chinese remake.
- If a promising video is from a channel already used, it is allowed as long as the exact source video was not recorded before.
- If all promising candidates are uncertain, choose the safest high-fit candidate and clearly say what was verified.

## Record Format

Append to `data/recommended_videos.md`:

```markdown
| YYYY-MM-DD | Source video title | YouTube URL | Channel | Type | 已推荐 |
```
