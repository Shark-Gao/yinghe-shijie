---
name: yinghe-video-workflow
description: Use when the user says “推荐”, “推荐一条”, “给我推荐视频”, “选片”, asks to add a YouTube source video to 硬核视界 records, or asks for 硬核视界 recommendation info, title, video description, thumbnail text, Bilibili cover assets, or vertical short-video covers for 快手、抖音、视频号.
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

Before selecting a source video, judge whether it can be localized into a topic style that already works for similar Chinese creators. Prefer source videos that can be reframed around:

- 大国工程：nuclear power, hydropower, rail, bridges, tunnels, power grids, ports, aerospace.
- 产业竞争：chips, lithography, GPUs, robots, batteries, engines, drones, machine tools.
- AI 应用：AI agents, AI training, AI hardware, AI video, AI safety, AI robots.
- 军工装备：aircraft carriers, submarines, tanks, fighter jets, missile defense, unmanned systems.
- 世界冷知识：map animation, geography, extreme environments, resource competition, disaster breakdowns, megastructures.

Avoid over-prioritizing cold pure-mechanism videos unless they can become a clear mainstream question such as `芯片为什么这么难造？`, `AI 为什么离不开 GPU？`, or `航母内部到底怎么运转？`.

## Required Workflow

1. Read existing records before recommending or recording a source video:
   - `data/recommended_videos.md`
   - `data/queued_videos.md`
   - `data/completed_videos.md`
2. Search or open current web sources to verify the video exists, the title/channel are correct, and the source URL is not already recorded.
3. Select exactly one video. Prefer videos that fit the current content matrix and have a clear Chinese-market title hook:
   - 科技纪录片 22%
   - AI 45%
   - 军事 23%
   - 世界冷知识 10%
   - 汽车机械 0%
   - 人体科普 0%
4. Output the recommendation in the exact 14-item format below, including platform-specific title variants.
5. Add the video to the top of `data/recommended_videos.md` with today’s date and status `已推荐`, keeping newest records first.
6. Also add the full recommendation details to the top of `data/recommended_video_details.md` in one human-readable block, keeping newest records first so the user can review recent entries without re-reading chat history.
7. Generate all upload-ready cover assets automatically unless the user explicitly says not to: two Bilibili covers plus one 9:16 short-video cover for 快手、抖音、视频号.

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
9. B站标题建议
10. 抖音标题建议
11. 快手标题建议
12. 小红书标题建议
13. 封面文案
14. 视频简介

For `内容分类`, use hashtag labels separated by spaces, not slashes or prose. Example:

```text
内容分类：#科技纪录片 #卫星互联网 #3D动画
```

Platform-title requirements:

- `B站标题建议`: 18-28 Chinese characters where possible. State the subject and viewing payoff clearly, while leading with conflict, scale, cost, scarcity, or a mainstream question.
- `抖音标题建议`: short, spoken, and immediately curiosity-inducing. Prioritize a striking fact, visual moment, or counterintuitive question; do not use empty shock words.
- `快手标题建议`: conversational and direct. Frame the curiosity around a concrete question or everyday consequence; avoid overly formal wording.
- `小红书标题建议`: searchable and save-worthy. Include the core technical keyword plus a clear learning benefit, such as `看懂`, `图解`, or `3分钟了解`; do not force emojis or hashtags into the title.

For `视频简介`, write 80-150 Chinese characters suitable for a Bilibili/short-video publishing description. Summarize the core visual hook, what the viewer will understand, and why the topic is worth watching. Do not paste a translated source description verbatim. Do not overpromise with unverifiable claims.

After the 14 fields, mention that both recommendation records were updated, then show only the three final upload-ready cover images:

- Use absolute filesystem paths, not relative paths, for cover links and Markdown image previews.
- Provide a clickable Markdown link and an inline Markdown image preview for each final cover.
- Do not show or link the generated base image in the final response unless the user explicitly asks for it.
- Keep the answer concise.

## Cover Workflow

For every recommendation, generate three upload-ready covers:

- 首页推荐封面（4:3）：`1146x860`
- 个人空间封面（16:9）：`1920x1080`
- 短视频竖版封面（9:16）：`1080x1920`，用于快手、抖音、视频号等竖屏发布；发布时只将其配给同为 9:16 的视频版本。

Use `imagegen` for the base raster visual when no suitable project-local image exists. Prompt for a high-impact, no-text visual that matches the video topic and leaves negative space for Chinese title text. Generate a separate vertical base when a crop would cut off the subject or make the title area unusable. Avoid logos, watermarks, people, and brand marks unless the source topic requires them.

Save cover assets under:

```text
covers/<source-video-slug>/
```

Use stable filenames:

```text
base-<topic>.png
<source-video-slug>-cover-4x3.png
<source-video-slug>-cover-16x9.png
<source-video-slug>-cover-9x16.png
```

