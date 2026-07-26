---
name: generate-narration-audio
description: 当用户要求为硬核视界生成源片等长中文解说、CosyVoice 或 Edge 中文配音、自动压低原声的混音，或根据 SRT/VTT/TXT 生成视频文字注释 JSON 时使用。改写时遵循普通观众问题、先给答案、地缘政治、军事装备、工程科技和多平台包装规则。
---

# 生成中文解说音频

把双语、英文或中英字幕转换为硬核视界的源片等长中文解说，输出时间线 JSON、带中英双语的中文解说 SRT、CosyVoice 或 Edge 生成的中文解说 MP3、原中文字幕直读 MP3、中文字幕直读加 BGM MP3、机器可读的画面注释 JSON，以及自动压低原声的混音 MP3，供剪映使用。

只使用“等长全程”模式，不制作短混剪或断续的提示音轨。

默认风格是沉稳、清晰、纪录片式的中文口播，重点解释技术、工程和机制；不得写成营销文案，也不能逐句直译字幕。

配音默认优先使用项目已验证的本地 `CosyVoice-300M-SFT`，以减少云端额度消耗并保持稳定音质；`CosyVoice-300M-Instruct` 仅在用户明确要求并通过短句试听后使用，不作为默认模型。CosyVoice 环境不可用、需要快速试稿或用户指定云端声音时，使用 Edge TTS。CosyVoice 的计划字段、参考音频和模式见 [references/cosyvoice.md](references/cosyvoice.md)。

统一运行规则：CosyVoice 使用 `tools/CosyVoice/.venv/Scripts/python.exe`、`tools/CosyVoice/pretrained_models/CosyVoice-300M-SFT` 和 `mode: "sft"`；`render_cosyvoice_timeline.py` 自动检测 CUDA，有可用 NVIDIA GPU 时使用 CUDA + FP16，本机默认走 RTX 4060，无法使用 GPU 时才回退 CPU。Edge TTS 只能作为用户指定或 CosyVoice 不可用时的回退，不得无说明地替换本地配音。每次仍须记录实际 TTS 分段时长。

## 编辑预检

改写长解说前，先在时间线工作目录旁建立一份简短编辑卡：

```text
主赛道：地缘政治 / 军事装备 / 大国工程科技
普通人问题：观众为什么要关心？
核心答案：这条视频最终让观众明白什么？
前2秒钩子：第一句如何制造冲突、结果或反常识？
5—10秒承诺：最晚何时交付核心答案？
情绪变化：观众看完后从什么判断变成什么判断？
系列归属：下一条可以接什么？
```

不得从泛泛背景或源频道介绍开始。地缘政治内容要分开事实、来源观点和推断，保留不确定性，不能把评论写成事实。军事和工程内容的重要解释必须能在画面、图示、地图或字幕中找到依据。

## 工作流程

1. 使用 `Get-Content -Raw` 读取用户提供的字幕文件（`.srt`、`.vtt` 或 `.txt`）。
2. 优先理解现有中文含义；需要纠正误译时，用英文字幕辅助核对。
3. 改写为完整源片长度的中文解说，不做逐句翻译。每段解说都要同时写出准确、自然的英文翻译到 `english_text`；该字段只用于双语中文解说 SRT，不会被 TTS 朗读。
4. 除非用户要求保留，否则删除创作者行动号召、赞助感谢、长篇填充、平台结尾卡和低价值支线。
5. 保持原视频总时长和章节顺序，以原字幕时间范围作为对齐锚点。
6. 所有生成文件保存到 `outputs/audio/`。
7. 文件名使用源字幕主名，并尽量保留中文标题。
8. 生成前在 `videos/raw/` 中定位原始视频。字幕主名去掉末尾类似 `_时间线01` 的时间线后缀，再匹配视频；存在多个扩展名时优先 `.mp4`。
9. 必须生成以下文件：
   - `outputs/audio/<字幕主名>_等长解说时间线.json`
   - `outputs/audio/<字幕主名>_等长_<provider>.mp3`
   - `outputs/audio/<字幕主名>_中文解说.srt`
   - `outputs/audio/<字幕主名>_中文字幕直读时间线.json`
   - `outputs/audio/<字幕主名>_中文字幕直读_<provider>.mp3`
   - `outputs/audio/<字幕主名>_中文字幕直读_背景音乐_正式版.mp3`
   - `outputs/audio/<字幕主名>_等长文本注释.json`
   - 有匹配源视频时再生成 `outputs/audio/<字幕主名>_等长_自动混音_正式版.mp3`
