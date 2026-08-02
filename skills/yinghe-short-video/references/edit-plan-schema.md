# 剪辑计划结构

使用 UTF-8 JSON。时间值可以写成秒数，也可以写成 `HH:MM:SS.mmm`。

```json
{
  "version": 1,
  "title": "一枚导弹如何在高速飞行中锁定目标？",
  "editorial": {
    "content_lane": "军事武器/武器系统",
    "audience_question": "这枚导弹为什么能在高速飞行中持续锁定目标？",
    "promised_answer": "因为导引头、飞控和弹道修正会在飞行中不断更新目标位置。",
    "emotional_shift": "从以为导弹只是沿固定路线飞行，到看懂它其实在持续修正攻击路径。",
    "series_link": "导弹制导系列",
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
    "bilibili": "一枚导弹如何在高速飞行中锁定目标？",
    "douyin": "导弹高速飞行时，怎么还能锁定目标？",
    "kuaishou": "导弹飞这么快，咋还能一直追着目标？",
    "xiaohongshu": "导弹制导图解：看懂高速飞行中如何锁定目标"
  },
  "platform_descriptions": {
    "bilibili": "导弹高速飞行时如何持续锁定目标？用画面看懂导引头、飞控和弹道修正如何协同工作。",
    "douyin": "导弹飞得越快，越需要持续修正路线。它不是瞄准一次就结束，而是在飞行中不断更新目标位置。",
    "kuaishou": "导弹为啥能一直追着目标？关键不是飞得快，而是导引头和飞控一直在修正路线。",
    "xiaohongshu": "导弹制导图解：看懂导引头、飞控和弹道修正怎样协同，让导弹在高速飞行中持续追踪目标。"
  },
  "source_video": "G:/workspace/yinghe-shijie/videos/raw/example.mp4",
  "output_video": "G:/workspace/yinghe-shijie/videos/exports/example-short-01_短视频/example-short-01_短视频.mp4",
  "cover_title": "这台机器为什么这么快？",
  "cover_headline": "导弹如何持续锁定目标",
  "cover_subhead": "高速飞行中不断修正路线",
  "cover_style": "military",
  "cover_aspect": "16:9",
  "background_music": "",
  "layout": "source",
  "burn_captions": false,
  "write_subtitles": true,
  "mix": { "source_volume": 0.0, "narration_volume": 1.0, "music_volume": 0.0, "music_fade_seconds": 0.0 },
  "clips": [
    { "id": "hook", "source_start": "00:08:12.400", "source_end": "00:08:15.800", "focus_x": 0.56 },
    { "id": "scale", "source_start": "00:02:44.000", "source_end": "00:02:51.800", "focus_x": 0.50 },
    { "id": "mechanism", "source_start": "00:09:06.200", "source_end": "00:09:18.000", "focus_x": 0.42 }
  ],
  "narration": {
    "provider": "edge",
    "voice": "zh-CN-YunyangNeural",
    "rate": "+10%",
    "segments": [
      { "start": "00:00:00.000", "end": "00:00:03.400", "text": "这台机器一天，能挖走二十四万吨岩石。" },
      { "start": "00:00:03.400", "end": "00:00:11.000", "text": "它不是普通挖掘机，而是一座连续运转的露天矿工厂。" }
    ]
  }
}
```

`clips` 按数组顺序拼接。默认 `layout` 为 `source`：保留源视频分辨率和画幅比例（通常是 16:9），不裁切、不缩放、不生成背景。可以在单个片段中设置 `layout` 覆盖默认值。

电视剧的无语音剧情注释计划应把 `clips` 当作“高能故事链”的直接剪切清单：先选冲突爆发、升级、反击/证据和结果片段，再根据故事完整性加入起因、人物关系、动作因果和结果承接等过渡片段。过渡片段数量不设固定上限，但每个片段只能使用一次，任何两个片段的源时间都不能重叠；高能片段也没有重叠例外。高能片段可写 `high_energy: true` 和 `annotation_ids: ["anno_007"]`，用于要求对应的可编辑剧情注释覆盖其成片时间。

推荐在影视计划中加入：

