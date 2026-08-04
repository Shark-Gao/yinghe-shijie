# 双版本、注释和文件交付规范

## 双版本

默认同时交付：

- 原创中文解说版：`annotation_only: false`，包含混音 MP4、中文解说 MP3、中文解说 SRT 和剪辑计划。
- 屏幕注释纯原声版：`annotation_only: true`，只保留原剧原声和必要动作声，包含 MP4、`annotations.json`、外置注释 SRT 和剪辑计划；不生成中文配音，不烧录注释。

两个版本使用同一组已复核的源片段和同一套包装信息，分目录保存：

```text
videos/exports/短视频/<主题>/
videos/exports/短视频/<主题>_视频注释版/
```

## 注释规则

- 注释落在剪辑后成片时间轴，不直接使用源片时间码。
- 每个高能片段绑定对应 `annotation_ids`；每条注释落在对应成片片段内。
- `caption_mode: "plot_summary"`，`subtext` 为空，`style: "arrow_callout"`。
- 注释是单行自然中文剧情简介，外层使用中文双引号 `“……”`；若引用台词，内层使用中文单引号 `‘……’`。
- JSON、注释旁车 SRT 和剪映草稿中的文字与时间必须一致；注释不得烧录进 MP4。

生成后运行：

```powershell
python "L:/workspace/yinghe-shijie/skills/generate-narration-audio/scripts/validate_annotations_json.py" "<annotations.json>"
```

## 交付文件

交付前确认：两版 MP4、中文解说 MP3/SRT、注释 JSON/SRT、两份计划、三种封面、平台标题、完整简介和 3—4 个话题均已生成。用户明确跳过某版本或封面时，在计划和最终验收中记录原因。