10. 用 `scripts/build_subtitle_tts_timeline.py` 构建 `*_中文字幕直读时间线.json`。它只保留中文字幕和原时间码，不改写、不翻译原文。只有英文字幕时，不能生成这条直读音轨。
11. 用 `scripts/timeline_to_srt.py` 根据改写后的解说时间线导出 `*_中文解说.srt`。每个字幕段包含中文解说和下一行英文翻译，并使用对应解说时间码。不要覆盖原始双语字幕。
12. 根据时间线中的 `provider` 分别生成改写解说 MP3 和中文字幕直读 MP3：`provider: "cosyvoice"` 使用本地 CosyVoice，`provider: "edge"` 或省略时使用 Edge TTS。每个段落必须记录真实生成时长，不能用计划窗口代替。
13. 用 `scripts/mix_narration_with_bgm.py` 给中文字幕直读 MP3 加默认 BGM：音乐 0.45、口播 1.0，不压低音乐、不增加口播增益、不使用限幅、不淡入淡出。
14. 有匹配源视频时，用 `scripts/auto_mix_audio.py` 将改写解说和原视频声音混合，并在解说出现时自动压低原声。找不到源视频时才跳过。
15. 用 `scripts/validate_annotations_json.py` 校验 `*_等长文本注释.json`。
16. 回复用户前做文件和内容预检：等长解说分支不能被直读字幕分支替代，不能复制、改名或重新渲染未经改写的直读时间线来冒充等长解说。确认等长 JSON 使用 `mode: source_length_full_narration`，每段都有自然改写的中文 `text` 和非空 `english_text`，且与源中文字幕有实质区别。再确认所有必需文件存在；有源视频时也确认自动混音文件存在。缺失或无效的文件必须补生成。
17. 回复前删除临时测试文件：删除 `outputs/` 或 `outputs/audio/` 中名称包含 `_测试版_`、`_test` 或 `_smoke` 的文件，但保留正式文件。
18. 最终报告两条时间线 JSON、中文解说 SRT、注释 JSON、两条纯人声音频、BGM 混音、自动混音（如有）、时长、声音和语速。

## 脚本管理

- 重用本技能 `scripts/` 中固定的工具，不要为每条视频重新复制或改写 Python 脚本。
- 不要在 `outputs/`、`outputs/audio/`、临时目录或项目根目录创建只服务于单条视频的一次性辅助脚本。
- 如果缺少可重复的能力，例如根据 SRT 创建时间线、在片头裁切后统一平移时间码，应在 `skills/generate-narration-audio/scripts/` 中新增或更新一个稳定、带参数的脚本，再通过参数调用。
- 输出 JSON 和音频都是数据文件，不是可执行代码。临时媒体只保留到命令结束，完成后删除。

## 中文解说规则

- 使用自然中文口播，不写翻译腔。
- 大多数句子控制在 15–25 个汉字以内。
- 用逗号、句号和段落分隔制造自然 TTS 停顿。
- 需要时把数字改写为适合朗读的中文，例如 `550` 写成“五百五十”。
- 保留源片关键事实和数字，不得编造事实。
- 如果补充简单解释，必须忠于源片和可见画面。
- 5–10 秒内交付核心答案；历史背景、定义和次要信息放到答案之后，除非背景本身就是答案。
- 地缘政治内容避免对国家、战争或联盟下绝对结论，除非有当前核验和源片依据；优先解释地理、装备、后勤、能源、产业或平民影响等具体机制。
- 通过清晰、后果、对比或有用问题制造情绪变化，不使用空洞愤怒、辱骂或虚构冲突。
- 在不超出时间窗口、不遮挡关键画面节奏的前提下，优先补充“为什么”“数据怎样流动”“设计带来什么结果”，而不是只复述字幕或画面。
- 对 20–30 分钟的视频，通常使用 50–80 个自然口播段；每 30 秒时间窗通常写 80–110 个中文字符，再按实际 TTS 时长缩短或拆分。除非画面确实需要留白，不要让长时间窗只剩一两句解说。
- 默认使用低沉、平稳、纪录片风格男声。
- 避免 `家人们`、`震惊`、`太离谱了`、`看到最后`、夸张断言和销售口吻。

