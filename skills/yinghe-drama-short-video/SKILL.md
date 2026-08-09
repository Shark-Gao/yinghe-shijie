---
name: yinghe-drama-short-video
description: 当用户要求制作或优化电视剧、电影、短剧或电视节目短视频时，基于有授权的影视素材和字幕，筛选一条可独立成立的冲突链，制作原创中文解说版和屏幕注释纯原声版，并用统一的宫廷悬疑编辑风封面、平台包装和发布后数据复盘形成迭代闭环。硬核视界的军事武器、武器系统和作战机制视频不得使用本技能。
---

# 电视剧剧情短视频工坊

本技能把一段电视剧剧情压缩成一条能独立观看的短视频。核心不是复述整集，而是把一个具体道具、动作或异常，组织成清楚的：

> 异常出现 → 危机升级 → 主角改局 → 认知改变 → 结果落地

短视频同时追求两件事：

- **点击承诺**：观众为什么要点进来。通常来自具体道具、明确危险、人物责任和惩罚/奖励结果。
- **观看完成**：观众为什么继续看。通常来自证据清楚、因果连续、解释紧凑和结尾释放。

银针类视频验证了“道具 + 人物 + 恶果”更容易扩大播放规模；绣线类视频验证了“单一问题 + 聪明解法 + 正向结果”更有观看效率。制作前必须区分这两类优势，不把播放量、完播率和平均观看时长混成一个结论。

## 渐进式读取路由

主文件保留硬规则和工作流。执行具体任务前，按需读取以下参考文件：

- 选题、故事卡、双评分、开头钩子、镜头选择和原创表达：读取 [`references/story-and-editing.md`](references/story-and-editing.md)。
- 配音、TTS、混音、停讲、原声切换：读取 [`references/audio-and-pause.md`](references/audio-and-pause.md)。
- 屏幕注释、双版本目录、注释 JSON/SRT 和剪映交付：读取 [`references/annotation-and-delivery.md`](references/annotation-and-delivery.md)。
- 三种封面、缩略图测试、标题层级和内部标签隔离：读取 [`references/cover-rules.md`](references/cover-rules.md)。
- 预检、成片验收、主页缩略图抽检和返修：读取 [`references/review-and-qa.md`](references/review-and-qa.md)。
- 平台时长、标题、简介、话题和最终回复：读取 [`references/platform-packaging.md`](references/platform-packaging.md)。
- 发布后的数据记录、横向对照和结论分级：读取 [`references/post-publish-review.md`](references/post-publish-review.md)。

## 已验证的内容模型

### 一条视频只解决一个问题

每条视频必须能回答一个普通观众问题，并交付一个素材已经证明的阶段性结果。例如：

- 用错道具后，主角如何避免被追责？
- 一个不起眼的物件，为什么会改变所有人的判断？
- 明明快要获罪，主角靠什么把危机改成奖励？

如果只能复述集数进度、人物关系或“这一集发生了很多事”，就不能进入制作。

### 选题采用双评分，而不是只看反转

每个候选分别评估：

**内容完成度**：

- 反转强度
- 独立成立
- 因果清楚
- 视觉证据
- 结果满足
- 剪辑可行

**分发潜力**：

- 道具或异常是否一眼可识别
- 前2秒是否能看出危险、指责或悬念
- 标题和封面能否说清“谁、因为什么、会发生什么”
- 是否有惩罚、奖励、揭穿、翻盘等情绪回报
- 画面缩小后是否仍然有明确主体

内容完成度高，说明适合做成片；分发潜力高，说明更可能扩大播放。两者都高才是首选 S 级。

### 封面、标题、开头和结尾必须承诺同一个结果

优先采用：

> 具体道具/异常 + 人物冲突 + 结果或危险

例如“银针”本身是识别物，“玲珑自食恶果”是结果；“绣线不对”是异常，“皇后追问谁敢糊弄”是追责悬念。前者结果承诺更强，后者需要在视频前5—10秒补足“为什么危险”。

## 不可违反的硬规则

1. 只处理用户提供且有权使用的素材；授权范围不明时只交付内部文案和剪辑计划，不公开发布。
2. 一条视频只讲一条独立冲突链，回答一个普通观众问题，交付一个已核验的阶段性结果。
3. 前2秒出现具体异常、危险动作、证据或人物反应；前5秒说明为什么值得继续看；前10秒交付核心问题或主要代价。
4. 原创解说和观点承担主体信息；原剧画面、对白和动作声只保留能够证明观点的必要证据。
5. 标题、封面、开头、口播/注释和结尾不能承诺素材没有展示的真相、动机或后续。
6. 原剧对白必须保留完整句或自然语义段；`source_end` 不得落在一句话中间，也不得硬切关键动作的起势、执行或后果。
7. 源片段两两不得重叠或重复。同一源时间段只能使用一次，高能片段不构成重复播放例外。
8. 默认直接切，不用黑屏、淡黑或人为停顿式过渡；确有时空跳跃或因果断裂时，才在明确段落边界使用极短过渡。
9. 默认不加 BGM；不要让中文配音遮挡关键台词、动作证据或人物反应。
10. 注释不是逐句字幕。每条注释只解释一个事实、因果、判断或结果，避免把观众已经看懂的对白重复写一遍。
11. `cover_style`、`content_lane`、`theme` 只作内部分类，不能自动成为封面文字；不得叠加“女性成长”“女性向”“军事向”等类别标签。
12. 每次生成后都必须完成实际时长、音频停讲、对白边界、画面、注释、三种封面、主页缩略图和交付文件复核；发布后还要记录数据，未完成时不能标记为正式完成。