```json
"edit_rules": {
  "selection_mode": "high_energy_story_chain",
  "clip_order": "story_order",
  "source_reuse": false,
  "source_overlap": false,
  "allow_transition_clips": true,
  "direct_cut": true,
  "burn_annotations": false
}
```

每个新的短视频计划都必须有 `platform_titles`，包含四个平台标题：`bilibili`、`douyin`、`kuaishou` 和 `xiaohongshu`。为兼容当前渲染脚本，`title` 必须等于 `platform_titles.bilibili`。渲染器不会读取 `platform_titles` 来剪视频；它保留这些字段，方便最终交付平台标题。

每个新的短视频计划都必须有 `platform_descriptions`，使用同样的四个平台键，保存可直接发布的中文简介。渲染器不会读取这个对象；它保留这些字段，方便最终交付平台简介。简介必须真实，并与完成后的口播和画面一致；需要时加入来源或授权署名。

硬核视界的新计划必须有 `editorial`，渲染器不会读取它。该对象记录内容赛道，以及开头 5–10 秒必须兑现的承诺：

- `content_lane`：男性向只能是 `军事武器/武器系统` 或 `作战机制`；女性向按具体的成长、情绪、关系或亲子主题填写。
- `audience_question`：普通观众能用日常语言提出的一个问题。
- `promised_answer`：开头必须交付或明确建立的一句话答案。
- `emotional_shift`：视频希望改变观众哪一个判断；不能只写敌意或未经支持的愤怒。
- `series_link`：所属系列或下一期的承接方向。
- `claim_status`：使用 `verified_fact`、`source_analysis` 或 `mixed`。使用 `mixed` 时，要在口播或简介中说明哪些部分属于分析。
- `cover_style`：只能是 `military` 或 `female`。军事武器、武器系统、作战机制和直接相关军工使用场景使用 `military`；女性成长、情绪、关系和亲子内容使用 `female`。它是内容包装字段，渲染器不读取，但每个新计划都必须明确填写。

涉及地图、战争史或国际局势时，如果源片只有评论，不能把 `claim_status` 写成 `verified_fact`。`editorial` 要简洁，只用于指导编辑，不要重复整篇口播。

只有用户明确要求输出 9:16 视频时，才使用 `contain_blur` 或 `fill_crop`。`fill_crop` 适合裁切后主体仍然清楚的近景；`focus_x` 控制保留的水平位置：`0` 为左侧，`0.5` 为中央，`1` 为右侧。选取的源片时间必须在源视频时长以内。

`narration.segments` 使用成片时间码，不是源视频时间码。普通短视频计划通过 `produce_short_video.py` 把它转换为时间线 JSON，并自动生成匹配的中文音频。电视剧也支持不配音的剧情注释模式：设置 `annotation_only: true`、`annotation_file`、`caption_mode: "plot_summary"`、`burn_captions: false` 和 `write_subtitles: false`，省略 `narration.segments` 和 `narration_audio`，使用 `mix.source_audio_mode: "keep_source"`，再调用电视剧技能的 `produce_annotation_video.py` 生成无文字清剪版。正式注释通过 `jianying_assistant` 写入剪映草稿，不得烧录进 MP4。

普通配音计划中的 `narration.provider` 可以是 `cosyvoice` 或 `edge`。硬核视界男性向短视频默认使用 Edge TTS `voice: "zh-CN-YunyangNeural"`、`rate: "+10%"`；只有用户明确指定其他声音时才改用其他配置。其他题材仍可按用户要求使用 CosyVoice：需要 `python: "tools/CosyVoice/.venv/Scripts/python.exe"`、`model_dir: "tools/CosyVoice/pretrained_models/CosyVoice-300M-SFT"`、`mode: "sft"` 和 `voice`，`speed` 为数值速度，默认 `1.0`。渲染器自动检测 CUDA，当前 RTX 4060 环境使用 CUDA + FP16；只有用户明确指定 Instruct 并试听通过时，才使用 `CosyVoice-300M-Instruct`、`mode: "instruct"` 和 `instruction`。Edge TTS 和 CosyVoice 都必须记录实际分段时长；CosyVoice 的 `zero_shot`、`instruct` 和参考音频字段见 `skills/generate-narration-audio/references/cosyvoice.md`。只有复用已经渲染好的配音轨时才需要 `narration_audio`。