## 时间线 JSON

通常为 20–30 分钟视频写 20–80 个较短的时间线段。每段都必须有 `id`、`start`、`end`、`text` 和 `english_text`。开始时间按升序排列；有视频文件时，最后一段结束时间应等于源视频时长。

时间线 JSON 是口播文本和时间的唯一事实来源，不要默认另建一份重复的人类可读脚本。

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
      "english_text": "This is an English translation of the rewritten Chinese narration."
    }
  ]
}
```

生成 MP3 前确认：`segments` 按开始时间排序；每个 `end` 晚于 `start`；每个非空中文 `text` 都有准确、简洁、自然的 `english_text`；最后一段加尾部缓冲能够覆盖 `video_duration`。

## 视频文字注释规则

默认生成按时长缩放的低密度画面注释，除非用户明确要求不生成。它们不是完整字幕，而是偶尔出现、能增加理解价值的屏幕标签。电视剧的无配音模式可调用 `build_timeline_annotations.py --format plot_summary`：此模式只输出一条剧情简介到 `text`，强制 `subtext` 为空，并使用 `style: "arrow_callout"`，方便 `jianying_assistant` 的“视频注释插入”插件只插入单行文字，不生成主标题加副标题结构。

建议数量：

- 0–8 分钟：12–24 条；
- 8–15 分钟：24–45 条；
- 15–25 分钟：45–75 条；
- 25 分钟以上：75–120 条。

不要为了凑数量添加装饰性文字。较好的节奏是每分钟约 2–5 条，再在主要章节、关键数字或视觉解释处加标签。没有强视觉标注时，可以从中文解说中压缩出一个有用的屏幕短语，但不能整句复制字幕。

可用于：

- 高度、速度、尺寸、成本、规模、时间等关键数字；
- 用普通中文解释一个技术词；
- 标出画面中出现的部件；
- 总结当前发生的原理；
- 做前后、新旧、传统与新技术对比；
- 在没有更强视觉标签时，提炼解说中的实用提示。

JSON 必须是 UTF-8 的单个对象，不是 Markdown 代码块，不是 JSONL，也不是顶层数组。

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

顶层字段必须是 `version`、`source_subtitle`、`target_video`、`notes` 和 `annotations`；版本当前为整数 `1`。`source_subtitle` 只写源字幕文件名，未知的 `target_video` 使用空字符串。注释数组按视频时长生成 8–120 条，不要在未同步下游程序前增加顶层字段。

每个注释对象必须包含：

- `id`：稳定的 `anno_001` 样式编号；
- `start`、`end`：`HH:MM:SS.mmm`，且 `end` 晚于 `start`；
- `type`：`data`、`term`、`callout`、`principle`、`comparison` 或 `chapter`；
- `text`：主文字；
- `subtext`：没有副文字时写空字符串；
- `position`：`top_center` 或 `center`；
- `x`、`y`：剪映/CapCut 坐标。`top_center` 使用 `x: 0, y: 520`，`center` 使用 `x: 0, y: 260`；
- `layer`：整数图层，默认 `10`；
- `style`：默认 `tech_label`，必要时使用 `data_badge` 或 `arrow_callout`；
- `motion`：默认 `fade`，静态标签使用 `none`；
- `visual_hint`：用于把文字匹配到画面的简短中文提示；
- `avoid`：不能覆盖的区域，例如 `subtitle`、`face`、`map`、`diagram`、`core_subject`。

主行尽量控制在 6–14 个汉字，副行控制在 8–20 个汉字；通常显示 2–4 秒，校验器允许 1.5–5 秒。不要把注释放在画面底部，也不要覆盖脸、核心机械、地图或图表。

校验命令：

```powershell
python "L:/workspace/yinghe-shijie/skills/generate-narration-audio/scripts/validate_annotations_json.py" `
  "L:/workspace/yinghe-shijie/outputs/audio/星链如何把网络送到全球_时间线01_等长文本注释.json"
```