Overlay text locally after the base image is generated:

- Main title: use item 13 “封面文案” or a punchier two-line version of item 9.
- Subtitle: short value hook such as `3D 剖面看懂原理`, `硬核拆解`, or `一眼看懂`.
- Style: large bold Chinese text, high contrast, black stroke/shadow, engineering/tech visual tone.
- Composition: keep the subject visible after both crops; keep important text away from edges.
- Vertical composition: place one clear subject in the lower or middle third. Reserve the upper third for a two-line headline and keep all text inside the central 80% safe area; do not simply stretch a horizontal cover.

Before finishing, inspect all three generated cover images. If text is cramped, cropped, unreadable, or overlaps the subject badly, adjust and regenerate the final cover files.

In the final response, show which file goes into each Bilibili upload slot and the vertical short-video cover using absolute paths and inline previews. Do not include `base-<topic>.png` in the final response unless explicitly requested.

```markdown
首页推荐封面 4:3
[打开图片](G:/workspace/yinghe-shijie/covers/<slug>/<slug>-cover-4x3.png)
![首页推荐封面 4:3](G:/workspace/yinghe-shijie/covers/<slug>/<slug>-cover-4x3.png)

个人空间封面 16:9
[打开图片](G:/workspace/yinghe-shijie/covers/<slug>/<slug>-cover-16x9.png)
![个人空间封面 16:9](G:/workspace/yinghe-shijie/covers/<slug>/<slug>-cover-16x9.png)

短视频竖版封面 9:16（快手 / 抖音 / 视频号）
[打开图片](G:/workspace/yinghe-shijie/covers/<slug>/<slug>-cover-9x16.png)
![短视频竖版封面 9:16](G:/workspace/yinghe-shijie/covers/<slug>/<slug>-cover-9x16.png)
```

## Selection Notes

- Prefer videos that can work with the V1.0 workflow: Telegram download MP4 → 剪映生成中英字幕 → 导出成片.
- Prefer videos that can be titled around conflict, scale, cost, scarcity, practical use, or why the subject is difficult.
- Prefer source topics that resemble proven domestic formats: engineering spectacle, industry competition, AI demos, military equipment, geography knowledge, disaster or failure reconstruction.
- When multiple candidates are similarly strong, break ties in this order: `#AI` / `#AI硬件` / `#芯片制造` / `#机器人` / `#航天工程` / `#科技纪录片` first, then other categories.
- Strongly prefer source videos that can be localized into mainstream Chinese tech questions such as `AI 为什么离不开 GPU？`, `芯片为什么这么难造？`, `机器人为什么还替代不了人？`, `数据中心为什么越建越耗电？`, or `商业航天到底贵在哪？`.
- Avoid videos that rely heavily on talking-head performance, podcast-style discussion, or visual context that cannot be understood with subtitles.
- Prefer visually self-explanatory source videos where subtitles alone can carry the Chinese remake.
- Prefer source videos with no obvious watermarks, channel bug overlays, platform logos, or reused compilation watermarks. If a strong candidate has minor unavoidable branding, mention the risk and prefer a cleaner alternative when available.
- If a promising video is from a channel already used, it is allowed as long as the exact source video was not recorded before.
- If all promising candidates are uncertain, choose the safest high-fit candidate and clearly say what was verified.

## Record Format

Insert below the table header in `data/recommended_videos.md`:

```markdown
| YYYY-MM-DD | Source video title | YouTube URL | Channel | Type | 已推荐 |
```

Use the same hashtag label format in the `Type` column, for example `#科技纪录片 #卫星互联网 #3D动画`.

Also append a full detail block to `data/recommended_video_details.md` using this structure:

```markdown
## YYYY-MM-DD - Source video title

视频链接：https://...
视频标题：...
频道：...
内容分类：#标签1 #标签2 #标签3
推荐理由：...
搬运适合度（★★★★★）：★★★★★
中文字幕难度：中
国内受众潜力：高
B站标题建议：...
抖音标题建议：...
快手标题建议：...
小红书标题建议：...
封面文案：...
视频简介：...
首页推荐封面 4:3：G:/workspace/yinghe-shijie/covers/<slug>/<slug>-cover-4x3.png
个人空间封面 16:9：G:/workspace/yinghe-shijie/covers/<slug>/<slug>-cover-16x9.png
短视频竖版封面 9:16：G:/workspace/yinghe-shijie/covers/<slug>/<slug>-cover-9x16.png
状态：已推荐
```

Requirements for `data/recommended_video_details.md`:

- Keep all recommendation detail blocks in this single file.
- Keep entries in reverse chronological order, with the newest date first. Preserve recommendation order within the same date.
- Use absolute filesystem paths for all three cover lines.
- This detail file is for human review, so keep prose readable instead of using a Markdown table.
