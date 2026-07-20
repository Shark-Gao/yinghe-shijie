# Edit plan schema

Use UTF-8 JSON. Time values can be seconds or `HH:MM:SS.mmm`.

```json
{
  "version": 1,
  "title": "一台机器一天挖走二十四万吨岩石",
  "platform_titles": {
    "bilibili": "一台机器一天挖走二十四万吨岩石，它究竟怎么做到的？",
    "douyin": "一天挖走二十四万吨岩石，什么机器这么猛？",
    "kuaishou": "一天挖二十四万吨岩石，这台机器到底咋干的？",
    "xiaohongshu": "矿山巨型机械图解：看懂一天挖走二十四万吨岩石"
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
    "voice": "zh-CN-YunyangNeural",
    "rate": "+0%",
    "segments": [
      { "start": "00:00:00.000", "end": "00:00:03.400", "text": "这台机器一天，能挖走二十四万吨岩石。" },
      { "start": "00:00:03.400", "end": "00:00:11.000", "text": "它不是普通挖掘机，而是一座连续运转的露天矿工厂。" }
    ]
  }
}
```

`clips` are concatenated in array order. The default `layout` is `source`: retain the source resolution and frame ratio (normally 16:9) without crop, scaling, or a generated background. Set a clip's `layout` to override it.

`platform_titles` is required for every new short-video plan. It contains four delivery titles: `bilibili`, `douyin`, `kuaishou`, and `xiaohongshu`. Keep `title` equal to `platform_titles.bilibili` for compatibility with the current render scripts. The renderer ignores `platform_titles`; it is preserved in the plan so every final delivery can list platform-ready titles.

Use `contain_blur` or `fill_crop` only when a 9:16 output has been explicitly requested. `fill_crop` is for a close-up that remains readable after cropping; its `focus_x` controls the retained horizontal position: `0` left, `0.5` center, `1` right. Keep the selected source ranges inside the source duration.

`narration.segments` use output-video timecodes, not source-video timecodes. `produce_short_video.py` converts them to a timeline JSON and renders the matching Chinese audio automatically. `narration_audio` is optional and is only needed when reusing a pre-rendered voice track.

`write_subtitles` defaults to true and writes an adjacent SRT from the Chinese narration timeline for manual import into Jianying/CapCut. When `scripts/produce_short_video.py` renders narration, it also measures each TTS segment and uses those measured durations to cap the matching SRT cues; this prevents subtitles from continuing after the spoken line ends. Displayed SRT cues strip trailing sentence punctuation, while narration text retains punctuation for natural TTS pauses. `burn_captions` defaults to false. Only set it to true when the user explicitly requests burned-in captions.

`background_music` points to the reusable CC0 background track. The builder loops it to the output duration and mixes it directly with narration. Keep `source_volume` at `0.0` unless the user explicitly wants original source sound. By default, `music_volume` is `0.45`, `narration_volume` is `1.0`, and `music_fade_seconds` is `0.0`: do not alter narration or add fades unless the user asks.

`cover_title` is optional and should be concise Chinese cover text; otherwise `title` is used. `cover_aspect` defaults to `16:9`; generate a landscape AI cover with this ratio, never a source-video screenshot. `cover_headline` and `cover_subhead` are the high-impact exact Chinese overlays. Use `scripts/add_cover_title.py` to render them deterministically. `--theme` is optional and should remain omitted unless the user explicitly asks for a subject label.
