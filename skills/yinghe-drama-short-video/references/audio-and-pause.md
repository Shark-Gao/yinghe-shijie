# 配音、停讲与原声混音规范

## 默认配置

解说版默认使用：

```json
{
  "provider": "cosyvoice",
  "mode": "sft",
  "voice": "中文女",
  "speed": 1.12,
  "mix": {
    "source_audio_mode": "play_between_narration",
    "source_gap_volume": 0.65,
    "source_audio_under_narration_volume": 0.12,
    "narration_volume": 1.0,
    "music_volume": 0.0
  }
}
```

不加 BGM。中文解说 MP3/SRT 是正式旁车文件，不得当作中间文件清理。

## 解说段落和停讲

- 每段通常 3—8 秒、1—2 句，紧贴当前画面。
- 相邻段间按实际 TTS 时长计算间隔，普通停讲至少 1.5 秒，章节转折或关键对白前后优先 2—3 秒。
- 0.3 秒左右的技术空隙不算停讲；必须在时间线中显式安排原声呼吸段或静音段。
- 计划区分两种模式：
  - 停中文解说、保留计划内的原剧必要对白/动作声；
  - 完全静音。用户要求完全静音时，不能让 `source_gap_volume` 覆盖停讲。
- 原声在解说期间短暂压低，关键对白不得被中文配音遮挡；原声引用应等待完整句或自然语义段结束。

## 生成和检查

1. 在 `narration.segments` 写入成片时间，不直接套源片时间码。
2. 运行：

   ```powershell
   python "L:/workspace/yinghe-shijie/skills/yinghe-short-video/scripts/produce_short_video.py" --plan "<plan.json>"
   ```

3. 读取生成的 `中文解说分段时长.json`，计算：最短停讲、关键转折停讲、最后一段实际结束时间。
4. 最短停讲低于 1.5 秒时返修；最后一段实际结束时间必须早于视频结束，并保留至少约 0.6 秒收束画面。
5. 试听或用静音检测确认停讲期间确实没有中文解说；如果仍听到声音，判断它是计划内原声还是误混入的连续配音。

