---
name: yinghe-video-workflow
description: Use when the user asks for a video recommendation (including an unqualified “推荐视频” or “推荐一条”), selects a source video, or asks for recommendation info, titles, descriptions, thumbnail text, Bilibili cover assets, or vertical short-video covers. If direction is missing, ask before acting.
---

# 硬核视界视频工作流

## Direction Gate（强制）

本技能现在服务两个彼此独立的账号方向。每次触发“推荐视频 / 推荐一条 / 选片”时，必须先从当前用户消息中识别出**一个且只有一个**方向，再进行搜索、选片、写记录或生成封面：

- `男性向`：硬核视界，继续使用 `data/recommended_videos.md`、`data/recommended_video_details.md` 及现有男性向选题矩阵。
- `女性向`：TA成长笔记，使用 `data/female_recommended_videos.md`、`data/female_recommended_video_details.md` 及对应女性向记录文件。

用户可以说“男性视频 / 男性向 / 硬核视界”，或“女性向视频 / 女性视频 / TA成长笔记”。如果用户只说“推荐视频”“推荐一条”而没有明确方向，**不得搜索、推荐、更新记录或生成封面**，先只追问：`这次要推荐男性向（硬核视界）还是女性向（TA成长笔记）视频？` 不得根据历史对话、最近一次选择或视频主题自行推断。普通用户请求若同时写了两个方向，先请用户拆分或明确本次主方向，禁止把两种账号混在同一批记录中。例外是已明确配置固定配额的每日自动任务（例如“男性向 3 条 + 女性向 3 条”）：自动任务可以同时运行两条分支，但必须分组处理、分别查重、分别写入记录，不能把两种方向合并成一个选题或记录。

## Goal

Recommend the requested number of YouTube source videos for the selected account direction and keep only that branch's project records current.

## Project Context

Use this skill for the project at `L:\workspace\yinghe-shijie` or any checkout containing the same `AGENTS.md`, `data/`, `docs/`, and `prompts/` structure. Keep male and female recommendations, queues, completed items, titles, covers, and metrics separate.

Follow the project positioning:

- Audience: male viewers interested in technology, AI, military, business, cars, engineering, documentaries, psychology, men’s health, and relationship science.
- Prefer: strong visuals, high information density, little or no presenter footage.
- Prioritize: 3D animation, engineering visualization, documentary footage, map animation, industrial manufacturing, AI demos, large machinery, infrastructure, data visualization.
- Avoid recommending the same source video twice.
- 永久排除频道 `3Blue1Brown`：不得推荐其任何视频；即使用户指定该频道，也先说明其已被项目列入禁推名单，并改选其他来源。
- Keep topics series-friendly instead of jumping randomly between categories.
- 军工装备是高优先级题材：候选质量相当时，优先航母、潜艇、战机、导弹防御、无人装备等少真人、强工程可视化内容。
- 若用户要求每日三条推荐，三条必须属于三个不同的主主题；单日内不重复同一题材或同一系列，系列连续性通过跨天选题维持。

### 女性向账号：TA成长笔记

仅当用户明确选择 `女性向` 时使用以下定位，不要把它套到男性向账号：

- 账号主题：亲子育己、情绪管理、亲子沟通、家庭关系、女性自我成长。
- 目标表达：温和、具体、可实践、适合收藏和转发；优先把研究或故事转成“今天就能用”的一个小方法。
- 画面偏好：少真人出镜或无真人出镜，优先动画/插画、心理学实验、纪录片片段、情境演示、信息图和可理解的生活场景。
- 视觉审美优先：把“唯美、可爱、治愈感强”作为女性向源片的硬筛选项。优先温暖插画、绘本/定格/纸艺动画、柔和 3D、自然与生活美学镜头；画面要有统一配色、可做封面与首屏的主体，避免白底课件、粗糙线条动画、密集说教字幕和长时间专家对镜讲解。题材可靠性相当时，优先视觉更精致、情绪更柔和、适合国内女性收藏转发的版本。
- 选题边界：优先可靠的心理学、教育学、关系沟通与家庭生活内容；涉及医学、心理诊断或育儿结论时，必须保留来源和不确定性，不作诊断或绝对化承诺。
- 避免：性别对立煽动、羞辱父母或孩子、贩卖焦虑、未经证实的“育儿秘籍”、过度依赖专家面对镜头讲话的视频。
- 频道与清晰度：在质量相当时优先订阅量约 10 万以上但非巨型频道；优先可核验的 1080p 或更高画质。频道规模和清晰度无法核验时如实标注，不得编造。
- 初始测试矩阵（后续按数据调整）：亲子沟通 25%、情绪管理 25%、家庭关系 20%、女性成长 20%、心理学实验/生活方法 10%。女性向推荐不套用男性向的 AI/军事比例。

女性向记录的 `类型` 使用清晰的主题标签，例如 `#亲子沟通 #情绪管理 #心理学实验`，并在每条记录中写明 `账号方向：女性向`。