## 中文解说 SRT 规则

始终从改写后的 `*_等长解说时间线.json` 导出独立的 `*_中文解说.srt`。它是供中文解说音频使用的中英双语字幕轨，不是原始双语字幕的替代品。

- 使用改写后的中文 `text`、对应 `english_text` 和时间线时间码；
- 每个 SRT 段先写中文，再写英文翻译；一个口播段对应一个字幕段；
- 英文要自然、简洁，并保留中文解说的事实、语气和意图，不得添加信息；
- 保存为 UTF-8 SRT 到 `outputs/audio/`；
- 原始字幕保持不变，剪映中可以选择原双语字幕或这条中文解说 SRT。

## 自动混音规则

源视频存在时，生成一条适合剪映的 MP3，包含：

- 原视频声音作为背景；
- 中文解说作为前景；
- 解说出现时自动压低原声，解说间隙恢复原声。

使用 `scripts/auto_mix_audio.py`，默认正式输出为 `outputs/audio/<字幕主名>_等长_自动混音_正式版.mp3`。默认参数：原声底音量 `0.35`，中文解说音量 `4.0`，侧链压缩阈值 `0.003`、比例 `16`、启动 `35ms`、释放 `900ms`；输出为 `44100Hz`、立体声、`192kbps` 的干净 MP3，不继承视频元数据。生成后用 `ffprobe` 确认混音时长等于视频时长。剪映中使用该文件时，要把原视频轨静音或设为 `0`。

## 中文字幕直读音频规则

始终根据原中文字幕另做一条纯人声备选：

- `*_中文字幕直读_<provider>.mp3`：只读原中文字幕，使用字幕时间码，不含原声和 BGM；
- `*_中文字幕直读_背景音乐_正式版.mp3`：同一条直读人声加标准循环 CC0 BGM；
- `*_等长_<provider>.mp3`：改写后的纪录片式中文解说，不含原声和 BGM；
- `*_等长_自动混音_正式版.mp3`：改写解说加自动压低的原视频声音。

双语字幕只读取每个字幕段中的中文行，去掉字幕标记但保留原文，不使用英文行，也不改写中文。使用 `+0%`，让直读音频尽量贴合原字幕节奏。

直读加 BGM 版本必须遵循短视频现有混音约定：BGM `0.45`、口播 `1.0`，不压低、不增益、不限幅、不淡入淡出，也不包含原视频声音。

## 默认值

| 项目 | 默认值 |
| --- | --- |
| 模式 | 仅 `等长全程` |
| 配音 provider | 优先 `cosyvoice`，不可用时 `edge` |
| CosyVoice 默认模型 | `CosyVoice-300M-SFT` |
| CosyVoice 默认声音 | `中文男` |
| CosyVoice 加速 | CUDA 可用时自动使用 GPU + FP16 |
| Edge 默认声音 | `zh-CN-YunyangNeural` |
| 改写解说语速 | `-8%` |
| 输出目录 | `outputs/audio/` |
| 中文解说字幕 | 始终由改写解说时间线生成双语 `*_中文解说.srt` |
| 直读字幕音频 | 始终由中文 SRT/VTT 生成 `*_中文字幕直读_<provider>.mp3` |
| 直读加 BGM | 音乐 `0.45`、口播 `1.0` |
| 文件命名 | 保留源字幕主名，优先保留中文标题 |
| 文字注释 | 按视频时长生成 8–120 条 JSON 注释 |
| 自动混音 | 有源视频路径时生成 |

如果源视频本身有英文旁白，自动混音时只能将它作为低音量背景；如果英文人声仍然干扰中文解说，建议静音原声并使用轻量科技 BGM。

## 常用命令

根据时间线生成等长中文解说 MP3（Edge TTS）：

```powershell
python "L:/workspace/yinghe-shijie/skills/generate-narration-audio/scripts/render_timeline_tts.py" `
  --timeline "L:/workspace/yinghe-shijie/outputs/audio/星链如何把网络送到全球_时间线01_等长解说时间线.json"
