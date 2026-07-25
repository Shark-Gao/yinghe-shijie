# CosyVoice 本地配音

项目已经验证 `tools/CosyVoice` 的本地推理路线。后续需要低成本、稳定的中文影视解说配音时，优先使用 CosyVoice；未安装本地环境或需要快速批量试稿时，回退到 Edge TTS。

## 计划字段

在编辑计划的 `narration` 中填写：

```json
{
  "provider": "cosyvoice",
  "python": "tools/CosyVoice/.venv/Scripts/python.exe",
  "model_dir": "tools/CosyVoice/pretrained_models/CosyVoice-300M-SFT",
  "mode": "sft",
  "voice": "中文男",
  "speed": 1.0,
  "segments": []
}
```

路径相对于项目根目录时，渲染器会自动寻找；也可以填写绝对路径。`provider` 省略或写成 `edge` 时，继续使用 `zh-CN-*Neural` 声音和 `rate` 百分比语速。

## 统一运行环境

- Python：`tools/CosyVoice/.venv/Scripts/python.exe`
- 默认模型：`tools/CosyVoice/pretrained_models/CosyVoice-300M-SFT`
- 默认模式：`sft`
- GPU：渲染器自动检测 CUDA；当前环境使用 RTX 4060 + CUDA PyTorch + FP16。
- 回退：CUDA 不可用时仍可使用 CPU，但要在交付说明中注明；CosyVoice 不可用时才回退 Edge TTS。

不要在计划中把 `CosyVoice-300M-Instruct` 当作默认模型。它只在用户明确要求、短句试听通过后启用。

模型目录必须和模式匹配：`sft` 使用 `CosyVoice-300M-SFT`，`instruct` 使用 `CosyVoice-300M-Instruct`。电视剧解说需要情绪、悬疑或角色化表达时，计划可写成：

```json
{
  "provider": "cosyvoice",
  "python": "tools/CosyVoice/.venv/Scripts/python.exe",
  "model_dir": "tools/CosyVoice/pretrained_models/CosyVoice-300M-Instruct",
  "mode": "instruct",
  "voice": "中文女",
  "speed": 1.0,
  "instruction": "请用克制、带有悬疑感的电视剧解说方式朗读，强调人物选择和后果。"
}
```

## 模式选择

- `sft`：使用模型内置音色，当前推荐 `中文男`，适合影视解说和硬核纪录片口播。
- `zero_shot`：使用参考音频复刻音色，额外填写 `prompt_audio` 和 `prompt_text`。参考音频必须有合法使用权，且尽量只有一个人、少噪音、发音清楚。
- `instruct`：使用 `CosyVoice-300M-Instruct` 的自然语言指令控制风格，额外填写 `instruction`；可控制沉稳、悬疑、压迫、质问等表达，但不会凭空增加新的音色。当前试听效果不如 SFT 时，不要启用该模式。

当前已下载的 `CosyVoice-300M-SFT` 和 `CosyVoice-300M-Instruct` 内置音色均为：`中文女`、`中文男`、`日语男`、`粤语女`、`英文女`、`英文男`、`韩语女`。普通话影视解说默认使用 `CosyVoice-300M-SFT` 的 `中文男` 或 `中文女`；Instruct 只作为可选实验模式。想要真正不同的声线时，使用 `zero_shot` 和有授权的参考音频。

CosyVoice 的 `speed` 使用数值，`1.0` 为默认速度。若未填写，渲染器会把 `rate` 的百分比转换为近似速度，例如 `-8%` 转为 `0.92`。每个时间线段单独生成并测量真实时长，再写入分段时长清单；不要用计划窗口假定语音时长。

## 调用方式

短视频流程会根据 `narration.provider` 自动选择渲染器。手动渲染时使用：

```powershell
& "tools/CosyVoice/.venv/Scripts/python.exe" `
  "skills/generate-narration-audio/scripts/render_cosyvoice_timeline.py" `
  --timeline "outputs/shorts/example_中文解说时间线.json" `
  --segment-manifest "outputs/shorts/example_中文解说分段时长.json"
```

CosyVoice 当前在本机 CPU 上可以正常生成，但批量生成明显慢于 Edge TTS。安装并验证 CUDA 版 PyTorch 后，再把同一 `narration.python` 切换到对应虚拟环境；不要修改全局 Python 环境。

## 交付前检查

试听至少检查：普通话清晰度、声线是否符合题材、数字和专有名词是否读对、句间停顿、口播是否压住画面，以及实际时长是否超过计划窗口。CosyVoice 失败时不得静默生成空音频；可以回退到 Edge TTS，但要在最终报告说明实际使用的 provider 和声音。