### 女性向制作与包装基线（TA成长笔记）

当女性向源片进入短视频制作、生成封面或输出发布条目时，以下要求默认强制执行，除非用户明确要求例外：

- **配音与音乐：** 女性向必须按题材自动选声；用户指定声音时始终以用户要求为准。亲子沟通、儿童情绪、早期成长、照护者与孩子互动等内容，使用温和女声 `zh-CN-XiaoxiaoNeural`，语速默认 `+0%`；女性成长、自我关怀、成人情绪管理、关系边界、伴侣沟通、依恋与独处等以成年女性为主要受众且无儿童场景的内容，使用沉稳、有陪伴感的男声 `zh-CN-YunyangNeural`，语速默认 `-4%`。男声应克制、清晰，不采用激情播报或“霸总式”表达；只要主题同时涉及儿童或亲子关系，就优先切回女声。使用 `music/TA成长笔记_CalmBGM_syncopika_CCBY30.ogg`，背景音量与男性向默认一致，为 `0.45`，不混入原片声音。该音乐为 CC-BY 3.0，发布简介必须包含：`音乐：calm bgm — syncopika（CC BY 3.0）`。
- **标题与承诺：** 标题、封面文案、前 5–10 秒口播、方法步骤和结尾必须回答同一个具体问题。不得把长期练习包装成“立刻冷静”，不得使用“治愈”“保证”“一定有效”等绝对承诺；将收益写成可被视频证明的具体动作或能力，例如“高压下稳定发挥”“把注意力拉回当下”。
- **封面视觉：** 所有女性向封面沿用“稳定发挥”视觉体系：深海军蓝底、薄荷绿/青绿色聚焦层、珊瑚色混乱线条收束为清晰目标、温暖的非写实编辑插画。默认以沉静的成年女性/照护者为主体；亲子内容可使用照护者与孩子，但色彩、线条和“混乱→聚焦”的叙事不变。16:9 主体置左侧或左下、右侧留深色标题区；9:16 主体置下半区、顶部留深色标题区。底图不生成文字，后期再叠加高对比中文标题。参考文件：`videos/exports/短视频/压力一上来如何冷静？3个可练习的稳定方法/稳定发挥_短视频/稳定发挥_封面_16x9_设计版.png` 与对应 `9x16` 文件。
- **节奏验收：** 依据实际 TTS 时长回写时间线；普通口播段间保留约 `0.2–0.4` 秒，超过 `0.6` 秒必须有明确叙事理由。最终必须检查标题—口播—字幕—画面四者一致，不能只通过分辨率和字幕时间等技术校验。

Before selecting a source video, judge whether it can be localized into a topic style that already works for similar Chinese creators. Prefer source videos that can be reframed around:

- 大国工程：nuclear power, hydropower, rail, bridges, tunnels, power grids, ports, aerospace.
- 产业竞争：chips, lithography, GPUs, robots, batteries, engines, drones, machine tools.
- AI 应用：AI agents, AI training, AI hardware, AI video, AI safety, AI robots.
- 军工装备：aircraft carriers, submarines, tanks, fighter jets, missile defense, unmanned systems.
- 世界冷知识：map animation, geography, extreme environments, resource competition, disaster breakdowns, megastructures.

Avoid over-prioritizing cold pure-mechanism videos unless they can become a clear mainstream question such as `芯片为什么这么难造？`, `AI 为什么离不开 GPU？`, or `航母内部到底怎么运转？`.

## Required Workflow

1. Read existing records before recommending or recording a source video. After the Direction Gate, read the matching branch:
   - 男性向：`data/recommended_videos.md`、`data/queued_videos.md`、`data/completed_videos.md`。
   - 女性向：`data/female_recommended_videos.md`、`data/female_queued_videos.md`、`data/female_completed_videos.md`。
   Never use a record from the other branch as if it belonged to the selected account. Before finalizing, perform an exact-URL duplicate check against both branches; a source already used by either account is a duplicate unless the user explicitly asks to reuse it.
2. Search or open current web sources to verify the video exists, the title/channel are correct, and the source URL is not already recorded. Reject the candidate immediately if the channel is `3Blue1Brown`.
3. Select exactly the number of videos requested by the user; when no quantity is specified, select one. For a daily batch of exactly three, select three different primary themes before optimizing for series continuity. For the configured six-item automation, apply this rule separately to the three-item 男性向 branch and the three-item 女性向 branch. Prefer videos that fit the current content matrix and have a clear Chinese-market title hook:
   - 科技纪录片 22%
   - AI 38%
   - 军事 30%
   - 世界冷知识 10%
   - 汽车机械 0%
   - 人体科普 0%
