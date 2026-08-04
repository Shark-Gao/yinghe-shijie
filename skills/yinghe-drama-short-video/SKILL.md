---
name: yinghe-drama-short-video
description: 当用户明确要求制作或优化电视剧、电影、短剧或电视节目解说短视频、剧情文案、标题和简介时，分析有授权的影视素材和字幕，默认同时生成原创中文解说版与屏幕注释纯原声版两套影视短视频。两套版本都减少原剧画面和原声的连续复现，以少量证据片段支撑剧情理解；硬核视界的军事武器、武器系统和作战机制视频不得使用本技能。
---

# 电视剧剧情短视频工坊

本技能用于把有权使用的电视剧、电影或短剧素材剪成“原创解说和观点为主体、原剧短片段为证据”的视频。默认双版本交付：原创中文解说混音版，以及屏幕注释纯原声版。原剧画面和原声不能连续承担完整剧情，人物关系、因果、判断和情绪落点必须由原创表达完成。

## 渐进式读取路由

主文件只保留硬规则和工作流。执行具体任务前，按需读取以下直接引用的参考文件，不要把所有参考文件一次性加载：

- 选题、故事卡、镜头选择、原创表达和剧情边界：读取 [`references/story-and-editing.md`](references/story-and-editing.md)。
- 配音、TTS、混音、停讲、原声切换：读取 [`references/audio-and-pause.md`](references/audio-and-pause.md)。
- 屏幕注释、双版本目录、注释 JSON/SRT 和剪映交付：读取 [`references/annotation-and-delivery.md`](references/annotation-and-delivery.md)。
- 三种封面、叠字和内部标签隔离：读取 [`references/cover-rules.md`](references/cover-rules.md)。
- 预检、成片验收、问题返修和交付清单：读取 [`references/review-and-qa.md`](references/review-and-qa.md)。
- 平台时长、标题、简介、话题和最终回复：读取 [`references/platform-packaging.md`](references/platform-packaging.md)。

## 不可违反的硬规则

1. 只处理用户提供且有权使用的素材；授权范围不明时只交付内部文案和剪辑计划，不公开发布。
2. 一条视频只讲一条可独立成立的冲突链，回答一个普通观众问题，交付一个已核验的阶段性结果。
3. 原创解说和观点承担主体信息；原剧画面、对白和动作声只保留能够证明观点的必要证据。
4. 原剧对白必须保留完整句或自然语义段；`source_end` 不得落在一句话中间，也不得硬切关键动作的起势、执行或后果。
5. 源片段两两不得重叠或重复。同一源时间段只能使用一次，高能片段不构成重复播放例外。
6. 默认直接切，不用黑屏、淡黑或人为停顿式过渡；确有时空跳跃或因果断裂时，才在明确段落边界使用极短过渡。
7. 默认不加 BGM；不要让中文配音遮挡关键台词、动作证据或人物反应。
8. 解说版相邻实际 TTS 段间普通停讲不少于 1.5 秒，关键转折优先 2—3 秒；必须区分“停中文解说但保留原声”和“完全静音”。
9. `cover_style`、`content_lane`、`theme` 只作内部分类，不能自动成为封面文字。未经用户明确要求，不得叠加“女性成长”“女性向”“军事向”等类别标签。
10. 每次生成后都必须完成实际时长、音频停讲、对白边界、画面、注释、三种封面和交付文件复核；任何一项失败都不能标记为完成。

## 默认输入、输出与脚本

- 输入：原始视频、对应字幕、可核验授权信息；只有剧情梗概或截图时，不虚构时间码和成片。
- 输出根目录：`L:\workspace\yinghe-shijie\videos\exports\短视频\<主题目录>`。
- 解说版：`annotation_only: false`，调用 `skills/yinghe-short-video/scripts/produce_short_video.py`，输出 MP4、中文解说 MP3、中文解说 SRT、计划和发布文案。
- 注释版：`annotation_only: true`，调用 `skills/yinghe-drama-short-video/scripts/produce_annotation_video.py`，输出纯原声 MP4、注释 JSON、外置注释 SRT、计划和发布文案；不生成中文配音、不烧录注释。
- 两个版本必须使用同一条冲突链、同一组经过复核的源片段和同一套包装信息，并分目录保存。
- 两个版本默认都要制作 16:9、4:3、3:4 三种封面；电视剧封面优先遵循 `references/cover-rules.md` 中已确认的排版风格，先测试三种比例再生成正式文件；只有用户明确说不要封面时才跳过。

## 标准工作流

1. 核对剧名、集数、素材来源、字幕和授权范围。
2. 读取 `story-and-editing.md`，填写剧情卡，确定核心问题、开头冲突、观点和阶段性结果。
3. 选择不重复、不重叠的源片段，建立“源时间 → 成片时间 → 字幕/原声 → 解说/注释”的对应表。
4. 读取 `audio-and-pause.md`，编写解说时间线并设置真实可感知的停讲。
5. 运行 `validate_preflight_review.py --plan <plan.json>`，通过后再渲染。
6. 按默认双版本流程生成 MP4、旁车文件和注释文件。
7. 读取 `review-and-qa.md` 完成实际成片复核；发现问题时同步修改计划、旁车和受影响的成片并重新验收。
8. 读取 `cover-rules.md` 生成并检查三种封面，读取 `platform-packaging.md` 生成标题、简介和话题。
9. 最终回复直接展示平台、标题、完整简介、话题和主要文件路径，并标明授权状态。

## 计划最小结构

解说计划至少记录：`drama`、`source_video`、`source_subtitle`、`output_video`、`clips`、`narration`、`mix`、`edit_rules`、`expression_rules`、`preflight_review`。注释计划另加 `annotation_only: true`、`annotation_file`、`caption_mode: "plot_summary"` 和 `write_subtitles: false`。

解说版默认使用 CosyVoice `CosyVoice-300M-SFT`、声音 `中文女`、速度 `1.12`、无 BGM；默认混音为 `source_audio_mode: "play_between_narration"`、`source_gap_volume: 0.65`、`source_audio_under_narration_volume: 0.12`。若用户要求完全静音停讲，必须显式调整原声策略，不能沿用默认原声床。

## 交付底线

未通过预检、实际时长检查、音频停讲检查、对白边界检查、注释检查、画面抽检、封面检查或文件清点时，只能标记为“待返修”。授权未核验时，成片仅供内部审看，不得声称可公开发布。