```

根据时间线生成等长中文解说 MP3（CosyVoice）：

```powershell
& "L:/workspace/yinghe-shijie/tools/CosyVoice/.venv/Scripts/python.exe" `
  "L:/workspace/yinghe-shijie/skills/generate-narration-audio/scripts/render_cosyvoice_timeline.py" `
  --timeline "L:/workspace/yinghe-shijie/outputs/audio/星链如何把网络送到全球_时间线01_等长解说时间线.json" `
  --segment-manifest "L:/workspace/yinghe-shijie/outputs/audio/星链如何把网络送到全球_时间线01_等长解说分段时长.json"
```

导出中英双语中文解说字幕：

```powershell
python "L:/workspace/yinghe-shijie/skills/generate-narration-audio/scripts/timeline_to_srt.py" `
  --timeline "L:/workspace/yinghe-shijie/outputs/audio/星链如何把网络送到全球_时间线01_等长解说时间线.json" `
  --output "L:/workspace/yinghe-shijie/outputs/audio/星链如何把网络送到全球_时间线01_中文解说.srt"
```

建立并生成中文字幕直读音频：

```powershell
python "L:/workspace/yinghe-shijie/skills/generate-narration-audio/scripts/build_subtitle_tts_timeline.py" `
  --subtitle "L:/workspace/yinghe-shijie/星链如何把网络送到全球_时间线01.srt" `
  --video "L:/workspace/yinghe-shijie/videos/raw/星链如何把网络送到全球.mp4" `
  --output "L:/workspace/yinghe-shijie/outputs/audio/星链如何把网络送到全球_时间线01_中文字幕直读时间线.json" `
  --audio-output "星链如何把网络送到全球_时间线01_中文字幕直读_Yunyang.mp3"

python "L:/workspace/yinghe-shijie/skills/generate-narration-audio/scripts/render_timeline_tts.py" `
  --timeline "L:/workspace/yinghe-shijie/outputs/audio/星链如何把网络送到全球_时间线01_中文字幕直读时间线.json"

python "L:/workspace/yinghe-shijie/skills/generate-narration-audio/scripts/mix_narration_with_bgm.py" `
  --narration "L:/workspace/yinghe-shijie/outputs/audio/星链如何把网络送到全球_时间线01_中文字幕直读_Yunyang.mp3" `
  --output "L:/workspace/yinghe-shijie/outputs/audio/星链如何把网络送到全球_时间线01_中文字幕直读_背景音乐_正式版.mp3"
```

生成自动压低原声的混音：

```powershell
python "L:/workspace/yinghe-shijie/skills/generate-narration-audio/scripts/auto_mix_audio.py" `
  --video "L:/workspace/yinghe-shijie/videos/exports/星链如何把网络送到全球.mp4" `
  --narration "L:/workspace/yinghe-shijie/outputs/audio/星链如何把网络送到全球_时间线01_等长_Yunyang.mp3"
```

如果原视频声音太小，可增加 `--bg-volume`，例如：

```powershell
python "L:/workspace/yinghe-shijie/skills/generate-narration-audio/scripts/auto_mix_audio.py" `
  --video "L:/workspace/yinghe-shijie/videos/exports/星链如何把网络送到全球.mp4" `
  --narration "L:/workspace/yinghe-shijie/outputs/audio/星链如何把网络送到全球_时间线01_等长_Yunyang.mp3" `
  --bg-volume 0.45
```

## 最终回复格式

最终回复保持简短，但要提供：

- 等长解说时间线 JSON；
- 中文解说 SRT；
- 中文字幕直读时间线 JSON；
- 等长文本注释 JSON；
- 等长解说 MP3，并注明 provider 和声音；
- 中文字幕直读配音 MP3，并注明 provider 和声音；
- 中文字幕直读加 BGM MP3；
- 生成了自动混音时，提供自动混音 MP3；
- 已核验的时长、声音和语速。

同时说明：在剪映中可以选择原始双语字幕或中英双语的 `中文解说.srt`；音频可以选直读纯人声、直读加 BGM 或正式自动混音。使用任意一条生成音频时，都要把原视频轨静音。