4. Output every recommendation as one copy-ready publishing entry. The topic, hashtag classification, recommendation angle, video description, and all platform title variants must stay together in that single entry.
5. Add the video to the top of the matching recommendation file (`data/recommended_videos.md` for 男性向, `data/female_recommended_videos.md` for 女性向) with today’s date, the selected account direction, and status `已推荐`, keeping newest records first.
6. Also add the full recommendation details to the top of the matching detail file (`data/recommended_video_details.md` for 男性向, `data/female_recommended_video_details.md` for 女性向) in one human-readable block, keeping newest records first so the user can review recent entries without re-reading chat history.
7. Do **not** generate cover assets by default. Generate the two Bilibili covers and one 9:16 short-video cover only when the user explicitly asks to generate covers (for example, `生成封面` or `同时出封面`). When covers are not requested, do not create cover files, do not include cover sections in the response, and write `封面：未生成（需用户明确要求）` in the detail record.

## Output Format

Present every source as one self-contained, copy-ready publishing entry. A single-source response begins with `## 推荐 1｜可复制发布条目`; a three-source daily response repeats it as `推荐 1` through `推荐 3`. Never split one source's topic, classification, description, and titles across a separate summary or table.

Immediately below each heading, use one `text` code block in this exact structure. Keep all copy-ready publishing fields in the same block. The clickable source-video link is the sole exception: show it immediately below the code block as a Markdown link, so it can be opened directly in the chat:

```text
【选题】
主主题：<科技纪录片 / AI / 军事 / 世界冷知识 / 汽车机械 / 人体科普之一>
内容分类：#标签1 #标签2 #标签3
选题角度：<一句话说明可包装成的国内热门问题或冲突>

【发布内容】
视频简介：<80—150 字中文发布简介>
封面文案：<适合两行排版的短文案>

【标题｜按平台直接复制】
B站：<18—28 字标题>
抖音：<短、口语化标题>
快手：<直接、生活化标题>
小红书：<含核心关键词和“看懂 / 图解 / 3分钟了解”等学习收益的标题>

【源片信息】
视频标题：...
频道：...

【制作评估】
推荐理由：...
搬运适合度（★★★★★）：★★★★★
中文字幕难度：低 / 中 / 高
国内受众潜力：高 / 中 / 低
```

Then add this clickable line directly below the code block:

```markdown
源片：[点击直接打开 YouTube 视频](https://...)
```

Formatting requirements:

- The `【标题｜按平台直接复制】` section is mandatory. Always put the four platform titles together, with the platform label at the beginning of each line.
- `主主题` and `内容分类` are separate: the first supports daily topic balancing; the second must use hashtag labels separated by spaces.
- `选题角度` and `视频简介` are both required. The former is the packaging hook; the latter is copy-ready publishing text.
- Do not put user-facing recommendation fields outside this code block, except for the required clickable `源片` Markdown link and, when explicitly requested, the three cover sections that follow it.

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

Only when the user explicitly requested cover generation, immediately after the copy-ready entry show the three cover sections in this exact order. Each section must include one `打开图片` link followed by its inline preview; do not place all cover links together or omit previews. When covers were not requested, omit all three cover sections:

```markdown
首页推荐封面 4:3
[打开图片](<absolute-path-to-4x3-cover>)
![首页推荐封面 4:3](<absolute-path-to-4x3-cover>)

个人空间封面 16:9
[打开图片](<absolute-path-to-16x9-cover>)
![个人空间封面 16:9](<absolute-path-to-16x9-cover>)

短视频竖版封面 9:16（快手 / 抖音 / 视频号）
[打开图片](<absolute-path-to-9x16-cover>)
![短视频竖版封面 9:16](<absolute-path-to-9x16-cover>)
```

After all recommendation blocks, add one concise line confirming which direction-specific recommendation and detail files were updated.

Cover-output rules:

- Use absolute filesystem paths, not relative paths, for cover links and Markdown image previews.
- Provide a clickable Markdown link and an inline Markdown image preview for each final cover.
- Do not show or link the generated base image in the final response unless the user explicitly asks for it.
- Keep the answer concise.

## Cover Workflow

Only when the user explicitly requests cover generation, generate three upload-ready covers:

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
- When multiple candidates are similarly strong, first preserve different primary themes within a three-video daily batch. Then break ties in this order: `#军事` / `#军工装备` / `#AI` / `#AI硬件` / `#芯片制造` / `#机器人` / `#航天工程` / `#科技纪录片`, then other categories.
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

For 女性向, use the same row shape in `data/female_recommended_videos.md`, add `女性向` in the `账号方向` column, and use labels such as `#亲子沟通 #情绪管理 #心理学实验` or `#家庭关系 #女性成长`.

Also append a full detail block to `data/recommended_video_details.md` using this structure:

```markdown
## YYYY-MM-DD - Source video title

视频链接：[点击打开源片](https://...)
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

For 女性向, write the same detail block to `data/female_recommended_video_details.md`, include `账号方向：女性向`, and apply the female-account topic and safety rules above. Do not mix the two account directions in one detail file.