`platform_titles`、`platform_descriptions`、`editorial` 和 `cover_*` 都是内容包装字段；渲染脚本主要使用 `source_video`、`output_video`、`clips`、`narration`、`mix`、`layout` 和音频/字幕相关字段。任何新增字段都要先确认下游脚本是否支持。

`preflight_review` 是渲染前的内容审查记录，不是可选备注。必须使用 `status: "passed"` 和 `review_scope: "content_before_render"`，并让所有 `checks` 都为 `"pass"`。运行 `scripts/validate_preflight_review.py --plan <plan.json>` 后，才能运行 `scripts/produce_short_video.py`；审查失败时先修改计划，再审查，不得先生成成片。

影视计划如果包含 `drama` 对象，还必须填写 `drama.opening_stance_hook`、`drama.commentary_viewpoint`、`drama.discussion_conflict` 和 `drama.emotional_value`。普通配音模式使用 `mix.source_audio_mode: "play_between_narration"`；`annotation_only: true` 模式使用 `mix.source_audio_mode: "keep_source"`，并由预检脚本拦截缺少剧情审核字段或误带中文配音分段的计划。

电视剧计划的 `drama.work_title` 和 `drama.episode` 还必须填写并经过素材核验；它们是正式封面的显示元数据，分别传给 `add_cover_title.py --series-title` 和 `--episode`，不得只留在文件名或发布文案中。

`write_subtitles` 默认是 `true`，普通模式会根据中文口播时间线写出旁车 SRT；中文解说版必须把解说 MP3 和解说 SRT 独立交付给剪映，`burn_captions` 通常保持为 `false`。如果需要保留原剧对白字幕，应使用已经映射到成片时间轴的 `original_dialogue_subtitle` 并单独启用原剧对白烧录，不得把解说 SRT 当作烧录字幕。电视剧 `annotation_only` 模式应设为 `false`，因为正式注释由 `jianying_assistant` 写入草稿。剧情注释模式不生成 TTS，也不显示 `subtext`。所有带中文解说的计划都必须以 TTS 实测时长验收最后一句，保留 `narration_tail_seconds`（默认约 0.6 秒）的收束画面；不满足时禁止交付。

`background_music` 指向可循环使用的 CC0 BGM。构建器会把音乐循环到成片时长，并直接与口播混音。默认不填写 `background_music`，也不合并 BGM；只有用户明确要求或平台版本确有需要时才填写音乐路径，并将 `music_volume` 单独记录。默认保持 `source_volume` 为 `0.0`、`music_volume` 为 `0.0`、`narration_volume` 为 `1.0`、`music_fade_seconds` 为 `0.0`；不要擅自添加原声、增益或淡出。

影视剧情解说可以在 `mix` 中使用动态原声策略：`source_audio_mode: "play_between_narration"`、`source_gap_volume: 1.0`、`source_audio_intro_deadline_seconds: 10.0`、`source_audio_intro_min_seconds: 0.5`。启用后，构建器依据 TTS 实测时间段在解说时将原视频音频压到 0，在解说间隙恢复原声，并检查前 10 秒是否至少留出指定时长的原声；其他内容默认仍使用 `source_audio_mode: "static"`。

`cover_title` 是自动生成的简短封面文字；没有时使用 `title`。`cover_aspect` 默认是 `16:9`。短视频计划默认必须包含封面字段，封面应是单独生成的对应比例视觉，不使用源视频截图。每条完整短视频都要自动准备 16:9、4:3（`1440x1080`）和 3:4（`1080x1440`）三张上传封面，但这些图片不是渲染脚本的输入；只有用户明确要求不生成封面时才跳过。`cover_headline` 和 `cover_subhead` 是后期叠加的准确中文文字。使用 `scripts/add_cover_title.py` 稳定渲染；电视剧还必须传入 `--series-title` 和 `--episode`，脚本会在顶部显示 `《剧名》  第X集` 并放大主冲突文字；除非用户明确要求主题标签，否则不设置 `--theme`。
