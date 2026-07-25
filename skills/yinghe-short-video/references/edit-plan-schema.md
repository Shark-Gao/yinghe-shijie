# 剪辑计划结构

使用 UTF-8 JSON。时间值可以写成秒数，也可以写成 `HH:MM:SS.mmm`。

```json
{
  "version": 1,
  "title": "一台机器一天挖走二十四万吨岩石",
  "editorial": {
    "content_lane": "大国工程/科技/产业竞争",
    "audience_question": "这台机器为什么能连续处理这么大的工程量？",
    "promised_answer": "因为挖掘、输送和堆料被连成了一条连续生产线。",
    "emotional_shift": "从以为是单台巨型设备，到看懂它其实是一套连续系统。",
    "series_link": "超级机械系列",
    "claim_status": "verified_fact"
  },
  "preflight_review": {
    "status": "passed",
    "review_scope": "content_before_render",
    "one_line_question": "普通观众真正想知道什么？",
    "one_line_answer": "这条视频最终给出的明确答案是什么？",
    "conflict": "这条内容的核心对立关系是什么？",
    "emotional_value": "观众看完后改变了哪个判断或获得了什么具体感受？",
    "checks": {
      "position_and_fact": "pass",
      "emotional_value": "pass",
      "conflict_and_hook": "pass",
      "answer_timing": "pass",
      "visual_evidence": "pass",
      "title_script_consistency": "pass",
      "safety_and_attribution": "pass"
    },
    "risk_notes": [],
    "revision_notes": []
  },
  "platform_titles": {
    "bilibili": "一台机器一天挖走二十四万吨岩石，它究竟怎么做到的？",
    "douyin": "一天挖走二十四万吨岩石，什么机器这么猛？",
    "kuaishou": "一天挖二十四万吨岩石，这台机器到底咋干的？",
    "xiaohongshu": "矿山巨型机械图解：看懂一天挖走二十四万吨岩石"
  },
  "platform_descriptions": {
    "bilibili": "一台斗轮挖掘机如何把挖掘、输送和堆料连成连续作业？用画面看懂它一天处理二十四万吨岩石的原理。",
    "douyin": "一天挖走二十四万吨岩石，靠的不是一台普通挖掘机，而是一条不停转的露天矿生产线。",
    "kuaishou": "这台大家伙为啥能一天挖二十四万吨岩石？关键在于挖、运、堆三件事从不停下来。",
    "xiaohongshu": "矿山巨型机械图解：看懂斗轮挖掘机怎样把挖掘、输送和堆料连成连续作业，一天处理二十四万吨岩石。"
  },
  "source_video": "G:/workspace/yinghe-shijie/videos/raw/example.mp4",
  "output_video": "G:/workspace/yinghe-shijie/videos/exports/example-short-01_短视频/example-short-01_短视频.mp4",
  "cover_title": "这台机器为什么这么快？",
  "cover_headline": "一台机器一天挖走二十四万吨",
  "cover_subhead": "它究竟怎么做到的？",
  "cover_aspect": "16:9",
  "background_music": "music/硬核视界_通用BGM_舒缓科普探索_CC0.mp3",
  "layout": "source",
  "burn_captions": false,
  "write_subtitles": true,
  "mix": { "source_volume": 0.0, "narration_volume": 1.0, "music_volume": 0.45, "music_fade_seconds": 0.0 },
  "clips": [
    { "id": "hook", "source_start": "00:08:12.400", "source_end": "00:08:15.800", "focus_x": 0.56 },
    { "id": "scale", "source_start": "00:02:44.000", "source_end": "00:02:51.800", "focus_x": 0.50 },
    { "id": "mechanism", "source_start": "00:09:06.200", "source_end": "00:09:18.000", "focus_x": 0.42 }
  ],
  "narration": {
    "provider": "cosyvoice",
    "python": "tools/CosyVoice/.venv/Scripts/python.exe",
    "model_dir": "tools/CosyVoice/pretrained_models/CosyVoice-300M-SFT",
    "mode": "sft",
    "voice": "中文男",
    "speed": 1.0,
    "rate": "+0%",
    "segments": [
      { "start": "00:00:00.000", "end": "00:00:03.400", "text": "这台机器一天，能挖走二十四万吨岩石。" },
      { "start": "00:00:03.400", "end": "00:00:11.000", "text": "它不是普通挖掘机，而是一座连续运转的露天矿工厂。" }
    ]
  }
}
```

`clips` 按数组顺序拼接。默认 `layout` 为 `source`：保留源视频分辨率和画幅比例（通常是 16:9），不裁切、不缩放、不生成背景。可以在单个片段中设置 `layout` 覆盖默认值。

每个新的短视频计划都必须有 `platform_titles`，包含四个平台标题：`bilibili`、`douyin`、`kuaishou` 和 `xiaohongshu`。为兼容当前渲染脚本，`title` 必须等于 `platform_titles.bilibili`。渲染器不会读取 `platform_titles` 来剪视频；它保留这些字段，方便最终交付平台标题。

每个新的短视频计划都必须有 `platform_descriptions`，使用同样的四个平台键，保存可直接发布的中文简介。渲染器不会读取这个对象；它保留这些字段，方便最终交付平台简介。简介必须真实，并与完成后的口播和画面一致；需要时加入来源或授权署名。