## 默认输入、输出与版本选择

- 输入：原始视频、对应字幕、可核验授权信息；只有剧情梗概或截图时，不虚构时间码和成片。
- 输出根目录：`L:\workspace\yinghe-shijie\videos\exports\短视频\<主题目录>`。
- 默认双版本交付：原创中文解说混音版，以及屏幕注释纯原声版。
- 制作前必须标记主版本：
  - 原剧对白、表演和动作本身已经能讲清冲突，优先把注释纯原声版作为主版本。
  - 因果、人物关系或观点分散在多个片段，需要压缩解释时，优先把原创解说版作为主版本。
- 两个版本必须使用同一条冲突链、同一组经过复核的源片段和同一套包装信息，并分目录保存。
- 两个版本默认都要制作 `16:9`、`4:3`、`3:4` 三种封面；只有用户明确说不要封面时才跳过，并在计划和验收记录中说明原因。

解说版：`annotation_only: false`，调用 `skills/yinghe-short-video/scripts/produce_short_video.py`，输出 MP4、中文解说 MP3、中文解说 SRT、计划和发布文案。

注释版：`annotation_only: true`，调用 `skills/yinghe-drama-short-video/scripts/produce_annotation_video.py`，输出纯原声 MP4、注释 JSON、外置注释 SRT、计划和发布文案；不生成中文配音、不烧录注释。

## 标准工作流

1. 核对剧名、集数、素材来源、字幕和授权范围。
2. 读取 `yinghe-drama-reversal-analysis` 的分析规则，按本地视频和字幕筛选候选，不用网络梗概替代本地证据。
3. 为候选填写剧情卡、内容完成度和分发潜力评分，确定主问题、开头钩子、观点、结果、标题承诺和目标平台。
4. 选择不重复、不重叠的源片段，建立“源时间 → 成片时间 → 字幕/原声 → 解说/注释 → 观点证据”的对应表。
5. 确定时长档位：单次翻盘通常 `90—130秒`；需要多阶段证据链时可用 `150—210秒`；不得为了凑平台时长删除必要证据。
6. 读取 `audio-and-pause.md`，编写解说时间线并设置真实可感知的停讲；读取 `annotation-and-delivery.md`，设置注释功能和密度。
7. 运行 `validate_preflight_review.py --plan <plan.json>`，通过后再渲染。
8. 按主版本优先、另一版本同步的原则生成 MP4、旁车文件和注释文件。
9. 读取 `cover-rules.md` 生成三种封面，先做缩略图测试，再生成正式文件。
10. 读取 `platform-packaging.md` 生成与封面、开头和结尾一致的标题、完整简介和话题。
11. 读取 `review-and-qa.md` 完成实际成片、画面、音频、字幕、封面和主页缩略图复核；发现问题时同步修改计划、旁车和受影响的成片并重新验收。
12. 发布后读取 `post-publish-review.md` 记录数据，区分播放规模、观看效率、互动效率和转粉效率，把结论反馈到下一条选题和包装。

## 计划最小结构

解说计划至少记录：`drama`、`source_video`、`source_subtitle`、`output_video`、`clips`、`narration`、`mix`、`edit_rules`、`expression_rules`、`story_card`、`selection_score`、`target_platform`、`duration_bucket`、`preflight_review`。

注释计划另加：`annotation_only: true`、`annotation_file`、`caption_mode: "plot_summary"`、`write_subtitles: false`、`annotation_strategy`。

`story_card` 建议包含：`core_conflict`、`audience_question`、`opening_hook`、`viewing_promise`、`viewpoint`、`payoff_type`、`ending_result`、`discussion_point`、`unsupported_claims`。

`selection_score` 建议分别记录：`content_completion`、`distribution_potential`、`hook_type`、`object_or_evidence`、`emotional_payoff`、`visual_risk`、`dialogue_density`、`context_dependency`。

## 默认声音配置

解说版默认使用 CosyVoice `CosyVoice-300M-SFT`、声音 `中文女`、速度 `1.12`、无 BGM；默认混音为 `source_audio_mode: "play_between_narration"`、`source_gap_volume: 0.65`、`source_audio_under_narration_volume: 0.12`。若用户要求完全静音停讲，必须显式调整原声策略，不能沿用默认原声床。

解说版相邻实际 TTS 段间普通停讲不少于1.5秒，关键转折优先2—3秒；必须区分“停中文解说但保留原声”和“完全静音”。

## 交付底线

未通过预检、实际时长检查、音频停讲检查、对白边界检查、注释检查、画面抽检、封面检查、主页缩略图检查或文件清点时，只能标记为“待返修”。授权未核验时，成片仅供内部审看，不得声称可公开发布。发布后没有数据记录时，不能完成本条技能的复盘闭环。