硬核视界的新计划必须有 `editorial`，渲染器不会读取它。该对象记录内容赛道，以及开头 5–10 秒必须兑现的承诺：

- `content_lane`：只能是 `地缘政治/国际局势`、`军事装备/战争机制` 或 `大国工程/科技/产业竞争`。
- `audience_question`：普通观众能用日常语言提出的一个问题。
- `promised_answer`：开头必须交付或明确建立的一句话答案。
- `emotional_shift`：视频希望改变观众哪一个判断；不能只写敌意或未经支持的愤怒。
- `series_link`：所属系列或下一期的承接方向。
- `claim_status`：使用 `verified_fact`、`source_analysis` 或 `mixed`。使用 `mixed` 时，要在口播或简介中说明哪些部分属于分析。

当前地缘政治内容，如果源片只有评论，不能把 `claim_status` 写成 `verified_fact`。`editorial` 要简洁，只用于指导编辑，不要重复整篇口播。

只有用户明确要求输出 9:16 视频时，才使用 `contain_blur` 或 `fill_crop`。`fill_crop` 适合裁切后主体仍然清楚的近景；`focus_x` 控制保留的水平位置：`0` 为左侧，`0.5` 为中央，`1` 为右侧。选取的源片时间必须在源视频时长以内。

`narration.segments` 使用成片时间码，不是源视频时间码。`produce_short_video.py` 会把它转换为时间线 JSON，并自动生成匹配的中文音频。`narration.provider` 可以是 `cosyvoice` 或 `edge`；CosyVoice 默认需要 `python: "tools/CosyVoice/.venv/Scripts/python.exe"`、`model_dir: "tools/CosyVoice/pretrained_models/CosyVoice-300M-SFT"`、`mode: "sft"` 和 `voice`，`speed` 为数值速度，默认 `1.0`。渲染器自动检测 CUDA，当前 RTX 4060 环境使用 CUDA + FP16；只有用户明确指定 Instruct 并试听通过时，才使用 `CosyVoice-300M-Instruct`、`mode: "instruct"` 和 `instruction`。CosyVoice 不可用或用户明确指定时才使用 Edge TTS。省略 provider 时保持 Edge TTS 兼容。CosyVoice 的 `zero_shot`、`instruct` 和参考音频字段见 `skills/generate-narration-audio/references/cosyvoice.md`。只有复用已经渲染好的配音轨时才需要 `narration_audio`。

`platform_titles`、`platform_descriptions`、`editorial` 和 `cover_*` 都是内容包装字段；渲染脚本主要使用 `source_video`、`output_video`、`clips`、`narration`、`mix`、`layout` 和音频/字幕相关字段。任何新增字段都要先确认下游脚本是否支持。

`preflight_review` 是渲染前的内容审查记录，不是可选备注。必须使用 `status: "passed"` 和 `review_scope: "content_before_render"`，并让所有 `checks` 都为 `"pass"`。运行 `scripts/validate_preflight_review.py --plan <plan.json>` 后，才能运行 `scripts/produce_short_video.py`；审查失败时先修改计划，再审查，不得先生成成片。

影视解说计划如果包含 `drama` 对象，还必须填写 `drama.opening_stance_hook`、`drama.commentary_viewpoint`、`drama.discussion_conflict` 和 `drama.emotional_value`，并在 `mix.source_audio_mode` 中使用 `"play_between_narration"`。预检脚本会在生成配音前拦截缺少这些内容的计划。

`write_subtitles` 默认是 `true`，会根据中文口播时间线写出相邻的 SRT 文件。渲染配音时，脚本会测量每段 TTS 的真实时长，并用它限制对应字幕段，防止字幕在语音结束后继续显示。SRT 显示文本会去掉句末标点，口播文本仍保留标点以形成自然 TTS 停顿。`burn_captions` 默认是 `false`，只有用户明确要求时才设为 `true`。

`background_music` 指向可循环使用的 CC0 BGM。构建器会把音乐循环到成片时长，并直接与口播混音。除非用户明确要求，保持 `source_volume` 为 `0.0`。默认 `music_volume` 为 `0.45`，`narration_volume` 为 `1.0`，`music_fade_seconds` 为 `0.0`；不要擅自修改口播音量、增加增益或添加淡出。

影视剧情解说可以在 `mix` 中使用动态原声策略：`source_audio_mode: "play_between_narration"`、`source_gap_volume: 1.0`、`source_audio_intro_deadline_seconds: 10.0`、`source_audio_intro_min_seconds: 0.5`。启用后，构建器依据 TTS 实测时间段在解说时将原视频音频压到 0，在解说间隙恢复原声，并检查前 10 秒是否至少留出指定时长的原声；其他内容默认仍使用 `source_audio_mode: "static"`。

`cover_title` 是自动生成的简短封面文字；没有时使用 `title`。`cover_aspect` 默认是 `16:9`。短视频计划默认必须包含封面字段，封面应是单独生成的横版视觉，不使用源视频截图。每条完整短视频都要自动准备 16:9、4:3（`1440x1080`）和 9:16（`1080x1920`）三张上传封面，但这些图片不是渲染脚本的输入；只有用户明确要求不生成封面时才跳过。`cover_headline` 和 `cover_subhead` 是后期叠加的准确中文文字。使用 `scripts/add_cover_title.py` 稳定渲染；除非用户明确要求主题标签，否则不设置 `--theme`。
